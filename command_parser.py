# command_parser.py

import json
import re

def parse_calendar_add(llm, command):
    # Get smart default times and duration based on event type
    from smart_event_times import smart_times
    from datetime import datetime
    
    event_suggestions = smart_times.get_event_suggestions(command)
    smart_time = event_suggestions['time']
    smart_duration = event_suggestions['duration']
    detected_type = event_suggestions['type']
    
    print(f"[DEBUG] Smart suggestions for '{command}': type={detected_type}, time={smart_time}, duration={smart_duration}")
    
    # Get today's date for context
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
You are a helpful assistant that extracts calendar event information.
Given the following input, return a JSON with:
- "summary" (short description)
- "start_time" in ISO format (e.g. 2025-07-02T12:00:00) - use "default" if no time specified
- "duration_minutes" (length of event in minutes)

For context: Today is {today_date}.
If no specific time is mentioned, set start_time to "default".
If no duration is mentioned, use {smart_duration} minutes which is typical for {detected_type} events.

Input: "{command}"
Respond ONLY with JSON.
"""

    # Use the LLM without memory context for structured parsing
    response = llm.get_response(prompt, use_memory_context=False)

    try:
        event_data = json.loads(response)
        return event_data
    except json.JSONDecodeError:
        # Try to extract JSON from the response if it's embedded in other text
        json_pattern = r'\{[^}]*\}'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                event_data = json.loads(match)
                return event_data
            except json.JSONDecodeError:
                continue
        
        return None
