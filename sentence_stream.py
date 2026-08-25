# sentence_stream.py
"""Incremental sentence splitting for streamed LLM output.

Lets the assistant start speaking a response before the model has finished
generating all of it: feed() is called with each text delta as it arrives,
and returns any sentences that are now complete. The last, possibly
unfinished sentence stays buffered until more text (or flush()) completes
it.
"""

import re

try:
    from nltk.tokenize import sent_tokenize
    sent_tokenize("Warm-up call to check punkt data is actually available.")
    _NLTK_AVAILABLE = True
except Exception:
    _NLTK_AVAILABLE = False

# Fallback used when NLTK's punkt data isn't available: splits after
# sentence-ending punctuation followed by whitespace. Cruder than a real
# tokenizer (e.g. "Dr. Smith" will false-split), but dependency-free.
_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+')


def _split_sentences(text: str) -> list:
    if _NLTK_AVAILABLE:
        try:
            return sent_tokenize(text)
        except Exception:
            pass
    return [s for s in _SENTENCE_BOUNDARY.split(text) if s]


class SentenceSplitter:
    """Buffers streamed text chunks and yields complete sentences as soon
    as they're available."""

    def __init__(self):
        self._buffer = ""

    def feed(self, chunk: str) -> list:
        """Add a text delta. Returns a list of newly-complete sentences
        (possibly empty)."""
        if not chunk:
            return []
        self._buffer += chunk

        parts = _split_sentences(self._buffer)
        if len(parts) <= 1:
            return []

        # The last part might still be incomplete (more text could arrive
        # that continues it) - only the earlier ones are safe to emit. The
        # tokenizer's own text for the remainder becomes the new buffer;
        # minor whitespace normalization here doesn't matter since sentences
        # are stripped before being spoken anyway.
        complete, self._buffer = parts[:-1], parts[-1]

        return [s.strip() for s in complete if s.strip()]

    def flush(self):
        """Call once the stream has ended to get any trailing text that
        never reached a sentence boundary. Returns None if nothing's left."""
        remainder = self._buffer.strip()
        self._buffer = ""
        return remainder or None
