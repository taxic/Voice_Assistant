# simple_tts.py

import platform
import subprocess
import threading
import time
from config_manager import config

class SimpleTTS:
    def __init__(self, voice_recognizer=None):
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False
        self.speech_thread = None
        
        # Use Windows SAPI for reliable TTS
        self.use_windows_sapi = platform.system() == "Windows"
        
        if self.use_windows_sapi:
            print("[INFO] Using Windows SAPI TTS for reliable audio")
        else:
            print("[INFO] Using system TTS fallback")
    
    def speak(self, text, check_interrupts=True):
        """Speak text using Windows SAPI TTS"""
        print(f"[Jarvis]: {text}")
        
        if not check_interrupts:
            # Simple non-interruptible speech
            self._speak_direct(text)
            return
        
        # Interruptible speech
        self.interrupt_requested = False
        self.is_speaking = True
        
        # Start interrupt detection if available
        if self.voice_recognizer:
            self.voice_recognizer.start_interrupt_detection()
        
        try:
            self._speak_direct(text)
        except Exception as e:
            print(f"[ERROR] TTS error: {e}")
        finally:
            self.is_speaking = False
            if self.voice_recognizer:
                self.voice_recognizer.stop_interrupt_detection()
                self.voice_recognizer.clear_interrupt()
    
    def _speak_direct(self, text):
        """Direct speech using Windows SAPI"""
        if self.interrupt_requested:
            return
        
        try:
            if self.use_windows_sapi:
                # Use Windows Speech API via PowerShell
                # This is reliable and handles volume properly
                volume = int(config.get('tts.volume', 0.5) * 100)  # Convert to 0-100
                rate = config.get('tts.rate', 0)  # Speech rate (-10 to 10)
                
                powershell_cmd = f"""
Add-Type -AssemblyName System.Speech;
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer;
$speech.Volume = {volume};
$speech.Rate = {rate};
$speech.Speak('{text.replace("'", "''")}');
"""
                
                # Run PowerShell TTS
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    print(f"[ERROR] Windows TTS failed: {result.stderr}")
                    self._speak_fallback(text)
            else:
                self._speak_fallback(text)
                
        except Exception as e:
            print(f"[ERROR] Direct TTS failed: {e}")
            self._speak_fallback(text)
    
    def _speak_fallback(self, text):
        """Fallback TTS for non-Windows or when SAPI fails"""
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["say", text], check=True, timeout=30)
            elif platform.system() == "Linux":
                # Try espeak or festival
                try:
                    subprocess.run(["espeak", text], check=True, timeout=30)
                except FileNotFoundError:
                    try:
                        subprocess.run(["festival", "--tts"], input=text, text=True, check=True, timeout=30)
                    except FileNotFoundError:
                        print("[WARN] No TTS engine found on Linux")
            else:
                print("[WARN] No fallback TTS available")
        except Exception as e:
            print(f"[ERROR] Fallback TTS failed: {e}")
    
    def interrupt(self):
        """Request speech interruption"""
        self.interrupt_requested = True
        
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
    
    def _split_text_into_sentences(self, text):
        """Keep this method for compatibility"""
        # For simple TTS, we don't need chunking - Windows SAPI handles it well
        return [text]
