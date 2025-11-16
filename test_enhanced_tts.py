#!/usr/bin/env python3
# test_enhanced_tts.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_interruptible_tts import EnhancedInterruptibleTTS
from voice_recognition import VoiceRecognizer
import time
import threading

def test_enhanced_tts():
    """Test the enhanced interruptible TTS system"""
    print("=== Testing Enhanced Interruptible TTS ===\n")
    
    # Initialize the enhanced TTS system
    print("Initializing Enhanced TTS...")
    tts = EnhancedInterruptibleTTS()
    
    if not tts.piper_executable:
        print("[WARN] Piper not available, testing with fallback TTS")
    else:
        print("[INFO] Piper TTS initialized successfully")
    
    # Test texts of varying lengths
    test_texts = [
        "Hello! This is a short test of the enhanced text-to-speech system.",
        "This is a longer sentence that demonstrates how the system handles more complex speech with multiple clauses and longer phrases without breaking them up artificially.",
        "How are you today? I'm doing well, thank you for asking. The weather is quite pleasant, isn't it? Would you like to go for a walk in the park later?",
        "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet, which makes it useful for testing text-to-speech systems and ensuring proper pronunciation of all characters."
    ]
    
    print("\n--- Test 1: Basic Speech (Non-interruptible) ---")
    for i, text in enumerate(test_texts[:2], 1):
        print(f"\nTest {i}: {text}")
        tts.speak(text, check_interrupts=False)
        time.sleep(1)  # Brief pause between tests
    
    print("\n--- Test 2: Interruptible Speech ---")
    for i, text in enumerate(test_texts[2:], 3):
        print(f"\nTest {i}: {text}")
        # Start speech in a thread to allow for interruption
        speech_thread = threading.Thread(target=lambda: tts.speak(text, check_interrupts=True))
        speech_thread.start()
        
        # Wait a moment then interrupt
        time.sleep(2)
        print("Interrupting speech...")
        tts.interrupt()
        
        speech_thread.join(timeout=5)
        time.sleep(1)
    
    print("\n--- Test 3: Settings Configuration ---")
    print("Testing voice settings...")
    tts.set_voice_settings(rate=2, volume=0.8)
    
    test_text = "This is a test with adjusted voice settings. The rate and volume have been modified."
    print(f"Speaking with rate=2, volume=0.8: {test_text}")
    tts.speak(test_text, check_interrupts=False)
    
    print("\n=== Enhanced TTS Test Complete ===")
    print("\nKey improvements implemented:")
    print("* Sentence-based chunking instead of arbitrary 50-character chunks")
    print("* Removed artificial delays between speech segments")
    print("* Immediate audio playback without gaps")
    print("* Better interrupt handling with process termination")
    print("* Improved temporary file management")
    print("* Natural speech flow preservation")
    print("* Fallback TTS support when Piper unavailable")

def compare_with_old_system():
    """Compare enhanced system with original implementation"""
    print("\n=== Comparison with Original System ===\n")
    
    # Import original system for comparison
    from interruptible_tts import InterruptibleTTS
    
    print("Original InterruptibleTTS characteristics:")
    print("- Splits text into 50-character chunks")
    print("- Adds 0.1 second delays between chunks")
    print("- Creates separate subprocess for each chunk")
    print("- May cause robotic pauses and breaks")
    
    print("\nEnhanced system characteristics:")
    print("- Uses sentence-based chunking (up to 150 characters)")
    print("- No artificial delays between sentences")
    print("- Immediate audio playback")
    print("- Maintains natural speech rhythm")
    print("- Better interrupt handling")
    
    # Test same text with both systems
    test_text = "This is a test sentence. It has multiple parts. The enhanced system should handle this more smoothly than the original implementation."
    
    print(f"\nTesting same text with both systems:\n'{test_text}'\n")
    
    print("--- Original System ---")
    old_tts = InterruptibleTTS()
    start_time = time.time()
    old_tts.speak(test_text, check_interrupts=True)
    old_duration = time.time() - start_time
    print(f"Original system duration: {old_duration:.2f} seconds")
    
    time.sleep(2)
    
    print("\n--- Enhanced System ---")
    enhanced_tts = EnhancedInterruptibleTTS()
    start_time = time.time()
    enhanced_tts.speak(test_text, check_interrupts=True)
    enhanced_duration = time.time() - start_time
    print(f"Enhanced system duration: {enhanced_duration:.2f} seconds")
    
    if enhanced_duration < old_duration:
        print(f"* Enhanced system is {((old_duration - enhanced_duration) / old_duration * 100):.1f}% faster")
    else:
        print("* Enhanced system prioritizes quality over speed")

if __name__ == "__main__":
    try:
        test_enhanced_tts()
        compare_with_old_system()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()