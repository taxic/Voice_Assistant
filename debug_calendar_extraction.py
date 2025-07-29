#!/usr/bin/env python3
"""
Debug script to test calendar event extraction
"""

from llm_interface import LLMInterface
from datetime import datetime
import json

def test_calendar_extraction():
    """Test the calendar event extraction directly"""
    print("Testing calendar event extraction...")
    
    llm = LLMInterface()
    
    test_messages = [
        "Schedule a meeting tomorrow at 2 PM",
        "Add doctor appointment next Friday at 10 AM", 
        "Book lunch with John on Friday at 1:30 PM",
        "Create team standup meeting today at 9 AM for 30 minutes"
    ]
    
    for message in test_messages:
        print(f"\n--- Testing: '{message}' ---")
        
        # This is the exact prompt used in the GUI - updated version
        from datetime import timedelta
        today_date = datetime.now().strftime("%Y-%m-%d")
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        extraction_prompt = f"""Extract event details from this request. Today is {today_date}. Respond with a JSON object containing:
- "title": The event title/summary
- "date": The date in YYYY-MM-DD format (tomorrow would be {tomorrow_date})
- "time": The time in HH:MM 24-hour format (convert from AM/PM if needed)
- "duration": Duration in minutes (if not specified, use 60)

User request: "{message}"

JSON:"""
        
        print("Prompt sent to LLM:")
        print(extraction_prompt)
        print("\nLLM response:")
        
        response = llm._call_llm(extraction_prompt).strip()
        print(f"Raw response: '{response}'")
        
        # Try to parse JSON
        try:
            event_details = json.loads(response)
            print(f"✓ Successfully parsed JSON: {event_details}")
        except json.JSONDecodeError as e:
            print(f"✗ JSON parsing failed: {e}")
            
            # Try to extract JSON from response if embedded
            import re
            json_pattern = r'\{[^}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                print(f"Found potential JSON matches: {matches}")
                for match in matches:
                    try:
                        event_details = json.loads(match)
                        print(f"✓ Successfully parsed extracted JSON: {event_details}")
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    print("✗ None of the extracted JSON matches could be parsed")
            else:
                print("✗ No JSON pattern found in response")

if __name__ == "__main__":
    test_calendar_extraction()
