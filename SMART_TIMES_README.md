# Smart Event Times Feature

## Overview

The Smart Event Times feature automatically suggests appropriate default times and durations for calendar events when users don't specify them explicitly. This makes scheduling more intuitive and reduces the need for back-and-forth clarification.

## How It Works

1. **Event Type Detection**: The system analyzes the event description to identify the type of event (e.g., "lunch", "meeting", "doctor appointment")
2. **Smart Defaults**: Based on the detected type, appropriate default times and durations are applied
3. **Fallback**: If no specific event type is detected, sensible general defaults are used (10:00 AM, 60 minutes)

## Supported Event Types

### Meals
- **Breakfast**: 8:00 AM, 30 minutes
- **Brunch**: 10:30 AM, 90 minutes  
- **Lunch**: 1:00 PM, 60 minutes
- **Dinner**: 7:00 PM, 90 minutes
- **Supper**: 7:30 PM, 90 minutes

### Business/Work
- **Meeting**: 10:00 AM, 60 minutes
- **Conference**: 9:00 AM, 120 minutes
- **Call**: 2:00 PM, 30 minutes
- **Interview**: 2:00 PM, 60 minutes
- **Standup**: 9:00 AM, 15 minutes
- **Review**: 3:00 PM, 90 minutes

### Medical/Health
- **Appointment**: 10:00 AM, 30 minutes
- **Doctor**: 10:00 AM, 30 minutes
- **Dentist**: 2:00 PM, 60 minutes
- **Therapy**: 4:00 PM, 60 minutes
- **Workout/Gym**: 6:00 PM, 60-90 minutes

### Social
- **Coffee**: 10:00 AM, 60 minutes
- **Drinks**: 6:00 PM, 120 minutes
- **Party**: 7:00 PM, 180 minutes
- **Movie**: 7:30 PM, 150 minutes

### Errands
- **Shopping**: 2:00 PM, 90 minutes
- **Groceries**: 10:00 AM, 60 minutes
- **Bank**: 11:00 AM, 30 minutes
- **Post Office**: 11:00 AM, 20 minutes

## Example Usage

### Text GUI
```
User: "schedule lunch tomorrow"
Assistant: "The event 'Lunch' has been created for tomorrow at 1:00 PM with a 60-minute duration."
```

### Voice Assistant
```
User: "book a doctor appointment"
Assistant: "I've scheduled a doctor appointment for today at 10:00 AM."
```

## Integration Points

### Text Assistant GUI
- Integrated in `text_assistant_gui.py` via the `handle_calendar_add()` method
- Uses smart defaults in the LLM prompt for event extraction

### Voice Assistant  
- Integrated in `command_parser.py` via the `parse_calendar_add()` function
- Provides context to the LLM about appropriate defaults

### Core Module
- `smart_event_times.py` contains the main `SmartEventTimes` class
- Global instance `smart_times` available for import

## Benefits

1. **Reduced Friction**: Users don't need to specify obvious details like "lunch at 1 PM"
2. **Consistency**: Events are scheduled at predictable, sensible times
3. **Better UX**: Fewer clarification questions needed
4. **Natural Language**: Supports both voice and text input
5. **Extensible**: Easy to add new event types and modify defaults

## Technical Details

### Pattern Matching
- Uses regex word boundary matching to avoid partial matches
- Case-insensitive matching
- Supports compound phrases (e.g., "post office", "team meeting")

### Fallback Strategy
- If no specific event type is detected, uses general defaults
- If LLM parsing fails, provides helpful error messages
- Graceful degradation maintains functionality

### Configuration
Default times and durations are defined in `smart_event_times.py` and can be easily modified to suit different user preferences or cultural contexts.

## Testing

Run the test files to verify functionality:
- `python smart_event_times.py` - Core functionality test
- `python test_smart_times.py` - Integration test
- `python demo_smart_times.py` - Comprehensive demo
- `python test_lunch_example.py` - Specific example test

## Future Enhancements

- User-configurable defaults per event type
- Time zone awareness for different regions  
- Learning from user scheduling patterns
- Holiday and weekend-aware scheduling
- Integration with external calendar availability
