# enhanced_interruptible_tts.py

import os
import subprocess
import tempfile
import platform
from pathlib import Path
import time
import threading
import queue
import re
from config_manager import config


class EnhancedInterruptibleTTS:
    def __init__(self, voice_recognizer=None):
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False
        self.speech_thread = None
        self.audio_process = None
        self.temp_files = []

        # Piper settings
        self.piper_dir = Path.cwd() / "piper"
        self.models_dir = self.piper_dir / "models"
        self.piper_executable = None
        self.current_model = None
        self.current_config = None

        # Enhanced voice settings
        self.default_voice = config.get('tts.voice', 'en_GB-southern_english_female-low')
        self.speech_rate = config.get('tts.rate', 0)  # -10 to 10
        self.volume = config.get('tts.volume', 0.8)  # 0.0 to 1.0

        # Initialize Piper
        self._setup_piper()

    def _setup_piper(self):
        """Download and setup Piper TTS if not already available"""
        try:
            # Create directories if they don't exist
            self.piper_dir.mkdir(exist_ok=True)
            self.models_dir.mkdir(exist_ok=True)

            # Check for existing Piper executable in multiple possible locations
            possible_paths = [
                self.piper_dir / "piper.exe",
                self.piper_dir / "piper" / "piper.exe",  # Common nested structure
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.piper_executable = str(path)
                    print(f"[INFO] Found Piper executable at: {self.piper_executable}")
                    break
            else:
                print("[WARN] Piper executable not found, TTS will be limited")
                return

            # Use existing voice model or fall back
            voice_model_path = self.models_dir / f"{self.default_voice}.onnx"
            voice_config_path = self.models_dir / f"{self.default_voice}.onnx.json"
            
            if voice_model_path.exists() and voice_config_path.exists():
                self.current_model = str(voice_model_path)
                self.current_config = str(voice_config_path)
            else:
                print(f"[WARN] Voice model {self.default_voice} not found")
                # Try to find any available model
                for model_file in self.models_dir.glob("*.onnx"):
                    if model_file.with_suffix('.onnx.json').exists():
                        self.current_model = str(model_file)
                        self.current_config = str(model_file.with_suffix('.onnx.json'))
                        print(f"[INFO] Using available voice model: {model_file.name}")
                        break

            if self.piper_executable and self.current_model:
                print(f"[INFO] Enhanced TTS initialized with voice: {self.default_voice}")
            else:
                print("[WARN] Piper not fully available, falling back to basic TTS")

        except Exception as e:
            print(f"[ERROR] Failed to initialize Enhanced TTS: {e}")

    def speak(self, text, check_interrupts=True):
        """Speak text with enhanced interrupt handling and natural flow"""
        print(f"[Jarvis]: {text}")

        if not self.piper_executable or not self.current_model:
            # Fallback to system TTS
            self._fallback_tts(text)
            return

        if not check_interrupts:
            # Simple non-interruptible speech
            self._synthesize_and_play_single(text)
            return

        # Enhanced interruptible speech
        self.interrupt_requested = False
        self.is_speaking = True

        # Start interrupt detection if voice recognizer is available
        if self.voice_recognizer:
            self.voice_recognizer.start_interrupt_detection()

        try:
            # Use sentence-based chunking for natural flow
            chunks = self._split_into_sentences(text)
            
            for i, chunk in enumerate(chunks):
                if self.interrupt_requested or (self.voice_recognizer and self.voice_recognizer.check_interrupt()):
                    print("[INFO] Speech interrupted")
                    break

                # Synthesize and play each chunk
                self._synthesize_and_play_chunk(chunk, i == len(chunks) - 1)

        except Exception as e:
            print(f"[ERROR] Enhanced TTS error: {e}")
        finally:
            self.is_speaking = False
            self._cleanup_temp_files()
            if self.voice_recognizer:
                self.voice_recognizer.stop_interrupt_detection()
                self.voice_recognizer.clear_interrupt()

    def _split_into_sentences(self, text):
        """Split text into natural sentence chunks for better flow"""
        # Clean up the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split by sentences, periods, question marks, exclamation marks
        # Keep the punctuation with the sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences and group short ones
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would make the chunk too long, start a new one
            if current_chunk and len(current_chunk + " " + sentence) > 150:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # If we only have one very long chunk, split it further
        if len(chunks) == 1 and len(chunks[0]) > 200:
            words = chunks[0].split()
            mid_point = len(words) // 2
            
            # Try to split at a natural break point
            for i in range(mid_point - 10, mid_point + 10):
                if i < len(words) and words[i] in ['and', 'but', 'or', 'the', 'a', 'an']:
                    chunks = [' '.join(words[:i]), ' '.join(words[i:])]
                    break
            else:
                # If no natural break found, just split in half
                chunks = [' '.join(words[:mid_point]), ' '.join(words[mid_point:])]
        
        return chunks if chunks else [text]

    def _synthesize_and_play_chunk(self, text, is_last_chunk=False):
        """Synthesize and play a single chunk of text"""
        try:
            # Create temporary file for this chunk
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_path = tmp_file.name
            self.temp_files.append(wav_path)

            # Use Piper to synthesize speech
            cmd = [
                self.piper_executable,
                "--model", self.current_model,
                "--output_file", wav_path
            ]

            # Run Piper subprocess with timeout
            process = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=20
            )

            if process.returncode != 0:
                print(f"[ERROR] Piper failed for chunk: {process.stderr}")
                return

            # Play the generated audio file immediately
            self._play_wav_file_immediate(wav_path)

        except subprocess.TimeoutExpired:
            print("[ERROR] TTS synthesis timeout")
        except Exception as e:
            print(f"[ERROR] Chunk synthesis failed: {e}")

    def _synthesize_and_play_single(self, text):
        """Synthesize and play entire text as single chunk"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_path = tmp_file.name
            self.temp_files.append(wav_path)

            cmd = [
                self.piper_executable,
                "--model", self.current_model,
                "--output_file", wav_path
            ]

            process = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=30
            )

            if process.returncode != 0:
                print(f"[ERROR] Piper failed: {process.stderr}")
                return

            self._play_wav_file_immediate(wav_path)

        except Exception as e:
            print(f"[ERROR] Single synthesis failed: {e}")

    def _play_wav_file_immediate(self, wav_path):
        """Play WAV file with immediate execution and interrupt checking"""
        try:
            if platform.system() == "Windows":
                # Use PowerShell for immediate playback with better control
                ps_command = f"""
$player = New-Object System.Media.SoundPlayer '{wav_path}';
$player.PlaySync();
"""
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    check=True,
                    timeout=60
                )
            else:
                # For other systems, try common audio players
                for player in ["aplay", "paplay", "play", "afplay"]:
                    try:
                        subprocess.run([player, wav_path], check=True, timeout=30)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    print("[WARN] No suitable audio player found")

        except subprocess.TimeoutExpired:
            print("[WARN] Audio playback timeout")
        except Exception as e:
            print(f"[ERROR] Audio playback failed: {e}")

    def _fallback_tts(self, text):
        """Fallback to system TTS when Piper is not available"""
        try:
            if platform.system() == "Windows":
                # Use Windows SAPI
                volume = int(self.volume * 100)
                rate = int(self.speech_rate)
                
                ps_command = f"""
Add-Type -AssemblyName System.Speech;
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer;
$speech.Volume = {volume};
$speech.Rate = {rate};
$speech.Speak('{text.replace("'", "''")}');
"""
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    timeout=60
                )
            else:
                # For other systems
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["say", text], timeout=30)
                elif platform.system() == "Linux":
                    try:
                        subprocess.run(["espeak", text], timeout=30)
                    except FileNotFoundError:
                        print("[WARN] No fallback TTS available")
                        
        except Exception as e:
            print(f"[ERROR] Fallback TTS failed: {e}")

    def _cleanup_temp_files(self):
        """Clean up temporary audio files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"[WARN] Failed to clean up temp file {temp_file}: {e}")
        self.temp_files.clear()

    def interrupt(self):
        """Request speech interruption"""
        self.interrupt_requested = True
        
        # Kill any running audio process
        if self.audio_process and self.audio_process.poll() is None:
            try:
                self.audio_process.terminate()
                self.audio_process.wait(timeout=1)
            except Exception:
                try:
                    self.audio_process.kill()
                except Exception:
                    pass
        
        if self.is_speaking:
            print("[INFO] Speech interrupted by request")

    def is_currently_speaking(self):
        """Check if currently speaking"""
        return self.is_speaking

    def wait_for_completion(self, timeout=30):
        """Wait for current speech to complete"""
        start_time = time.time()
        while self.is_speaking and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        return not self.is_speaking
    
    def set_voice_settings(self, rate=None, volume=None):
        """Update voice settings"""
        if rate is not None:
            self.speech_rate = max(-10, min(10, rate))
        if volume is not None:
            self.volume = max(0.0, min(1.0, volume))