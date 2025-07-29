# Calendar Functionality in GUI

The Enhanced Assistant GUI now includes full calendar integration with Google Calendar. Here are the available features:

## Available Commands

### Viewing Calendar Events
You can ask the assistant to show your calendar events using natural language:

- **"What's on my calendar today?"**
- **"Show me my events for tomorrow"**
- **"What meetings do I have this week?"**
- **"Check my schedule for Monday"**
- **"What do I have on December 15th?"**

### Adding Calendar Events
You can ask the assistant to schedule new events:

- **"Schedule a meeting tomorrow at 2 PM"**
- **"Add doctor appointment next Friday at 10 AM"**
- **"Book lunch with John on Friday"**
- **"Create an event for team standup at 9 AM Monday"**

The assistant will automatically extract:
- Event title
- Date (defaults to today if not specified)
- Time (defaults to 10:00 AM if not specified)
- Duration (defaults to 60 minutes if not specified)

## GUI Features

### Text Interface
- Type any calendar-related request in the chat interface
- The assistant will detect your intent and respond accordingly
- All calendar interactions are saved to conversation memory

### Quick Access Button
- **"Today's Events"** button in the status bar
- Click to instantly see today's calendar events in a popup
- No typing required - just one click

### Intent Recognition
The assistant uses advanced intent parsing to understand various ways of asking about calendar events:
- "What's my schedule?" → View calendar events
- "Book a meeting" → Add calendar event  
- "Any appointments today?" → View today's events
- "Schedule something" → Add calendar event

## Technical Implementation

### Google Calendar Integration
- Uses Google Calendar API v3
- Supports OAuth2 authentication
- Automatically handles token refresh
- Timezone-aware event handling

### Natural Language Processing
- LLM-powered event detail extraction
- Supports flexible date/time formats
- Intelligent defaults for missing information
- Context-aware conversation flow

### Error Handling
- Graceful handling of authentication issues
- Clear error messages for missing information
- Fallback options when calendar is unavailable
- User-friendly guidance for proper formatting

## Setup Requirements

To use calendar functionality, you need:

1. **Google Calendar API Credentials**
   - Download `credentials.json` from Google Cloud Console
   - Place in the project directory

2. **Required Python Packages**
   - `google-auth`
   - `google-auth-oauthlib`
   - `google-auth-httplib2`
   - `google-api-python-client`
   - `dateparser`
   - `pytz`

3. **Configuration**
   - Calendar settings in `config.json`
   - Timezone configuration
   - Default calendar selection

## Examples in Action

```
You: What's on my calendar today?
Assistant: Here are your events on Tuesday:
• Team Standup at 09:00
• Project Review at 14:00
• Doctor Appointment at 16:30

You: Schedule a meeting with John tomorrow at 3 PM for 90 minutes
Assistant: The event 'Meeting with John' has been created.

You: Any events this Friday?
Assistant: Here are your events on Friday:
• Lunch with Sarah at 12:30
• Client Call at 15:00
```

## Integration with Other Features

The calendar functionality works seamlessly with:
- **Memory System**: All calendar interactions are remembered
- **LLM Interface**: Natural language understanding for complex requests
- **Intent Parser**: Automatic detection of calendar-related commands
- **Threading**: Non-blocking calendar operations in GUI
- **Error Handling**: Consistent error reporting across the application

The calendar integration makes the Enhanced Assistant a powerful personal scheduling tool while maintaining the natural conversational interface.
