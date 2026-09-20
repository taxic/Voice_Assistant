# interruptible_tts.py

from config_manager import config


def _build_engine(voice_recognizer):
    """Pick the TTS engine from config (tts.engine, default "kokoro"),
    falling back to Piper if Kokoro can't actually be used - missing
    package, failed model download, etc. Piper is the proven-working
    engine, so this keeps the assistant from going silent just because the
    newer/less-tested engine hit a snag."""
    engine_name = config.get('tts.engine', 'kokoro')

    if engine_name == 'kokoro':
        from kokoro_tts import KokoroTTS
        engine = KokoroTTS(voice_recognizer=voice_recognizer)
        if engine.kokoro is not None:
            return engine
        print("[WARN] Kokoro TTS unavailable, falling back to Piper.")

    from piper_tts import PiperTTS
    return PiperTTS(voice_recognizer=voice_recognizer)


class InterruptibleTTS:
    def __init__(self, voice_recognizer=None):
        self.engine = _build_engine(voice_recognizer)
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False

    def speak(self, text, check_interrupts=True):
        """Speak text with optional interrupt checking"""
        # Delegate to the Piper TTS engine which handles all the functionality
        self.engine.speak(text, check_interrupts=check_interrupts)

        # Update our state to match the engine's state
        self.is_speaking = self.engine.is_speaking
        self.interrupt_requested = self.engine.interrupt_requested

    def interrupt(self):
        """Request speech interruption"""
        self.engine.interrupt()
        self.interrupt_requested = self.engine.interrupt_requested
        self.is_speaking = self.engine.is_speaking

