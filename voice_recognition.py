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
        """Listen until a finalized non-empty utterance or `timeout` seconds
        of silence elapse, whichever comes first.

        `timeout` is a wall-clock deadline, not just the gap between audio
        chunks - audio keeps arriving continuously from the mic every ~0.5s
        regardless of whether anyone is speaking, so bounding only the
        per-chunk wait meant this almost never actually timed out while
        silent. But the deadline isn't fixed either: every chunk where Vosk
        reports a non-empty partial transcript (i.e. the user is actively
        mid-utterance) pushes the deadline `timeout` seconds further out, so
        someone who starts talking just before the deadline doesn't get cut
        off - only a stretch of genuine silence that long ends the call.
        Pass timeout=None to wait indefinitely (used for wake-word
        listening, which is meant to block until the wake word is heard).
        """
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                               device=self.device, dtype='int16',
                               channels=1, callback=self._callback):
            rec = vosk.KaldiRecognizer(self.model, self.samplerate)
            deadline = time.time() + timeout if timeout is not None else None
            while True:
                if deadline is not None:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        print("[WARN] Listening timed out.")
                        return None
                else:
                    remaining = None

                try:
                    data = self.q.get(timeout=remaining)
                except queue.Empty:
                    print("[WARN] Listening timed out.")
                    return None

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    collected_text = result.get("text", "")
                    if collected_text:
                        return collected_text.lower()
                elif deadline is not None:
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    if partial:
                        deadline = time.time() + timeout

    def listen_for_wake_word(self):
        print(">> Listening for wake word...")
        while True:
            text = self._listen(timeout=None)
            if text and self.wake_word in text:
                print(f"[Wake word detected]: {self.wake_word}")
                return

    def listen_for_command(self, timeout=10):
        print(">> Listening for command...")
        command = self._listen(timeout=timeout)
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
