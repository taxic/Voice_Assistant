# kokoro_tts.py
"""Kokoro-82M TTS engine - an alternative to Piper with noticeably more
natural output (StyleTTS2-based, ~4.2 MOS in third-party benchmarks) for a
similar hardware footprint. Selected via config: tts.engine = "kokoro"
(default) or "piper" - see interruptible_tts.py.

Same public interface as PiperTTS (speak/interrupt/is_speaking/
interrupt_requested) so interruptible_tts.py can use either one
interchangeably. Degrades the same way Piper does if the optional
`kokoro-onnx` package isn't installed or the model files aren't available:
logs the text and does nothing, rather than crashing the assistant.
"""
import os
from pathlib import Path

import requests
from config_manager import config
from sentence_stream import split_sentences

import sounddevice as sd

try:
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False
    print("[INFO] kokoro-onnx not installed. Install with: pip install kokoro-onnx")

MODEL_RELEASE_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1"


class KokoroTTS:
    def __init__(self, voice_recognizer=None):
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False

        self.models_dir = Path.cwd() / "kokoro" / "models"
        self.model_variant = config.get('tts.kokoro.model_variant', 'int8')
        self.voice = config.get('tts.kokoro.voice', 'bf_emma')
        self.speed = config.get('tts.kokoro.speed', 1.0)
        self.lang = config.get('tts.kokoro.lang', 'en-gb')

        self.kokoro = None

        if not KOKORO_AVAILABLE:
            return

        try:
            self._setup_kokoro()
            print(f"[INFO] Kokoro TTS initialized with voice: {self.voice}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Kokoro TTS: {e}")
            print("[WARN] Falling back to basic text output")

    def _setup_kokoro(self):
        """Download the ONNX model + voice pack if not already present, then
        load them. Loading builds an onnxruntime session, so this happens
        once at startup, same as Piper's one-time setup."""
        self.models_dir.mkdir(parents=True, exist_ok=True)

        model_filename = "kokoro-v1.0.onnx" if self.model_variant == "f32" else f"kokoro-v1.0.{self.model_variant}.onnx"
        model_path = self.models_dir / model_filename
        voices_path = self.models_dir / "voices-v1.0.bin"

        self._ensure_file(model_path, f"{MODEL_RELEASE_BASE}/{model_filename}")
        self._ensure_file(voices_path, f"{MODEL_RELEASE_BASE}/voices-v1.0.bin")

        self.kokoro = Kokoro(str(model_path), str(voices_path))

    @staticmethod
    def _ensure_file(path: Path, url: str):
        if path.exists():
            return
        print(f"[INFO] Downloading {path.name} (this only happens once)...")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        tmp_path = path.with_suffix(path.suffix + ".part")
        with open(tmp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        tmp_path.rename(path)
        print(f"[INFO] Downloaded {path.name}")

    def speak(self, text, check_interrupts=True):
        """Speak text, sentence by sentence, with optional interrupt checking"""
        print(f"[Jarvis]: {text}")

        if not self.kokoro:
            print("[WARN] Kokoro not available, text output only")
            return

        self.interrupt_requested = False
        self.is_speaking = True

        if check_interrupts and self.voice_recognizer:
            self.voice_recognizer.start_interrupt_detection()

        try:
            for sentence in split_sentences(text):
                if self._should_stop(check_interrupts):
                    print("[INFO] Speech interrupted")
                    break
                self._synthesize_and_play(sentence)
        except Exception as e:
            print(f"[ERROR] TTS error: {e}")
        finally:
            self.is_speaking = False
            if check_interrupts and self.voice_recognizer:
                self.voice_recognizer.stop_interrupt_detection()
                self.voice_recognizer.clear_interrupt()

    def _should_stop(self, check_interrupts):
        if not check_interrupts:
            return False
        return bool(self.interrupt_requested or (self.voice_recognizer and self.voice_recognizer.check_interrupt()))

    def _synthesize_and_play(self, text):
        """Synthesize one sentence and play it - kokoro.create() returns
        (samples, sample_rate) already decoded (no raw-bytes parsing needed,
        unlike Piper's subprocess pipe)."""
        try:
            samples, sample_rate = self.kokoro.create(
                text, voice=self.voice, speed=self.speed, lang=self.lang,
            )
            if samples is None or len(samples) == 0:
                return
            sd.play(samples, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            print(f"[ERROR] Speech synthesis failed: {e}")

    def interrupt(self):
        """Request speech interruption - stops audio immediately, not just
        at the next sentence boundary."""
        self.interrupt_requested = True
        if self.is_speaking:
            print("[INFO] Speech interrupted by request")
        try:
            sd.stop()
        except Exception:
            pass
