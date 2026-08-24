# llm_interface.py

import threading
import requests
from enhanced_memory import EnhancedMemory
from datetime import datetime
from typing import Optional
from config_manager import config
from ollama_client import stream_chat, OllamaError

DEFAULT_SYSTEM_PROMPT = (
    "You are a capable, personable AI assistant running locally on the user's own "
    "hardware. Speak naturally and concisely, like a sharp, easygoing human "
    "assistant, not a corporate chatbot - warmth and personality are welcome, "
    "but don't pad answers with filler. Get straight to useful, correct "
    "information. If you're not sure about something, say so instead of "
    "guessing."
)


class LLMInterface:
    def __init__(self, model=None, memory: EnhancedMemory = None):
        # Use config for model if not specified
        self.model = model or config.get('llm.model', 'qwen2.5:7b-instruct')
        self.memory = memory  # Optional memory object
        self.host = config.get('llm.host', 'http://localhost:11434').rstrip('/')
        self.timeout = config.get('llm.timeout_seconds', 60)
        self.keep_alive = config.get('llm.keep_alive', '10m')
        self.num_ctx = config.get('llm.num_ctx', 4096)
        self.max_history_messages = config.get('llm.max_history_messages', 20)
        self.system_prompt = config.get('llm.system_prompt', DEFAULT_SYSTEM_PROMPT)

        # Running message-array conversation for this process's lifetime.
        # Long-term continuity across restarts still comes from `memory`.
        self.conversation_history = []

        self.interrupt_requested = False
        self._generating = False
        self._cancel_event = threading.Event()
        self._response_holder = {"response": None}
        self._stream_lock = threading.Lock()

    @property
    def current_process(self):
        """Backward-compatible truthy flag: is a generation in flight?

        main.py's interrupt-monitor loop polls this attribute (not a method)
        to know when the LLM has finished, so it stays a property rather than
        exposing the underlying requests.Response directly.
        """
        return True if self._generating else None

    def reset_conversation(self):
        """Clear the in-memory chat history (e.g. when starting a fresh topic)."""
        self.conversation_history = []

    def get_response(self, user_input: str, use_memory_context: bool = True) -> str:
        """Get response from LLM with optional memory context"""
        return self._get_response_with_context(user_input, use_memory_context)

    def get_response_with_memory_search(self, user_input: str) -> str:
        """Get response using contextual memory search based on user input"""
        if not self.memory:
            return self._get_response_with_context(user_input, False)

        limit = config.get('memory.contextual_search_limit', 3)
        context = self.memory.get_contextual_memory(user_input, limit=limit)

        messages = self._build_messages(extra_context=context)
        messages.append({"role": "user", "content": user_input})

        response = self._call_chat(messages)
        self._remember_turn(user_input, response)
        return response

    def _get_response_with_context(self, user_input: str, use_memory: bool = True) -> str:
        """Internal method to get response with standard context"""
        extra_context = None
        # Only pull persisted recent history the first time this process
        # talks (i.e. to restore continuity across restarts) - once
        # conversation_history has turns in it, it's already the source of
        # truth for recent context and re-injecting the DB copy would just
        # duplicate it in the prompt.
        if use_memory and self.memory and not self.conversation_history:
            limit = config.get('memory.max_recent_interactions', 5)
            extra_context = self.memory.recall_recent(limit=limit)

        messages = self._build_messages(extra_context=extra_context)
        messages.append({"role": "user", "content": user_input})

        response = self._call_chat(messages)
        self._remember_turn(user_input, response)
        return response

    def _build_messages(self, extra_context: Optional[str] = None) -> list:
        """Build the message array: system prompt + optional memory context + running history."""
        now = datetime.now().strftime("%A, %B %d, %Y at %H:%M")
        messages = [{"role": "system", "content": f"{self.system_prompt}\n\nCurrent date and time: {now}."}]

        if extra_context:
            messages.append({
                "role": "system",
                "content": f"Relevant context from earlier conversations:\n{extra_context}",
            })

        messages.extend(self.conversation_history[-self.max_history_messages:])
        return messages

    def _remember_turn(self, user_input: str, response: str):
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        if len(self.conversation_history) > self.max_history_messages:
            self.conversation_history = self.conversation_history[-self.max_history_messages:]

    def _call_llm(self, prompt: str) -> str:
        """Make a stateless, single-turn call (used for internal extraction
        prompts like 'pull the date out of this sentence'). Not added to the
        running conversation - it isn't a real dialogue turn."""
        return self._call_chat([{"role": "user", "content": prompt}])

    def _call_chat(self, messages: list) -> str:
        """Send a message array to Ollama and return the full reply text."""
        self.interrupt_requested = False
        self._cancel_event.clear()
        self._generating = True

        options = {"num_ctx": self.num_ctx}

        try:
            return stream_chat(
                messages,
                model=self.model,
                host=self.host,
                timeout=self.timeout,
                options=options,
                keep_alive=self.keep_alive,
                cancel_event=self._cancel_event,
                response_holder=self._response_holder,
            )
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Could not reach Ollama at {self.host}")
            return "I'm sorry, I can't reach the local LLM right now. Is Ollama running?"
        except requests.exceptions.Timeout:
            print("[ERROR] LLM call timed out")
            return "I'm sorry, that request is taking too long to process."
        except OllamaError as e:
            print(f"[ERROR] LLM call failed: {e}")
            return "I'm sorry, I'm having trouble processing your request right now."
        except Exception as e:
            print(f"[ERROR] Unexpected error calling LLM: {e}")
            return "I'm sorry, I encountered an unexpected error."
        finally:
            self._generating = False

    def interrupt_llm(self):
        """Interrupt the current LLM call"""
        if self._generating:
            print("[INFO] Interrupting LLM generation...")
            self.interrupt_requested = True
            self._cancel_event.set()
            with self._stream_lock:
                response = self._response_holder.get("response")
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass
            return True
        return False

    def analyze_intent_with_memory(self, user_input: str) -> dict:
        """Analyze user intent considering memory context"""
        if not self.memory:
            return {"intent": "unknown", "confidence": 0.0, "memory_relevant": False}

        # Check if this seems to be referencing previous conversations
        memory_indicators = [
            "remember", "said before", "told you", "previous", "earlier",
            "last time", "conversation", "talked about", "discussed",
            "mentioned", "we were talking", "you said", "I asked"
        ]

        text_lower = user_input.lower()
        memory_relevant = any(indicator in text_lower for indicator in memory_indicators)

        if memory_relevant:
            # Get relevant context
            limit = config.get('memory.contextual_search_limit', 3)
            context = self.memory.get_contextual_memory(user_input, limit=limit)

            prompt = f"""Analyze this user input to determine if it's asking about a previous conversation:

User input: "{user_input}"

Relevant conversation history:
{context}

Respond with just "YES" if the user is asking about something from the conversation history, or "NO" if it's a new topic.

Answer:"""

            result = self._call_llm(prompt)
            memory_relevant = result.strip().upper() == "YES"

        return {
            "intent": "memory_recall" if memory_relevant else "general_question",
            "confidence": 0.8 if memory_relevant else 0.5,
            "memory_relevant": memory_relevant
        }
