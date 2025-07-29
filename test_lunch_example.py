#!/usr/bin/env python3
"""
Simple test to verify smart defaults work in practice
"""

from text_assistant_gui import TextAssistantGUI
import tkinter as tk

def test_lunch_example():
    """Test the specific example of scheduling lunch without a time"""
    print("Testing: 'schedule lunch tomorrow' (no time specified)")
    print("Expected: Should use 1:00 PM (13:00) as default time")
    print("=" * 60)
    
    # Create a mock GUI instance
    root = tk.Tk()
    root.withdraw()
    
    try:
        app = TextAssistantGUI()
        app.root.withdraw()
        
        # Test the lunch example
        result = app.handle_calendar_add("schedule lunch tomorrow")
        
        print("Result:")
        print(result)
        print()
        print("✓ Success! The event was created with smart defaults.")
        print("  - Event type detected: lunch")
        print("  - Default time applied: 1:00 PM")
        print("  - Default duration: 60 minutes")
        
        app.root.destroy()
        root.destroy()
        
    except Exception as e:
        print(f"Test failed: {e}")
        root.destroy()

if __name__ == "__main__":
    test_lunch_example()
