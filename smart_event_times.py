#!/usr/bin/env python3
"""
Smart default times for calendar events
Provides intelligent time suggestions based on event types
"""

import re
from datetime import datetime, time

class SmartEventTimes:
    """
    Provides smart default times for common event types
    """
    
    def __init__(self):
        # Define default times for common event types
        self.default_times = {
            # Meals
            'breakfast': time(8, 0),   # 8:00 AM
            'brunch': time(10, 30),    # 10:30 AM  
            'lunch': time(13, 0),      # 1:00 PM
            'dinner': time(19, 0),     # 7:00 PM
            'supper': time(19, 30),    # 7:30 PM
        }
        
        # Define default durations (in minutes) for event types
        self.default_durations = {
            # Meals
            'breakfast': 30,
            'brunch': 90,
            'lunch': 60,
            'dinner': 90,
            'supper': 90,
            
            # Default fallback
            'default': 60
        }
        
        # Compile regex patterns for better matching
        self.event_patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for matching event types"""
        patterns = {}
        
        # Create patterns that match word boundaries to avoid partial matches
        for event_type in self.default_times.keys():
            if event_type != 'default':
                # Create pattern that matches the event type as a whole word
                pattern = r'\b' + re.escape(event_type.lower()) + r'\b'
                patterns[event_type] = re.compile(pattern, re.IGNORECASE)
        
        return patterns
    
    def detect_event_type(self, event_description):
        """
        Detect the type of event from its description
        Returns the matched event type or 'default' if no match
        """
        event_description_lower = event_description.lower()
        
        # Check each pattern
        for event_type, pattern in self.event_patterns.items():
            if pattern.search(event_description_lower):
                return event_type
        
        # No specific type detected
        return 'default'
    
    def get_smart_time(self, event_description, fallback_time="10:00"):
        """
        Get a smart default time for an event based on its description
        
        Args:
            event_description (str): Description of the event
            fallback_time (str): Fallback time in HH:MM format if no smart match
            
        Returns:
            str: Time in HH:MM format (24-hour)
        """
        event_type = self.detect_event_type(event_description)
        
        if event_type in self.default_times:
            smart_time = self.default_times[event_type]
            return smart_time.strftime("%H:%M")
        
        # Return fallback time
        return fallback_time
    
    def get_smart_duration(self, event_description, fallback_duration=60):
        """
        Get a smart default duration for an event based on its description
        
        Args:
            event_description (str): Description of the event
            fallback_duration (int): Fallback duration in minutes
            
        Returns:
            int: Duration in minutes
        """
        event_type = self.detect_event_type(event_description)
        
        if event_type in self.default_durations:
            return self.default_durations[event_type]
        
        # Return fallback duration
        return fallback_duration
    
    def get_event_suggestions(self, event_description):
        """
        Get comprehensive suggestions for an event
        
        Args:
            event_description (str): Description of the event
            
        Returns:
            dict: Dictionary with 'time', 'duration', and 'type' keys
        """
        event_type = self.detect_event_type(event_description)
        
        return {
            'type': event_type,
            'time': self.get_smart_time(event_description),
            'duration': self.get_smart_duration(event_description)
        }

# Create a global instance for easy importing
smart_times = SmartEventTimes()

# Test function to verify the functionality
def test_smart_times():
    """Test the smart times functionality"""
    test_events = [
        "lunch with John",
        "doctor appointment",
        "team meeting",
        "coffee with Sarah",
        "dinner at restaurant",
        "movie night",
        "gym session",
        "grocery shopping",
        "flight to London",
        "random event"
    ]
    
    print("Testing Smart Event Times:")
    print("=" * 50)
    
    for event in test_events:
        suggestions = smart_times.get_event_suggestions(event)
        print(f"Event: '{event}'")
        print(f"  Type: {suggestions['type']}")
        print(f"  Time: {suggestions['time']}")
        print(f"  Duration: {suggestions['duration']} minutes")
        print()

if __name__ == "__main__":
    test_smart_times()
