#!/usr/bin/env python3
"""
Demo of the enhanced calendar scheduling functionality with time prompting
Shows how the assistant now handles events when no time is specified
"""

from smart_event_times import smart_times
from calendar_interface import GoogleCalendar
from datetime import datetime, timedelta

def demo_time_prompting():
    """Demonstrate the new time prompting functionality"""
    print("=== Enhanced Calendar Scheduling Demo ===")
    print()
    print("This demo shows how the assistant now handles calendar events when no time is specified.")
    print()
    
    # Example scenarios
    scenarios = [
        "schedule lunch tomorrow",
        "add meeting next Monday", 
        "book doctor appointment",
        "gym session today",
        "coffee with Sarah",
        "random event tomorrow"
    ]
    
    print("Example Event Scenarios:")
    print("-" * 40)
    
    for scenario in scenarios:
        print(f"\nUser says: '{scenario}'")
        
        # Get smart suggestions
        suggestions = smart_times.get_event_suggestions(scenario)
        event_type = suggestions['type']
        smart_time = suggestions['time']
        smart_duration = suggestions['duration']
        
        print(f"  Event type detected: {event_type}")
        
        if event_type != 'default':
            print(f"  Smart default: {smart_time} for {smart_duration} minutes")
            print("  → Assistant uses smart default automatically")
        else:
            print("  No smart default available")
            print("  → Assistant prompts user with two options:")
            print("    1. 'Would you like me to find a free time slot?'")
            print("    2. 'Or would you prefer to specify a time?'")
            print()
            print("  User Response Options:")
            print("    Option 1: 'Find a free slot' → Assistant checks calendar for availability")
            print("    Option 2: 'I'll specify' → Assistant asks 'What time would you like?'")

def demo_free_slot_finding():
    """Demonstrate how free slot finding works"""
    print("\n=== Free Slot Finding Demo ===")
    print()
    print("When user chooses 'find a free slot', the assistant:")
    print()
    print("1. Analyzes the user's calendar for the specified date")
    print("2. Looks for gaps between existing events")
    print("3. Considers work hours (9 AM - 5 PM by default)")
    print("4. Finds the first available slot that fits the event duration")
    print("5. Schedules the event at that time")
    print()
    
    # Show example calendar analysis
    print("Example Calendar Analysis:")
    print("-" * 30)
    print("Date: Tomorrow")
    print("Existing events:")
    print("  • 09:00-10:00: Team standup")
    print("  • 11:00-12:00: Client call") 
    print("  • 14:00-15:30: Project review")
    print()
    print("Available slots:")
    print("  • 10:00-11:00 (60 minutes)")
    print("  • 12:00-14:00 (120 minutes)")
    print("  • 15:30-17:00 (90 minutes)")
    print()
    print("For a 60-minute lunch event:")
    print("  → Assistant schedules at 10:00 AM")
    print("  → Response: 'I've scheduled lunch for tomorrow at 10:00 AM. I found a free slot at that time.'")

def demo_voice_vs_text():
    """Show how this works in both voice and text interfaces"""
    print("\n=== Voice vs Text Interface ===")
    print()
    
    print("TEXT GUI:")
    print("-" * 10)
    print("1. User types: 'schedule meeting tomorrow'")
    print("2. If no time/smart default: Dialog box appears")
    print("3. Three-option dialog:")
    print("   • Yes: Find free slot automatically")
    print("   • No: Let me specify a time")  
    print("   • Cancel: Cancel event creation")
    print("4. If 'No': Text input dialog asks for time")
    print("5. Event created with chosen/found time")
    print()
    
    print("VOICE ASSISTANT:")
    print("-" * 15)
    print("1. User says: 'schedule meeting tomorrow'")
    print("2. If no time/smart default: Assistant speaks")
    print("3. 'I notice you didn't specify a time. Would you like me to")
    print("   find a free slot, or would you prefer to specify a time?'")
    print("4. User responds: 'find a slot' or 'I'll specify 2 PM'")
    print("5. Assistant processes accordingly")
    print("6. Confirms: 'Meeting scheduled for tomorrow at [time]'")

def show_implementation_details():
    """Show technical implementation details"""
    print("\n=== Implementation Details ===")
    print()
    
    print("Key Components:")
    print("-" * 15)
    print("1. SmartEventTimes: Provides intelligent defaults")
    print("2. GoogleCalendar.find_free_time_slot(): Finds available times")
    print("3. Enhanced text_assistant_gui.py: GUI prompting")
    print("4. Enhanced main.py: Voice prompting")
    print("5. Updated command_parser.py: Handles 'default' time values")
    print()
    
    print("Flow:")
    print("-----")
    print("1. User requests event without time")
    print("2. Smart times checked for event type")
    print("3. If no smart default → prompt user")
    print("4. If 'find slot' → analyze calendar")  
    print("5. If 'specify time' → ask for time")
    print("6. Create event with determined time")
    print()
    
    print("Benefits:")
    print("-" * 8)
    print("• More flexible scheduling")
    print("• Reduces scheduling conflicts")  
    print("• User maintains control")
    print("• Works in both text and voice modes")
    print("• Leverages existing smart defaults")

if __name__ == "__main__":
    demo_time_prompting()
    demo_free_slot_finding()
    demo_voice_vs_text()
    show_implementation_details()
    
    print("\n" + "="*50)
    print("DEMO COMPLETE")
    print("="*50)
    print("The assistant now provides intelligent time prompting")
    print("when scheduling events without specified times!")
