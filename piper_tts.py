# piper_tts.py

import json
import os
import subprocess
import tempfile
import requests
import zipfile
import platform
from pathlib import Path
import time
from config_manager import config
from sentence_stream import split_sentences

import numpy as np
import sounddevice as sd


class PiperTTS:
    def __init__(self, voice_recognizer=None):
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False

        # Piper settings
        self.piper_dir = Path.cwd() / "piper"
        self.models_dir = self.piper_dir / "models"
        self.piper_executable = None
        self.current_model = None
        self.current_config = None
        self.sample_rate = 22050  # overwritten from the voice config once loaded

        # Default voice settings - British English female voice
        self.default_voice = config.get('tts.voice', 'en_GB-southern_english_female-low')

        # Initialize Piper
        self._setup_piper()

    def _setup_piper(self):
        """Download and setup Piper TTS if not already available"""
        try:
            # Create directories if they don't exist
            self.piper_dir.mkdir(exist_ok=True)
            self.models_dir.mkdir(exist_ok=True)

            # Download Piper executable if not present
            self._ensure_piper_executable()

            # Download default voice model
            self._ensure_voice_model(self.default_voice)

            print(f"[INFO] Piper TTS initialized with voice: {self.default_voice}")

        except Exception as e:
            print(f"[ERROR] Failed to initialize Piper TTS: {e}")
            print("[WARN] Falling back to basic text output")

    def _ensure_piper_executable(self):
        """Download Piper executable for Windows"""
        system = platform.system().lower()

        if system == "windows":
            exe_name = "piper.exe"
            download_url = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
        else:
            print(f"[WARN] Unsupported platform: {system}. Please install Piper manually.")
            return

        exe_path = self.piper_dir / exe_name

        if exe_path.exists():
            self.piper_executable = str(exe_path)
            return

        print("[INFO] Downloading Piper executable...")

        try:
            # Download and extract
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # Extract the zip file
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(self.piper_dir)

            os.unlink(tmp_path)

            # Find the executable in the extracted files
            for file_path in self.piper_dir.rglob(exe_name):
                self.piper_executable = str(file_path)
                break

            if not self.piper_executable:
                raise Exception(f"Could not find {exe_name} after extraction")

            print(f"[INFO] Piper executable downloaded to: {self.piper_executable}")

        except Exception as e:
            print(f"[ERROR] Failed to download Piper executable: {e}")
            raise

    def _ensure_voice_model(self, voice_name):
        """Download voice model and config if not present"""
        model_path = self.models_dir / f"{voice_name}.onnx"
        config_path = self.models_dir / f"{voice_name}.onnx.json"

        if model_path.exists() and config_path.exists():
            self.current_model = str(model_path)
            self.current_config = str(config_path)
            self._load_sample_rate()
            return

        print(f"[INFO] Downloading voice model: {voice_name}...")

        try:
            # Download model for British English female voice
            model_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low.onnx"
            config_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low.onnx.json"

            # Download model file
            response = requests.get(model_url, stream=True)
            response.raise_for_status()

            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Download config file
            response = requests.get(config_url)
            response.raise_for_status()

            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            self.current_model = str(model_path)
            self.current_config = str(config_path)
            self._load_sample_rate()

            print(f"[INFO] Voice model downloaded: {voice_name}")

        except Exception as e:
            print(f"[ERROR] Failed to download voice model {voice_name}: {e}")
            raise

    def _load_sample_rate(self):
        """Read the voice's sample rate from its .onnx.json config, needed
        to play back the raw PCM Piper outputs at the correct speed/pitch."""
        try:
            with open(self.current_config, 'r', encoding='utf-8') as f:
                voice_config = json.load(f)
            self.sample_rate = voice_config['audio']['sample_rate']
        except Exception as e:
            print(f"[WARN] Could not read sample rate from voice config ({e}), defaulting to 22050Hz")
            self.sample_rate = 22050

    def speak(self, text, check_interrupts=True):
        """Speak text, sentence by sentence, with optional interrupt checking"""
        print(f"[Jarvis]: {text}")

        if not self.piper_executable or not self.current_model:
            print("[WARN] Piper not available, text output only")
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
        """Synthesize one sentence to raw PCM and play it - no temp files,
        no second subprocess for playback (see _play_raw_audio)."""
        try:
            cmd = [
                self.piper_executable,
                "--model", self.current_model,
                "--config", self.current_config,
                "--output-raw",
            ]

            process = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )

            if process.returncode != 0:
                print(f"[ERROR] Piper failed: {process.stderr.decode(errors='replace')}")
                return

            self._play_raw_audio(process.stdout)

        except subprocess.TimeoutExpired:
            print("[ERROR] Piper synthesis timed out")
        except Exception as e:
            print(f"[ERROR] Speech synthesis failed: {e}")

    def _play_raw_audio(self, raw_pcm_bytes):
        """Play 16-bit mono PCM bytes (Piper's --output-raw format) directly
        via sounddevice - in-process, no player subprocess, and genuinely
        interruptible mid-playback via sd.stop() from another thread."""
        if not raw_pcm_bytes:
            return
        try:
            audio = np.frombuffer(raw_pcm_bytes, dtype=np.int16)
            sd.play(audio, samplerate=self.sample_rate)
            sd.wait()
        except Exception as e:
            print(f"[ERROR] Failed to play audio: {e}")

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

    def is_currently_speaking(self):
        """Check if currently speaking"""
        return self.is_speaking

    def wait_for_completion(self, timeout=30):
        """Wait for current speech to complete"""
        start_time = time.time()
        while self.is_speaking and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        return not self.is_speaking