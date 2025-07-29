#!/usr/bin/env python3
"""
Test script for calendar functionality in the GUI
"""

import sys
from datetime import datetime
from intent_parser import IntentParser
from commands import get_calendar_events_for_date, add_calendar_event

def test_calendar_intents():
    """Test that calendar intents are properly detected"""
    print("Testing calendar intent detection...")
    
    intent_parser = IntentParser()
    
    # Test calendar viewing intents
    view_messages = [
        "What's on my calendar today?",
        "Show me my events for tomorrow",
        "What meetings do I have this week?",
        "Check my schedule for Monday"
    ]
    
    for message in view_messages:
        intent = intent_parser.parse_intent(message)
        print(f"Message: '{message}' -> Intent: {intent}")
        expected = intent == "calendar_view"
        print(f"✓ Correct" if expected else f"✗ Expected calendar_view, got {intent}")
        print()
    
    # Test calendar adding intents
    add_messages = [
        "Schedule a meeting tomorrow at 2 PM",
        "Add doctor appointment next week",
        "Book lunch with John on Friday",
        "Create an event for team standup"
    ]
    
    for message in add_messages:
        intent = intent_parser.parse_intent(message)
        print(f"Message: '{message}' -> Intent: {intent}")
        expected = intent == "calendar_add"
        print(f"✓ Correct" if expected else f"✗ Expected calendar_add, got {intent}")
        print()

def test_calendar_functions():
    """Test calendar functions directly"""
    print("Testing calendar functions...")
    
    try:
        # Test viewing events for today
        print("Testing get_calendar_events_for_date for today:")
        today = datetime.now().strftime('%Y-%m-%d')
        events = get_calendar_events_for_date(today)
        print(f"Today's events: {events}")
        print()
        
        # Test adding an event (this would require Google Calendar auth)
        print("Testing add_calendar_event (may require authentication):")
        # We'll just test the function signature, not actually add an event
        try:
            # This will likely fail without proper Google Calendar setup, but that's expected
            test_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
            result = add_calendar_event("Test Event", test_time.isoformat(), 60)
            print(f"Add event result: {result}")
        except Exception as e:
            print(f"Add event failed (expected without Google Calendar setup): {e}")
        
    except Exception as e:
        print(f"Calendar function test failed: {e}")
    
def test_gui_integration():
    """Test that GUI calendar methods would work"""
    print("Testing GUI calendar integration...")
    
    # Import the GUI class
    from text_assistant_gui import TextAssistantGUI
    
    # Create a mock GUI instance (without actually showing the window)
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create GUI instance
        app = TextAssistantGUI()
        app.root.withdraw()  # Hide this window too
        
        # Test calendar view handler
        print("Testing handle_calendar_view:")
        test_messages = [
            "What's on my calendar today?",
            "Show me tomorrow's events",
            "What do I have scheduled for next Monday?"
        ]
        
        for message in test_messages:
            try:
                result = app.handle_calendar_view(message)
                print(f"Message: '{message}' -> Result: {result[:100]}...")
            except Exception as e:
                print(f"Message: '{message}' -> Error: {e}")
        
        print()
        
        # Test calendar add handler
        print("Testing handle_calendar_add:")
        add_test_messages = [
            "Schedule a meeting tomorrow at 2 PM",
            "Add doctor appointment next Friday at 10 AM"
        ]
        
        for message in add_test_messages:
            try:
                result = app.handle_calendar_add(message)
                print(f"Message: '{message}' -> Result: {result[:100]}...")
            except Exception as e:
                print(f"Message: '{message}' -> Error: {e}")
        
        # Clean up
        app.root.destroy()
        root.destroy()
        
    except Exception as e:
        print(f"GUI integration test failed: {e}")
        root.destroy()

if __name__ == "__main__":
    print("=== Calendar GUI Integration Test ===")
    print()
    
    print("1. Testing Intent Detection")
    print("-" * 30)
    test_calendar_intents()
    
    print("2. Testing Calendar Functions")
    print("-" * 30)
    test_calendar_functions()
    
    print("3. Testing GUI Integration")
    print("-" * 30)
    test_gui_integration()
    
    print("\n=== Test Complete ===")
