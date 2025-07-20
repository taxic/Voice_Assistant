# test_interrupt.py

import time
import threading
from voice_recognition import VoiceRecognizer
from interruptible_tts import InterruptibleTTS

def test_interrupt_functionality():
    """Test the interrupt functionality with a simple simulation"""
    print("Testing interrupt functionality...")
    
    # Initialize components
    recognizer = VoiceRecognizer()
    tts = InterruptibleTTS(voice_recognizer=recognizer)
    
    # Test 1: Simple TTS without interruption
    print("\n=== Test 1: Simple TTS (no interruption) ===")
    tts.speak("This is a test of the text-to-speech system without interruption.", check_interrupts=False)
    
    # Test 2: TTS with manual interrupt
    print("\n=== Test 2: TTS with manual interrupt ===")
    
    def manual_interrupt():
        """Simulate an interrupt after 2 seconds"""
        time.sleep(2)
        print("[TEST] Simulating interrupt...")
        tts.interrupt()
    
    # Start interrupt simulation thread
    interrupt_thread = threading.Thread(target=manual_interrupt)
    interrupt_thread.start()
    
    # Start speaking (should be interrupted)
    tts.speak("This is a longer message that should be interrupted partway through. " +
              "If the interrupt functionality is working properly, you should not hear the complete message. " +
              "This part should definitely not be spoken if the interrupt works correctly.", 
              check_interrupts=True)
    
    interrupt_thread.join()
    
    # Test 3: Voice recognition interrupt simulation
    print("\n=== Test 3: Voice recognition interrupt simulation ===")
    
    def simulate_voice_interrupt():
        """Simulate voice interrupt detection"""
        time.sleep(1)
        print("[TEST] Simulating voice interrupt detection...")
        recognizer.interrupt_detected = True
    
    # Start voice interrupt simulation
    voice_interrupt_thread = threading.Thread(target=simulate_voice_interrupt)
    voice_interrupt_thread.start()
    
    # Start speaking with voice interrupt detection
    tts.speak("This message should be interrupted by a simulated voice command. " +
              "The interrupt should stop the speech when detected.", 
              check_interrupts=True)
    
    voice_interrupt_thread.join()
    
    print("\n=== Interrupt functionality tests completed ===")

if __name__ == "__main__":
    test_interrupt_functionality()
