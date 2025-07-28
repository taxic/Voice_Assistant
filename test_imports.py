#!/usr/bin/env python3

print("Testing module imports...")

modules_to_test = [
    "voice_recognition",
    "llm_interface", 
    "memory",
    "commands",
    "interruptible_tts",
    "command_parser",
    "intent_parser",
    "calendar_interface"
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"✓ {module} imported successfully")
    except Exception as e:
        print(f"✗ {module} failed to import: {e}")

print("\nTesting weather function specifically...")
try:
    from commands import get_weather
    result = get_weather("London")
    print(f"✓ Weather function works: {result}")
except Exception as e:
    print(f"✗ Weather function error: {e}")

print("\nTesting all external dependencies...")
external_deps = [
    "requests",
    "dateparser", 
    "vosk",
    "sounddevice",
    "pyttsx3",
    "google.auth",
    "googleapiclient",
    "nltk"
]

for dep in external_deps:
    try:
        __import__(dep)
        print(f"✓ {dep} available")
    except Exception as e:
        print(f"✗ {dep} missing or error: {e}")
