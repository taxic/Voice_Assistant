# interruptible_tts.py

import pyttsx3
import threading
import time
import queue


class InterruptibleTTS:
    def __init__(self, voice_recognizer=None):
        self.engine = pyttsx3.init()
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False
        self.speech_thread = None
        self.speech_queue = queue.Queue()
        
        # Configure TTS settings
        self.engine.setProperty('rate', 150)  # Adjust speech rate
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)
    
    def speak(self, text, check_interrupts=True):
        """Speak text with optional interrupt checking"""
        print(f"[Jarvis]: {text}")
        
        if not check_interrupts:
            # Simple non-interruptible speech
            self.engine.say(text)
            self.engine.runAndWait()
            return
        
        # Interruptible speech
        self.interrupt_requested = False
        self.is_speaking = True
        
        # Start interrupt detection if voice recognizer is available
        if self.voice_recognizer:
            self.voice_recognizer.start_interrupt_detection()
        
        # Split text into chunks for more responsive interruption
        chunks = self._split_text_into_chunks(text)
        
        try:
            for chunk in chunks:
                if self.interrupt_requested or (self.voice_recognizer and self.voice_recognizer.check_interrupt()):
                    print("[INFO] Speech interrupted")
                    self.engine.stop()
                    break
                
                self.engine.say(chunk)
                self.engine.runAndWait()
                
                # Small pause between chunks to check for interrupts
                time.sleep(0.1)
                
        except Exception as e:
            print(f"[ERROR] TTS error: {e}")
        finally:
            self.is_speaking = False
            if self.voice_recognizer:
                self.voice_recognizer.stop_interrupt_detection()
                self.voice_recognizer.clear_interrupt()
    
    def _split_text_into_chunks(self, text, max_chunk_size=50):
        """Split text into smaller chunks for more responsive interruption"""
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(' '.join(current_chunk)) > max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def interrupt(self):
        """Request speech interruption"""
        self.interrupt_requested = True
        if self.is_speaking:
            self.engine.stop()
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
