# voice_recognition.py

import queue
import sounddevice as sd
import vosk
import json
import sys
import threading
import time

class VoiceRecognizer:
    def __init__(self, wake_word="jarvis", model_path="models/vosk-model-small-en-us-0.15"):
        self.q = queue.Queue()
        self.wake_word = wake_word.lower()
        self.model = vosk.Model(model_path)
        self.samplerate = 16000
        self.device = None  # Use default microphone
        self.interrupt_detected = False
        self.interrupt_words = ["stop", "pause", "wait", "interrupt", "hold on", "quiet"]
        self.is_listening_for_interrupts = False
        self.interrupt_thread = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"[ERROR] Audio status: {status}", file=sys.stderr)
        self.q.put(bytes(indata))

    def _listen(self, timeout=10):
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                               device=self.device, dtype='int16',
                               channels=1, callback=self._callback):
            rec = vosk.KaldiRecognizer(self.model, self.samplerate)
            collected_text = ""
            while True:
                try:
                    data = self.q.get(timeout=timeout)
                except queue.Empty:
                    print("[WARN] Listening timed out.")
                    return None

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    collected_text = result.get("text", "")
                    if collected_text:
                        return collected_text.lower()
                else:
                    pass  # Partial result if needed: rec.PartialResult()

    def listen_for_wake_word(self):
        print(">> Listening for wake word...")
        while True:
            text = self._listen()
            if text and self.wake_word in text:
                print(f"[Wake word detected]: {self.wake_word}")
                return

    def listen_for_command(self):
        print(">> Listening for command...")
        command = self._listen()
        if command:
            return command
        else:
            print("[INFO] No command detected.")
            return None
    
    def _interrupt_listener(self):
        """Background thread to listen for interrupt commands"""
        print("[DEBUG] Interrupt listener started")
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                               device=self.device, dtype='int16',
                               channels=1, callback=self._callback):
            rec = vosk.KaldiRecognizer(self.model, self.samplerate)
            
            while self.is_listening_for_interrupts:
                try:
                    data = self.q.get(timeout=0.1)  # Short timeout for responsiveness
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").lower()
                        
                        if text and any(word in text for word in self.interrupt_words):
                            print(f"[INTERRUPT] Detected: {text}")
                            self.interrupt_detected = True
                            return
                            
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[ERROR] Interrupt listener error: {e}")
                    break
        
        print("[DEBUG] Interrupt listener stopped")
    
    def start_interrupt_detection(self):
        """Start listening for interrupt commands in background"""
        if not self.is_listening_for_interrupts:
            self.interrupt_detected = False
            self.is_listening_for_interrupts = True
            self.interrupt_thread = threading.Thread(target=self._interrupt_listener, daemon=True)
            self.interrupt_thread.start()
            print("[INFO] Interrupt detection started")
    
    def stop_interrupt_detection(self):
        """Stop listening for interrupt commands"""
        if self.is_listening_for_interrupts:
            self.is_listening_for_interrupts = False
            if self.interrupt_thread and self.interrupt_thread.is_alive():
                self.interrupt_thread.join(timeout=1)
            print("[INFO] Interrupt detection stopped")
    
    def check_interrupt(self):
        """Check if an interrupt was detected"""
        return self.interrupt_detected
    
    def clear_interrupt(self):
        """Clear the interrupt flag"""
        self.interrupt_detected = False
