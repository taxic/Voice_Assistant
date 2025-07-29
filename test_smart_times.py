#!/usr/bin/env python3
"""
Test script for smart default times functionality
"""

from text_assistant_gui import TextAssistantGUI
import tkinter as tk
from datetime import datetime

def test_smart_calendar_times():
    """Test that smart default times are being used correctly"""
    print("Testing Smart Calendar Default Times")
    print("=" * 50)
    
    # Create a mock GUI instance (without showing the window)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create GUI instance
        app = TextAssistantGUI()
        app.root.withdraw()  # Hide this window too
        
        # Test cases with events that should use smart defaults
        test_messages = [
            "schedule lunch tomorrow",           # Should use 13:00 (1 PM)
            "add dinner tonight",               # Should use 19:00 (7 PM) 
            "book doctor appointment tomorrow", # Should use 10:00 (10 AM)
            "gym session today",                # Should use 18:00 (6 PM)
            "coffee with Sarah tomorrow",       # Should use 10:00 (10 AM)
            "movie night this Friday",         # Should use 19:30 (7:30 PM)
            "team meeting next Monday",         # Should use 10:00 (10 AM)
            "grocery shopping tomorrow",        # Should use 14:00 (2 PM)
        ]
        
        print("Testing events without specific times (should use smart defaults):")
        print()
        
        for message in test_messages:
            try:
                result = app.handle_calendar_add(message)
                print(f"Message: '{message}'")
                print(f"Result: {result}")
                print()
            except Exception as e:
                print(f"Message: '{message}' -> Error: {e}")
                print()
        
        # Clean up
        app.root.destroy()
        root.destroy()
        
    except Exception as e:
        print(f"Test failed: {e}")
        root.destroy()

def test_voice_assistant_calendar():
    """Test the voice assistant calendar functionality with smart times"""
    print("Testing Voice Assistant Calendar with Smart Times")
    print("=" * 50)
    
    # Import and test the command parser directly
    from command_parser import parse_calendar_add
    from llm_interface import LLMInterface
    
    try:
        llm = LLMInterface()
        
        test_commands = [
            "schedule lunch tomorrow",
            "add dinner tonight", 
            "book doctor appointment",
            "gym session today",
            "coffee with Sarah",
            "movie night Friday",
        ]
        
        print("Testing voice assistant calendar parsing:")
        print()
        
        for command in test_commands:
            try:
                result = parse_calendar_add(llm, command)
                print(f"Command: '{command}'")
                if result:
                    print(f"  Summary: {result.get('summary', 'N/A')}")
                    print(f"  Start Time: {result.get('start_time', 'N/A')}")
                    print(f"  Duration: {result.get('duration_minutes', 'N/A')} minutes")
                else:
                    print("  Result: Failed to parse")
                print()
            except Exception as e:
                print(f"Command: '{command}' -> Error: {e}")
                print()
                
    except Exception as e:
        print(f"Voice assistant test failed: {e}")

if __name__ == "__main__":
    print("=== Smart Times Integration Tests ===")
    print()
    
    # Test GUI integration
    test_smart_calendar_times()
    
    print()
    print("-" * 50)
    print()
    
    # Test voice assistant integration
    test_voice_assistant_calendar()
    
    print("\\n=== Tests Complete ===")
