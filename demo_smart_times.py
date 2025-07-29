#!/usr/bin/env python3
"""
Comprehensive demo of smart event times functionality
Shows both GUI and voice assistant integration
"""

from smart_event_times import smart_times
from datetime import datetime

def demo_smart_times():
    """Demonstrate the smart times functionality with examples"""
    print("=== Smart Event Times Demo ===")
    print()
    print("This system automatically suggests appropriate times and durations")
    print("for common event types when users don't specify them explicitly.")
    print()
    
    # Demo categories
    categories = {
        "Meals": [
            "breakfast with mom",
            "lunch with colleagues", 
            "dinner at restaurant",
            "brunch on Sunday"
        ],
        "Work/Business": [
            "team meeting",
            "client call",
            "job interview",
            "morning standup",
            "project review"
        ],
        "Health/Medical": [
            "doctor appointment",
            "dentist checkup",
            "therapy session",
            "gym workout"
        ],
        "Social": [
            "coffee with Sarah",
            "drinks after work",
            "birthday party",
            "movie night",
            "visit grandparents"
        ],
        "Errands": [
            "grocery shopping",
            "bank appointment",
            "post office pickup",
            "car maintenance"
        ]
    }
    
    for category, events in categories.items():
        print(f"{category}:")
        print("-" * len(category))
        
        for event in events:
            suggestions = smart_times.get_event_suggestions(event)
            
            # Convert 24-hour to 12-hour format for display
            time_24 = suggestions['time']
            hour, minute = map(int, time_24.split(':'))
            if hour == 0:
                time_12 = f"12:{minute:02d} AM"
            elif hour < 12:
                time_12 = f"{hour}:{minute:02d} AM"
            elif hour == 12:
                time_12 = f"12:{minute:02d} PM"
            else:
                time_12 = f"{hour-12}:{minute:02d} PM"
            
            duration_hours = suggestions['duration'] // 60
            duration_mins = suggestions['duration'] % 60
            if duration_hours > 0:
                duration_str = f"{duration_hours}h {duration_mins}m" if duration_mins > 0 else f"{duration_hours}h"
            else:
                duration_str = f"{duration_mins}m"
            
            print(f"  '{event}' -> {time_12} ({duration_str})")
        
        print()

def demo_user_scenarios():
    """Show realistic user scenarios"""
    print("=== Real User Scenarios ===")
    print()
    
    scenarios = [
        ("User says: 'Schedule lunch tomorrow'", "lunch tomorrow"),
        ("User says: 'Book a doctor appointment'", "doctor appointment"),
        ("User says: 'Add gym session to my calendar'", "gym session"),
        ("User says: 'Meeting with the team next Monday'", "team meeting next Monday"),
        ("User says: 'Coffee with John on Friday'", "coffee with John on Friday"),
        ("User says: 'Movie night this weekend'", "movie night this weekend"),
        ("User says: 'Grocery shopping trip'", "grocery shopping"),
        ("User says: 'Dinner with family tonight'", "dinner with family tonight"),
    ]
    
    for description, event_text in scenarios:
        print(description)
        suggestions = smart_times.get_event_suggestions(event_text)
        
        # Convert time to 12-hour format
        time_24 = suggestions['time']
        hour, minute = map(int, time_24.split(':'))
        if hour == 0:
            time_12 = f"12:{minute:02d} AM"
        elif hour < 12:
            time_12 = f"{hour}:{minute:02d} AM"
        elif hour == 12:
            time_12 = f"12:{minute:02d} PM"
        else:
            time_12 = f"{hour-12}:{minute:02d} PM"
        
        print(f"  → System suggests: {time_12}, {suggestions['duration']} minutes")
        print(f"  → Event type detected: {suggestions['type']}")
        print()

def demo_integration_example():
    """Show how this integrates with the assistant"""
    print("=== Integration Example ===")
    print()
    print("When a user interacts with the assistant:")
    print()
    
    print("1. User: 'Schedule lunch tomorrow'")
    print("2. System detects event type: 'lunch'")
    print("3. Smart defaults applied:")
    print("   - Time: 1:00 PM (13:00)")
    print("   - Duration: 60 minutes") 
    print("4. Assistant creates calendar event for tomorrow at 1:00 PM")
    print("5. Assistant responds: 'I've scheduled lunch for tomorrow at 1:00 PM'")
    print()
    
    print("Benefits:")
    print("- Users don't need to specify obvious details")
    print("- Events are scheduled at sensible times")
    print("- Consistent scheduling patterns")
    print("- Reduces back-and-forth clarification")
    print("- Works for both voice and text interfaces")

if __name__ == "__main__":
    demo_smart_times()
    print()
    demo_user_scenarios()
    print()
    demo_integration_example()
