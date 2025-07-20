# command_parser.py

import json
import re

def parse_calendar_add(llm, command):
    prompt = f"""
You are a helpful assistant that extracts calendar event information.
Given the following input, return a JSON with:
- "summary" (short description)
- "start_time" in ISO format (e.g. 2025-07-02T12:00:00)
- "duration_minutes" (length of event)

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
