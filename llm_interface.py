# llm_interface.py

import subprocess
from memory import Memory
from datetime import datetime
from typing import Optional
import threading
import time

class LLMInterface:
    def __init__(self, model="mistral", memory: Memory = None):
        self.model = model
        self.memory = memory  # Optional memory object
        self.current_process = None
        self.interrupt_requested = False

    def get_response(self, user_input: str, use_memory_context: bool = True) -> str:
        """Get response from LLM with optional memory context"""
        return self._get_response_with_context(user_input, use_memory_context)
    
    def get_response_with_memory_search(self, user_input: str) -> str:
        """Get response using contextual memory search based on user input"""
        if not self.memory:
            return self._get_response_with_context(user_input, False)
        
        # Get contextual memory that's relevant to the user's query
        context = self.memory.get_contextual_memory(user_input, limit=3)
        
        now = datetime.now().strftime("%A, %B %d, %Y at %H:%M")
        system_prompt = f"""You are a helpful AI assistant. The current date and time is {now}.

You have access to our previous conversations which may be relevant to the current question.
Use this context to provide more personalized and informed responses.

If the user is asking about something we discussed before, reference that conversation appropriately.
If the context doesn't seem relevant to the current question, you can ignore it.

{context}Current conversation:
User: {user_input}
Assistant:"""

        return self._call_llm(system_prompt)
    
    def _get_response_with_context(self, user_input: str, use_memory: bool = True) -> str:
        """Internal method to get response with standard context"""
        # Build context
        context = ""
        if use_memory and self.memory:
            context = self.memory.recall_recent(limit=5)
        
        now = datetime.now().strftime("%A, %B %d, %Y at %H:%M")
        system_info = f"You are a helpful AI assistant. The current date and time is {now}."
        
        if context:
            prompt = f"{system_info}\n\n{context}Current conversation:\nUser: {user_input}\nAssistant:"
        else:
            prompt = f"{system_info}\n\nUser: {user_input}\nAssistant:"

        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """Make the actual call to the LLM"""
        return self._call_llm_interruptible(prompt)
    
    def _call_llm_interruptible(self, prompt: str, voice_recognizer=None) -> str:
        """Make an interruptible call to the LLM"""
        self.interrupt_requested = False
        
        try:
            # Start the LLM process
            self.current_process = subprocess.Popen(
                ["ollama", "run", self.model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send the prompt
            stdout, stderr = self.current_process.communicate(input=prompt, timeout=30)
            
            if self.current_process.returncode == 0:
                return stdout.strip()
            else:
                print(f"[ERROR] LLM call failed: {stderr.strip()}")
                return "I'm sorry, I'm having trouble processing your request right now."
                
        except subprocess.TimeoutExpired:
            if self.current_process:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            return "I'm sorry, that request is taking too long to process."
        except Exception as e:
            print(f"[ERROR] Unexpected error calling LLM: {e}")
            if self.current_process:
                self.current_process.terminate()
            return "I'm sorry, I encountered an unexpected error."
        finally:
            self.current_process = None
    
    def interrupt_llm(self):
        """Interrupt the current LLM call"""
        self.interrupt_requested = True
        if self.current_process:
            print("[INFO] Interrupting LLM generation...")
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
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
            context = self.memory.get_contextual_memory(user_input, limit=3)
            
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
