# interruptible_tts.py

from piper_tts import PiperTTS
import threading
import time
import queue


class InterruptibleTTS:
    def __init__(self, voice_recognizer=None):
        # Use Piper TTS instead of pyttsx3
        self.engine = PiperTTS(voice_recognizer=voice_recognizer)
        self.voice_recognizer = voice_recognizer
        self.is_speaking = False
        self.interrupt_requested = False
        self.speech_thread = None
        self.speech_queue = queue.Queue()
    
    def speak(self, text, check_interrupts=True):
        """Speak text with optional interrupt checking"""
        # Delegate to the Piper TTS engine which handles all the functionality
        self.engine.speak(text, check_interrupts=check_interrupts)
        
        # Update our state to match the engine's state
        self.is_speaking = self.engine.is_speaking
        self.interrupt_requested = self.engine.interrupt_requested
    
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
        self.engine.interrupt()
        self.interrupt_requested = self.engine.interrupt_requested
        self.is_speaking = self.engine.is_speaking
    
    def is_currently_speaking(self):
        """Check if currently speaking"""
        return self.engine.is_currently_speaking()
    
    def wait_for_completion(self, timeout=30):
        """Wait for current speech to complete"""
        return self.engine.wait_for_completion(timeout)
