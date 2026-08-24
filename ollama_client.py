# ollama_client.py
"""Thin HTTP client for Ollama's /api/chat endpoint.

Replaces the old pattern of shelling out to `ollama run <model>` via
subprocess for every call. Talking to the REST API directly gives us
streaming tokens, a real message-array conversation instead of one giant
concatenated prompt string, and keep_alive so the model doesn't get
reloaded from disk between turns.
"""

import json
import requests


class OllamaError(Exception):
    """Raised when Ollama itself reports an error for a request."""
    pass


def stream_chat(messages, model, host, timeout=60, options=None, keep_alive=None,
                 cancel_event=None, response_holder=None):
    """Call /api/chat with streaming and return the full assistant reply text.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    cancel_event: optional threading.Event; if set while streaming, the
        connection is torn down and whatever text arrived so far is returned.
    response_holder: optional dict; if given, response_holder["response"] is
        set to the live requests.Response so another thread can call
        .close() on it to trigger cancellation (used for TTS/LLM interrupts).
    """
    payload = {"model": model, "messages": messages, "stream": True}
    if options:
        payload["options"] = options
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive

    response = requests.post(f"{host}/api/chat", json=payload, stream=True, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        response.close()
        raise OllamaError(f"Ollama returned {response.status_code}: {e}") from e

    if response_holder is not None:
        response_holder["response"] = response

    chunks = []
    try:
        for line in response.iter_lines():
            if cancel_event is not None and cancel_event.is_set():
                break
            if not line:
                continue
            data = json.loads(line)
            if data.get("error"):
                raise OllamaError(data["error"])
            content = data.get("message", {}).get("content", "")
            if content:
                chunks.append(content)
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

    return "".join(chunks).strip()
