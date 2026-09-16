# ollama_client.py
"""Thin HTTP client for Ollama's /api/chat endpoint.

Replaces the old pattern of shelling out to `ollama run <model>` via
subprocess for every call. Talking to the REST API directly gives us
streaming tokens, a real message-array conversation instead of one giant
concatenated prompt string, keep_alive so the model doesn't get reloaded
from disk between turns, and (via stream_chat_with_tools) native function
calling so the LLM can decide which local tool to invoke instead of a
hand-written intent classifier routing to it.
"""

import json
import requests


class OllamaError(Exception):
    """Raised when Ollama itself reports an error for a request."""
    pass


def _stream_request(messages, model, host, timeout, options, keep_alive, tools,
                     cancel_event, response_holder, on_content=None):
    """Shared streaming implementation. Returns (text, tool_calls).

    on_content: optional callback invoked with each non-empty content delta
    as it streams in (before the full text is known). Used to start
    speaking a response sentence-by-sentence instead of waiting for the
    whole thing - see LLMInterface.run_agent_turn's on_sentence param.
    """
    payload = {"model": model, "messages": messages, "stream": True}
    if options:
        payload["options"] = options
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    if tools:
        payload["tools"] = tools

    response = requests.post(f"{host}/api/chat", json=payload, stream=True, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        response.close()
        raise OllamaError(f"Ollama returned {response.status_code}: {e}") from e

    if response_holder is not None:
        response_holder["response"] = response

    chunks = []
    tool_calls = None
    try:
        for line in response.iter_lines():
            if cancel_event is not None and cancel_event.is_set():
                break
            if not line:
                continue
            data = json.loads(line)
            if data.get("error"):
                raise OllamaError(data["error"])
            message = data.get("message") or {}
            content = message.get("content", "")
            if content:
                chunks.append(content)
                if on_content is not None:
                    on_content(content)
            if message.get("tool_calls"):
                tool_calls = message["tool_calls"]
            if data.get("done"):
                break
    except Exception:
        # A cancel_event-triggered close() from another thread surfaces here
        # as a connection error - that's expected, not a real failure.
        if not (cancel_event is not None and cancel_event.is_set()):
            raise
    finally:
        response.close()
        if response_holder is not None:
            response_holder["response"] = None

    return "".join(chunks).strip(), tool_calls


def stream_chat(messages, model, host, timeout=60, options=None, keep_alive=None,
                 cancel_event=None, response_holder=None, on_content=None):
    """Call /api/chat with streaming and return the full assistant reply text.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    cancel_event: optional threading.Event; if set while streaming, the
        connection is torn down and whatever text arrived so far is returned.
    response_holder: optional dict; if given, response_holder["response"] is
        set to the live requests.Response so another thread can call
        .close() on it to trigger cancellation (used for TTS/LLM interrupts).
    on_content: optional callback fired with each text delta as it streams.
    """
    text, _ = _stream_request(messages, model, host, timeout, options, keep_alive,
                               None, cancel_event, response_holder, on_content)
    return text


def stream_chat_with_tools(messages, model, host, tools, timeout=60, options=None,
                            keep_alive=None, cancel_event=None, response_holder=None,
                            on_content=None):
    """Like stream_chat, but passes a tool/function schema list and also
    returns any tool_calls the model made (list of
    {"function": {"name": str, "arguments": dict}}, empty if none).

    Returns (text, tool_calls).
    """
    text, tool_calls = _stream_request(messages, model, host, timeout, options, keep_alive,
                                        tools, cancel_event, response_holder, on_content)
    return text, (tool_calls or [])


def embed(texts, model, host, timeout=30, keep_alive=None):
    """Call /api/embed and return one L2-normalized vector per input string.

    texts: a single string or a list of strings (batched in one request -
        Ollama's recommended way to embed many texts at once).
    Returns a list of embedding vectors (list[list[float]]), one per input,
    in the same order. Raises OllamaError / requests exceptions on failure -
    callers that want graceful degradation (e.g. falling back to keyword
    search when the embed model isn't pulled) need to catch those.
    """
    single = isinstance(texts, str)
    payload = {"model": model, "input": [texts] if single else list(texts)}
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive

    response = requests.post(f"{host}/api/embed", json=payload, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise OllamaError(f"Ollama returned {response.status_code} for /api/embed: {e}") from e

    data = response.json()
    if data.get("error"):
        raise OllamaError(data["error"])

    embeddings = data.get("embeddings")
    if not embeddings:
        raise OllamaError("Ollama /api/embed returned no embeddings")

    return embeddings
