# commands.py
import requests
from datetime import datetime, timedelta
from calendar_interface import GoogleCalendar
from outlook_interface import OutlookInterface
from unified_calendar import UnifiedCalendar
from spotify_interface import SpotifyInterface
from web_search import web_searcher
from notion_interface import NotionInterface
from config_manager import config
import dateparser
import time
import threading
import re
from datetime import timedelta

calendar = GoogleCalendar()
outlook = OutlookInterface()
unified_calendar = UnifiedCalendar()
spotify = SpotifyInterface()

def get_weather(location, target_time=None):
    try:
        # Get weather configuration
        weather_config = config.get_section('weather')
        
        # Step 1: Get latitude and longitude from location name
        geocoding_url = f"{weather_config['geocoding_api_url']}?name={location}&count=1"
        
        # Add timeout and better error handling for geocoding request
        try:
            timeout = weather_config.get('timeout_seconds', 10)
            geo_response = requests.get(geocoding_url, timeout=timeout).json()
        except requests.RequestException as e:
            return f"Sorry, I couldn't connect to the geocoding service. Please try again later."

        if "results" not in geo_response or not geo_response["results"]:
            return f"Sorry, I couldn't find the location '{location}'. Please check the spelling or try a different location."

        lat = geo_response["results"][0]["latitude"]
        lon = geo_response["results"][0]["longitude"]
        city_name = geo_response["results"][0]["name"]

        # Remember if target_time was originally None for response formatting
        is_current_time = target_time is None
        
        # Default to now if no target_time provided
        if target_time is None:
            target_time = datetime.now()

        # Format for URL
        date_str = target_time.strftime("%Y-%m-%d")

        # Step 2: Get hourly weather forecast
        weather_url = (
            f"{weather_config['weather_api_url']}?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,precipitation_probability,weather_code"
            f"&timezone=auto"
            f"&start_date={date_str}&end_date={date_str}"
        )
        
        # Add timeout and better error handling for weather request
        try:
            weather_response = requests.get(weather_url, timeout=timeout).json()
        except requests.RequestException as e:
            return f"Sorry, I couldn't connect to the weather service. Please try again later."
        
        # Check if the weather API returned an error
        if "error" in weather_response:
            return f"Sorry, the weather service returned an error: {weather_response.get('reason', 'Unknown error')}"
        
        if "hourly" not in weather_response:
            return f"Sorry, no weather data is available for {city_name} on that date."

        # Extract timestamps and find the closest hour to the target time
        timestamps = weather_response["hourly"]["time"]
        temperatures = weather_response["hourly"]["temperature_2m"]
        precipitation = weather_response["hourly"]["precipitation_probability"]

        # Find index of closest time - try multiple formats
        target_iso = target_time.strftime("%Y-%m-%dT%H:00")
        idx = None
        
        if target_iso in timestamps:
            idx = timestamps.index(target_iso)
        else:
            # Try to find the closest hour if exact match not found
            target_hour = target_time.hour
            for i, timestamp in enumerate(timestamps):
                if timestamp.endswith(f"T{target_hour:02d}:00"):
                    idx = i
                    break
        
        if idx is None:
            return f"Sorry, no weather data available for {target_time.strftime('%A %H:%M')} in {city_name}."

        temp = temperatures[idx]
        precip = precipitation[idx]
        
        # Handle None values that might come from the API
        if temp is None:
            temp = "N/A"
        if precip is None:
            precip = "N/A"

        # Fixed logic: use the flag we set earlier, not checking target_time again
        if is_current_time:
            return (
                f"The current temperature in {city_name} is {temp}°C. "
                f"The chance of precipitation is {precip}%."
            )
        else:
            return (
                f"The temperature in {city_name} on {target_time.strftime('%A at %H:%M')} will be {temp}°C. "
                f"The chance of precipitation is {precip}%."
            )

    except KeyError as e:
        return f"Sorry, the weather data format was unexpected. Missing key: {e}"
    except Exception as e:
        return f"Sorry, I had trouble getting the weather. Error: {str(e)}"

def get_time():
    now = datetime.now()
    return f"The current time is {now.strftime('%H:%M')}."

def add_calendar_event(summary, time, duration):
    start_time = datetime.fromisoformat(time)
    end_time = start_time + timedelta(minutes=duration)
    return calendar.create_event(summary, start_time, end_time)


def add_suggest_event(summary, suggested_time, event_duration):
    date = datetime.now().date() if "tomorrow" in summary.lower() else datetime.now().date() + timedelta(days=1)
    free_time = calendar.find_free_time_slot(event_duration, date)
    if free_time:
        start = datetime.combine(date, datetime.strptime(free_time, "%H:%M").time())
        end = start + timedelta(minutes=event_duration)
        return calendar.create_event(summary, start, end)
    else:
        return "No free time slot available that matches the duration."

def get_calendar_events_for_date(date_str):
    date_obj = dateparser.parse(date_str)
    if not date_obj:
        return "Sorry, I couldn't understand which date you're referring to."

    return calendar.get_events_for_date(date_obj)

def delete_calendar_event(event_summary, date_str=None):
    """Delete a calendar event by summary/title."""
    try:
        # Parse date if provided
        date_obj = None
        if date_str:
            date_obj = dateparser.parse(date_str)
            if not date_obj:
                return "Sorry, I couldn't understand the date you specified."

        # First, try to find events in local cache
        if date_obj:
            events = calendar.cache_sync.local_db.find_events_by_summary(event_summary, date_obj)
        else:
            events = calendar.cache_sync.local_db.find_events_by_summary(event_summary)

        # If no events found in cache, try Google Calendar directly
        if not events:
            print(f"[INFO] No events found in cache for '{event_summary}', checking Google Calendar...")
            events = calendar.find_event_by_summary(event_summary, date_obj)

        if not events:
            # If still no events found, try a broader search
            print(f"[INFO] Still no events found, trying broader search...")
            try:
                all_events = calendar.list_upcoming_events(50)  # Get more events
                # Filter events that contain the summary
                filtered_events = []
                for event in all_events:
                    if event_summary.lower() in event.get('summary', '').lower():
                        filtered_events.append(event)

                if filtered_events:
                    events = filtered_events
                else:
                    return f"I couldn't find any events matching '{event_summary}'. Please check the event name or try 'list upcoming events' to see what's scheduled."
            except Exception as e:
                print(f"[ERROR] Failed to get upcoming events: {e}")
                return f"I couldn't find any events matching '{event_summary}'. Please check the event name or try 'list upcoming events' to see what's scheduled."

        if len(events) == 1:
            # Only one matching event, delete it
            event = events[0]
            event_id = event.get('id') or event.get('google_event_id')
            if not event_id:
                return "Sorry, I couldn't find the event ID to delete this event."

            return calendar.delete_event(event_id)

        else:
            # Multiple matching events, ask for clarification
            response_parts = [f"I found {len(events)} events that might match '{event_summary}':"]

            for i, event in enumerate(events[:5], 1):  # Show first 5 matches
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%A at %H:%M')
                else:
                    start_time = f"All day on {start}"

                summary = event.get('summary', 'Untitled Event')
                response_parts.append(f"{i}. {summary} - {start_time}")

            response_parts.append("\nPlease be more specific about which event you want to delete, or include the date/time.")
            return "\n".join(response_parts)

    except Exception as e:
        print(f"[ERROR] Failed to delete calendar event: {e}")
        return f"Sorry, I encountered an error deleting the event: {str(e)}"

def update_calendar_event(event_summary, date_str=None, new_summary=None, new_time=None, new_date=None):
    """Update a calendar event by summary/title."""
    try:
        # Parse date if provided
        date_obj = None
        if date_str:
            date_obj = dateparser.parse(date_str)
            if not date_obj:
                return "Sorry, I couldn't understand the date you specified."

        # First, try to find events in local cache
        if date_obj:
            events = calendar.cache_sync.local_db.find_events_by_summary(event_summary, date_obj)
        else:
            events = calendar.cache_sync.local_db.find_events_by_summary(event_summary)

        # If no events found in cache, try Google Calendar directly
        if not events:
            print(f"[INFO] No events found in cache for '{event_summary}', checking Google Calendar...")
            events = calendar.find_event_by_summary(event_summary, date_obj)

        if not events:
            # If still no events found, try a broader search
            print(f"[INFO] Still no events found, trying broader search...")
            try:
                all_events = calendar.list_upcoming_events(50)  # Get more events
                # Filter events that contain the summary
                filtered_events = []
                for event in all_events:
                    if event_summary.lower() in event.get('summary', '').lower():
                        filtered_events.append(event)

                if filtered_events:
                    events = filtered_events
                else:
                    return f"I couldn't find any events matching '{event_summary}'. Please check the event name or try 'list upcoming events' to see what's scheduled."
            except Exception as e:
                print(f"[ERROR] Failed to get upcoming events: {e}")
                return f"I couldn't find any events matching '{event_summary}'. Please check the event name or try 'list upcoming events' to see what's scheduled."

        if len(events) == 1:
            # Only one matching event, update it
            event = events[0]
            event_id = event.get('id') or event.get('google_event_id')
            if not event_id:
                return "Sorry, I couldn't find the event ID to update this event."

            # Prepare update parameters
            update_params = {}

            if new_summary:
                update_params['summary'] = new_summary
            if new_time:
                # Parse new time and combine with existing or new date
                time_obj = dateparser.parse(new_time)
                if time_obj:
                    if new_date:
                        date_obj = dateparser.parse(new_date)
                        if date_obj:
                            new_datetime = datetime.combine(date_obj.date(), time_obj.time())
                        else:
                            return "Sorry, I couldn't understand the new date."
                    else:
                        # Use existing event date
                        existing_start = datetime.fromisoformat(event['start_time'])
                        new_datetime = datetime.combine(existing_start.date(), time_obj.time())

                    update_params['start_time'] = new_datetime.isoformat()
                    # Update end time by maintaining duration
                    existing_start = datetime.fromisoformat(event['start_time'])
                    existing_end = datetime.fromisoformat(event['end_time'])
                    duration = existing_end - existing_start
                    new_end = new_datetime + duration
                    update_params['end_time'] = new_end.isoformat()

            if not update_params:
                return "Please specify what you want to update (title, time, or date)."

            return calendar.update_event(event_id, **update_params)

        else:
            # Multiple matching events, ask for clarification
            response_parts = [f"I found {len(events)} events that might match '{event_summary}':"]

            for i, event in enumerate(events[:5], 1):  # Show first 5 matches
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%A at %H:%M')
                else:
                    start_time = f"All day on {start}"

                summary = event.get('summary', 'Untitled Event')
                response_parts.append(f"{i}. {summary} - {start_time}")

            response_parts.append("\nPlease be more specific about which event you want to update, or include the date/time.")
            return "\n".join(response_parts)

    except Exception as e:
        print(f"[ERROR] Failed to update calendar event: {e}")
        return f"Sorry, I encountered an error updating the event: {str(e)}"

def list_upcoming_calendar_events(max_results=10):
    """List upcoming calendar events."""
    try:
        return calendar.list_upcoming_events(max_results)
    except Exception as e:
        print(f"[ERROR] Failed to list upcoming events: {e}")
        return f"Sorry, I encountered an error retrieving upcoming events: {str(e)}"

def move_calendar_event(event_summary, new_time, date_str=None):
    """Move a calendar event to a new time."""
    return update_calendar_event(event_summary, date_str, new_time=new_time)

def reschedule_calendar_event(event_summary, new_date, new_time=None, date_str=None):
    """Reschedule a calendar event to a new date and optionally time."""
    return update_calendar_event(event_summary, date_str, new_time=new_time, new_date=new_date)

def find_calendar_event(event_summary, date_str=None):
    """Find and display information about a specific calendar event."""
    try:
        # Parse date if provided
        date_obj = None
        if date_str:
            date_obj = dateparser.parse(date_str)
            if not date_obj:
                return "Sorry, I couldn't understand the date you specified."

        # Find events matching the summary
        if date_obj:
            events = calendar.cache_sync.local_db.find_events_by_summary(event_summary, date_obj)
        else:
            events = calendar.find_event_by_summary(event_summary, date_obj)

        if not events:
            return f"I couldn't find any events matching '{event_summary}'."

        if len(events) == 1:
            # Only one matching event, show details
            event = events[0]
            start = event['start_time']
            end = event['end_time']

            if 'T' in start:
                start_time = datetime.fromisoformat(start).strftime('%A, %B %d at %H:%M')
                end_time = datetime.fromisoformat(end).strftime('%H:%M')
                time_info = f"from {start_time} to {end_time}"
            else:
                time_info = f"all day on {start}"

            summary = event.get('summary', 'Untitled Event')
            description = event.get('description', 'No description')
            location = event.get('location', 'No location')

            response = f"Found event: '{summary}'\n"
            response += f"Time: {time_info}\n"
            if description != 'No description':
                response += f"Description: {description}\n"
            if location != 'No location':
                response += f"Location: {location}\n"

            return response

        else:
            # Multiple matching events, show list
            response_parts = [f"I found {len(events)} events matching '{event_summary}':"]

            for i, event in enumerate(events[:5], 1):  # Show first 5 matches
                start = event['start_time']
                if 'T' in start:
                    start_time = datetime.fromisoformat(start).strftime('%A at %H:%M')
                else:
                    start_time = f"All day on {start}"

                summary = event.get('summary', 'Untitled Event')
                response_parts.append(f"{i}. {summary} - {start_time}")

            response_parts.append("\nPlease be more specific about which event you're looking for.")
            return "\n".join(response_parts)

    except Exception as e:
        print(f"[ERROR] Failed to find calendar event: {e}")
        return f"Sorry, I encountered an error finding the event: {str(e)}"

def show_calendar_events(date_str=None):
    """Show calendar events for a specific date or today."""
    try:
        if date_str:
            date_obj = dateparser.parse(date_str)
            if not date_obj:
                return "Sorry, I couldn't understand the date you specified."
        else:
            date_obj = datetime.now()

        return calendar.get_events_for_date(date_obj)

    except Exception as e:
        print(f"[ERROR] Failed to show calendar events: {e}")
        return f"Sorry, I encountered an error retrieving calendar events: {str(e)}"

def cancel_calendar_event(event_summary, date_str=None):
    """Cancel a calendar event (alias for delete)."""
    return delete_calendar_event(event_summary, date_str)

def modify_calendar_event(event_summary, date_str=None, **kwargs):
    """Modify a calendar event with flexible parameters."""
    return update_calendar_event(event_summary, date_str, **kwargs)

def start_timer(duration_minutes):
    """Start a timer that runs in the background"""
    def countdown():
        try:
            print(f"Timer started for {duration_minutes} minutes.")
            time.sleep(duration_minutes * 60)
            print("Timer complete!")
        except Exception as e:
            print(f"Timer error: {e}")
    
    # Use daemon thread so it doesn't prevent program exit
    thread = threading.Thread(target=countdown, daemon=True)
    thread.start()
    return f"Starting a {duration_minutes}-minute timer."

def tell_joke():
    """Fetch and return a random joke from an online API"""
    try:
        # Get jokes configuration
        jokes_config = config.get_section('jokes')
        
        # Use the configured joke API
        response = requests.get(
            jokes_config['api_url'], 
            timeout=jokes_config.get('timeout_seconds', 5)
        )
        
        if response.status_code == 200:
            joke_data = response.json()
            return f"{joke_data['setup']} ... {joke_data['punchline']}"
        else:
            # Fallback to configured jokes if API fails
            fallback_jokes = jokes_config.get('fallback_jokes', [])
            if fallback_jokes:
                import random
                return random.choice(fallback_jokes)
            return "Why don't scientists trust atoms? Because they make up everything!"
            
    except requests.RequestException:
        # Fallback joke if network request fails
        fallback_jokes = config.get('jokes.fallback_jokes', [])
        if fallback_jokes:
            import random
            return random.choice(fallback_jokes)
        return "Why did the programmer quit his job? Because he didn't get arrays!"
    except Exception:
        # Another fallback
        fallback_jokes = config.get('jokes.fallback_jokes', [])
        if fallback_jokes:
            import random
            return random.choice(fallback_jokes)
        return "Why do programmers prefer dark mode? Because light attracts bugs!"

# Spotify Commands
def play_music(query):
    """Play music using Spotify"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    return spotify.search_and_play(query, play_immediately=True)

def queue_music(query):
    """Add music to Spotify queue"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    return spotify.search_and_play(query, play_immediately=False)

def pause_music():
    """Pause Spotify playback"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    success = spotify.pause_playback()
    if success:
        return "Music paused."
    else:
        return "Sorry, I couldn't pause the music. Make sure Spotify is playing on a device."

def resume_music():
    """Resume Spotify playback"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    success = spotify.resume_playback()
    if success:
        return "Music resumed."
    else:
        return "Sorry, I couldn't resume the music. Make sure Spotify is available on a device."

def next_song():
    """Skip to next song on Spotify"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    success = spotify.next_track()
    if success:
        return "Skipped to next song."
    else:
        return "Sorry, I couldn't skip to the next song."

def previous_song():
    """Go to previous song on Spotify"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    success = spotify.previous_track()
    if success:
        return "Playing previous song."
    else:
        return "Sorry, I couldn't go to the previous song."

def get_current_song():
    """Get information about currently playing song"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    current = spotify.get_current_track()
    if current and current.get('is_playing'):
        track = current['item']
        if track:
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            return f"Currently playing '{track_name}' by {artist_name}."
    
    return "Nothing is currently playing on Spotify."

def set_volume(volume_text):
    """Set Spotify volume"""
    if not spotify.is_authenticated:
        return "Sorry, Spotify is not connected. Please check your authentication setup."
    
    # Extract volume percentage from text
    volume_match = re.search(r'(\d+)', volume_text)
    if not volume_match:
        return "Sorry, I couldn't understand the volume level. Please specify a number between 0 and 100."
    
    volume = int(volume_match.group(1))
    if volume < 0 or volume > 100:
        return "Please specify a volume between 0 and 100."
    
    success = spotify.set_volume(volume)
    if success:
        return f"Volume set to {volume}%."
    else:
        return "Sorry, I couldn't change the volume."

# Web Search Commands
def search_web(query):
    """Search the web and return results with context"""
    try:
        print(f"[INFO] Performing web search for: {query}")
        
        # Perform search and scraping
        search_data = web_searcher.search_and_scrape(query)
        
        if not search_data['results']:
            return f"I couldn't find any web results for '{query}'. Please try a different search term."
        
        # Format results for response
        response_parts = [f"I found {len(search_data['results'])} results for '{query}':"]
        
        # Add top results summary
        for i, result in enumerate(search_data['results'][:3], 1):
            response_parts.append(f"\n{i}. {result['title']}")
            if result['snippet']:
                response_parts.append(f"   {result['snippet']}")
        
        # Add scraped content summary if available
        if search_data['scraped_content']:
            response_parts.append(f"\nI was able to gather detailed information from {len(search_data['scraped_content'])} sources.")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        print(f"[ERROR] Web search failed: {e}")
        return f"Sorry, I encountered an error while searching for '{query}'. Please try again later."

def search_web_with_context(query, llm_interface):
    """Search the web and use LLM to provide informed response"""
    try:
        print(f"[INFO] Performing contextual web search for: {query}")
        
        # Perform search and scraping
        search_data = web_searcher.search_and_scrape(query)
        
        if not search_data['results']:
            return f"I couldn't find any web results for '{query}'. Please try a different search term."
        
        # Try LLM enhancement, but fall back to basic search if it fails
        try:
            # Format search context for LLM
            search_context = web_searcher.format_search_context(search_data)
            
            # Limit the context length to avoid overwhelming the LLM
            max_context_length = 2000
            if len(search_context) > max_context_length:
                search_context = search_context[:max_context_length] + "\n\n[Context truncated due to length]"
            
            # Create prompt for LLM with web context
            llm_prompt = f"""You are a helpful assistant that can search the web for information. A user has asked you to look up information about: "{query}"

I have gathered the following information from web search results:

{search_context}

Based on this information, please provide a comprehensive and helpful response to the user's query. Include relevant details from the search results and cite sources when appropriate. If the search results don't fully answer the question, mention what additional information might be needed.

User query: {query}

Response:"""
            
            # Get LLM response with web context
            response = llm_interface._call_llm(llm_prompt)
            
            if response and len(response.strip()) > 0 and "I'm sorry" not in response:
                return response
            else:
                print(f"[WARN] LLM response was empty or error, falling back to basic search")
                raise Exception("LLM returned empty or error response")
                
        except Exception as llm_error:
            print(f"[WARN] LLM enhancement failed ({llm_error}), using basic search results")
            # Fall back to basic search formatting
            return search_web(query)
        
    except Exception as e:
        print(f"[ERROR] Contextual web search failed: {e}")
        return f"Sorry, I encountered an error while searching for information about '{query}'. Please try again later."

# Memory Management Commands
def get_memory_stats():
    """Get memory system statistics"""
    try:
        # Get the global memory instance from main
        # This is a simplified approach - in production you'd pass the memory instance
        from enhanced_memory import EnhancedMemory
        temp_memory = EnhancedMemory()
        stats = temp_memory.get_memory_stats()
        temp_memory.close()
        
        response_parts = ["Here are your memory statistics:"]
        response_parts.append(f"\n• Short-term memory: {stats['short_term_memory_count']} items")
        response_parts.append(f"• Long-term memory: {stats['long_term_memory_count']} items")
        response_parts.append(f"• Total interactions: {stats['total_interactions']}")
        response_parts.append(f"• Current session length: {stats['conversation_length']} interactions")
        response_parts.append(f"• Current topic: {stats['current_topic']}")
        
        if stats['categories']:
            response_parts.append(f"\nMemory categories:")
            for category, count in list(stats['categories'].items())[:5]:
                response_parts.append(f"  - {category}: {count} items")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        print(f"[ERROR] Failed to get memory stats: {e}")
        return "Sorry, I couldn't retrieve memory statistics at this time."

def save_important_info(title, content, category="general"):
    """Save important information to long-term memory"""
    try:
        from enhanced_memory import EnhancedMemory
        temp_memory = EnhancedMemory()
        
        # Save with high importance to ensure it stays in long-term memory
        ltm_id = temp_memory.save_long_term_memory(
            title=title,
            content=content,
            category=category,
            importance=8,  # High importance
            tags=["user_saved", "important"]
        )
        
        temp_memory.close()
        
        return f"I've saved '{title}' to your long-term memory in the {category} category."
        
    except Exception as e:
        print(f"[ERROR] Failed to save important info: {e}")
        return "Sorry, I couldn't save that information to memory."

def search_my_memory(query):
    """Search through stored memories"""
    try:
        from enhanced_memory import EnhancedMemory
        temp_memory = EnhancedMemory()
        
        # Search both long-term memory and conversations
        long_term_results = temp_memory.search_long_term_memory(query, limit=5)
        conversation_results = temp_memory.search_conversations(query, limit=5)
        
        temp_memory.close()
        
        response_parts = [f"I found the following memories related to '{query}':"]
        
        if long_term_results:
            response_parts.append("\n=== Long-term Memories ===")
            for result in long_term_results:
                response_parts.append(f"\n• {result['title']} ({result['category']})")
                # Truncate content for summary
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                response_parts.append(f"  {content_preview}")
        
        if conversation_results:
            response_parts.append("\n=== Past Conversations ===")
            for result in conversation_results[:3]:  # Limit to 3 for brevity
                response_parts.append(f"\n• {result['context_type']} conversation")
                user_preview = result['user_input'][:50] + "..." if len(result['user_input']) > 50 else result['user_input']
                response_parts.append(f"  You asked: {user_preview}")
        
        if not long_term_results and not conversation_results:
            return f"I couldn't find any memories related to '{query}'. Try different keywords or phrases."
        
        return "\n".join(response_parts)
        
    except Exception as e:
        print(f"[ERROR] Failed to search memory: {e}")
        return "Sorry, I couldn't search your memories at this time."

# Notion Commands
notion = NotionInterface()

def create_notion_todo(title, description="", due_date=None, priority="Medium"):
    """Create a todo item in Notion"""
    if not notion.is_authenticated:
        return "Sorry, Notion is not connected. Please set up your NOTION_API_TOKEN environment variable and configure your database."
    
    try:
        page_id = notion.create_todo_item(title, description, due_date, priority)
        if page_id:
            return f"Created todo item '{title}' in Notion."
        else:
            return "Sorry, I couldn't create the todo item. Please check your Notion configuration."
    except Exception as e:
        print(f"[ERROR] Failed to create Notion todo: {e}")
        return "Sorry, I encountered an error creating the todo item."

def create_notion_note(title, content, tags=None):
    """Create a note in Notion"""
    if not notion.is_authenticated:
        return "Sorry, Notion is not connected. Please set up your NOTION_API_TOKEN environment variable and configure your database."
    
    try:
        page_id = notion.create_note(title, content, tags)
        if page_id:
            tag_text = f" with tags: {', '.join(tags)}" if tags else ""
            return f"Created note '{title}' in Notion{tag_text}."
        else:
            return "Sorry, I couldn't create the note. Please check your Notion configuration."
    except Exception as e:
        print(f"[ERROR] Failed to create Notion note: {e}")
        return "Sorry, I encountered an error creating the note."

def search_notion_pages(query):
    """Search for pages in Notion workspace"""
    if not notion.is_authenticated:
        return "Sorry, Notion is not connected. Please set up your NOTION_API_TOKEN environment variable."
    
    try:
        pages = notion.search_pages(query, page_size=5)
        if not pages:
            return f"I couldn't find any pages matching '{query}' in your Notion workspace."
        
        response_parts = [f"I found {len(pages)} pages matching '{query}':"]
        
        for page in pages:
            formatted_info = notion.format_page_info(page)
            response_parts.append(formatted_info)
        
        return "\n".join(response_parts)
        
    except Exception as e:
        print(f"[ERROR] Failed to search Notion pages: {e}")
        return "Sorry, I encountered an error searching your Notion workspace."

def search_notion_todos(query="", status=None):
    """Search for todo items in Notion database"""
    if not notion.is_authenticated:
        return "Sorry, Notion is not connected. Please set up your NOTION_API_TOKEN environment variable and configure your database."
    
    try:
        todos = notion.search_todos(query, status)
        if not todos:
            filter_text = f" with status '{status}'" if status else ""
            query_text = f" matching '{query}'" if query else ""
            return f"I couldn't find any todo items{query_text}{filter_text} in your Notion database."
        
        response_parts = [f"I found {len(todos)} todo items:"]
        
        for todo in todos:
            formatted_info = notion.format_database_entry(todo)
            response_parts.append(formatted_info)
        
        return "\n".join(response_parts)
        
    except Exception as e:
        print(f"[ERROR] Failed to search Notion todos: {e}")
        return "Sorry, I encountered an error searching your todo items."

def append_to_notion_page(query, content, block_type="paragraph"):
    """Append content to an existing Notion page"""
    if not notion.is_authenticated:
        return "Sorry, Notion is not connected. Please set up your NOTION_API_TOKEN environment variable."
    
    try:
        # First search for the page
        pages = notion.search_pages(query, page_size=1)
        if not pages:
            return f"I couldn't find a page matching '{query}' in your Notion workspace."
        
        page = pages[0]
        page_id = page['id']
        
        # Get page title for confirmation
        page_title = "the page"
        if "properties" in page:
            for prop_name in ["Name", "Title", "title"]:
                if prop_name in page["properties"]:
                    prop = page["properties"][prop_name]
                    if prop["type"] == "title" and prop["title"]:
                        page_title = f"'{prop['title'][0]['text']['content']}'"
                        break
        
        success = notion.append_to_page(page_id, content, block_type)
        if success:
            return f"Added content to {page_title} in Notion."
        else:
            return f"Sorry, I couldn't add content to {page_title}."
            
    except Exception as e:
        print(f"[ERROR] Failed to append to Notion page: {e}")
        return "Sorry, I encountered an error adding content to the page."

def get_notion_page_content(query):
    """Get and summarize content from a Notion page"""
    if not notion.is_authenticated:
        return "Sorry, Notion is not connected. Please set up your NOTION_API_TOKEN environment variable."
    
    try:
        # First search for the page
        pages = notion.search_pages(query, page_size=1)
        if not pages:
            return f"I couldn't find a page matching '{query}' in your Notion workspace."
        
        page = pages[0]
        page_id = page['id']
        
        # Get page title
        page_title = "Untitled"
        if "properties" in page:
            for prop_name in ["Name", "Title", "title"]:
                if prop_name in page["properties"]:
                    prop = page["properties"][prop_name]
                    if prop["type"] == "title" and prop["title"]:
                        page_title = prop['title'][0]['text']['content']
                        break
        
        # Get page content
        content_blocks = notion.get_page_content(page_id)
        if not content_blocks:
            return f"The page '{page_title}' appears to be empty or I couldn't access its content."
        
        # Extract text content from blocks
        text_content = []
        for block in content_blocks:
            if block.get('type') == 'paragraph':
                paragraph = block.get('paragraph', {})
                rich_text = paragraph.get('rich_text', [])
                for text_obj in rich_text:
                    if text_obj.get('type') == 'text':
                        text_content.append(text_obj['text']['content'])
            elif block.get('type') in ['heading_1', 'heading_2', 'heading_3']:
                heading_type = block.get('type')
                heading = block.get(heading_type, {})
                rich_text = heading.get('rich_text', [])
                for text_obj in rich_text:
                    if text_obj.get('type') == 'text':
                        text_content.append(f"\n## {text_obj['text']['content']}")
        
        if not text_content:
            return f"The page '{page_title}' doesn't contain any readable text content."
        
        content_preview = " ".join(text_content)[:500]
        if len(" ".join(text_content)) > 500:
            content_preview += "..."
        
        return f"Content from '{page_title}':\n\n{content_preview}"
        
    except Exception as e:
        print(f"[ERROR] Failed to get Notion page content: {e}")
        return "Sorry, I encountered an error retrieving the page content."

# Unified Calendar Commands
def create_unified_calendar_event(summary, time, duration, description="", location="", provider=None):
    """Create an event using the unified calendar system"""
    try:
        start_time = datetime.fromisoformat(time)
        end_time = start_time + timedelta(minutes=duration)
        
        result = unified_calendar.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            provider=provider
        )
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to create unified calendar event: {e}")
        return f"Sorry, I encountered an error creating the calendar event: {str(e)}"

def get_unified_calendar_events(date_str, provider=None):
    """Get events for a date from unified calendar system"""
    try:
        date_obj = dateparser.parse(date_str)
        if not date_obj:
            return "Sorry, I couldn't understand which date you're referring to."
        
        return unified_calendar.get_events_for_date(date_obj, provider)
        
    except Exception as e:
        print(f"[ERROR] Failed to get unified calendar events: {e}")
        return f"Sorry, I encountered an error retrieving calendar events: {str(e)}"

def find_unified_free_time(duration_minutes, date_str, provider=None):
    """Find free time slot using unified calendar system"""
    try:
        date_obj = dateparser.parse(date_str) or datetime.now()
        
        free_time = unified_calendar.find_free_time_slot(
            duration_minutes=duration_minutes,
            date_obj=date_obj,
            provider=provider
        )
        
        if free_time:
            return f"I found a free {duration_minutes}-minute slot at {free_time}"
        else:
            return f"Sorry, I couldn't find a free {duration_minutes}-minute slot on {date_obj.strftime('%A, %B %d')}"
            
    except Exception as e:
        print(f"[ERROR] Failed to find free time: {e}")
        return f"Sorry, I encountered an error finding free time: {str(e)}"

def get_calendar_status():
    """Get status of all calendar providers"""
    try:
        return unified_calendar.get_provider_status()
    except Exception as e:
        print(f"[ERROR] Failed to get calendar status: {e}")
        return "Sorry, I encountered an error getting calendar status."

def authenticate_calendars():
    """Attempt to authenticate missing calendar providers"""
    try:
        return unified_calendar.authenticate_missing_providers()
    except Exception as e:
        print(f"[ERROR] Failed to authenticate calendars: {e}")
        return "Sorry, I encountered an error during calendar authentication."

def get_calendar_summary():
    """Get a summary of calendar connections"""
    try:
        return unified_calendar.get_calendar_summary()
    except Exception as e:
        print(f"[ERROR] Failed to get calendar summary: {e}")
        return "Sorry, I encountered an error getting calendar summary."

# Cache Management Commands
def refresh_calendar_cache():
    """Force refresh the calendar cache with latest Google Calendar data"""
    try:
        result = calendar.refresh_cache()
        if result.get('success'):
            return f"Calendar cache refreshed successfully. {result.get('events_synced', 0)} events synchronized."
        else:
            return f"Failed to refresh calendar cache: {result.get('error', 'Unknown error')}"
    except Exception as e:
        print(f"[ERROR] Failed to refresh calendar cache: {e}")
        return "Sorry, I encountered an error refreshing the calendar cache."

def get_calendar_cache_status():
    """Get the current status of the calendar cache and synchronization"""
    try:
        status = calendar.get_cache_status()
        if 'error' in status:
            return f"Error getting cache status: {status['error']}"

        response_parts = ["Calendar Cache Status:"]
        response_parts.append(f"• Sync enabled: {status.get('sync_enabled', 'Unknown')}")
        response_parts.append(f"• Last full sync: {status.get('last_full_sync', 'Never')}")
        response_parts.append(f"• Last incremental sync: {status.get('last_incremental_sync', 'Never')}")

        # Add database info
        db_info = status.get('database_info', {})
        response_parts.append(f"• Cached events: {db_info.get('events_count', 0)}")
        response_parts.append(f"• Database size: {db_info.get('database_size_bytes', 0)} bytes")

        return "\n".join(response_parts)
    except Exception as e:
        print(f"[ERROR] Failed to get cache status: {e}")
        return "Sorry, I encountered an error getting the cache status."

def cleanup_calendar_cache(days_to_keep: int = 30):
    """Clean up old events from the calendar cache"""
    try:
        deleted_count = calendar.cleanup_cache(days_to_keep)
        return f"Cleaned up calendar cache. Removed {deleted_count} old events."
    except Exception as e:
        print(f"[ERROR] Failed to cleanup calendar cache: {e}")
        return "Sorry, I encountered an error cleaning up the calendar cache."

def export_calendar_data(format: str = 'json'):
    """Export calendar data for backup or analysis"""
    try:
        data = calendar.export_cache(format)
        return f"Calendar data exported in {format.upper()} format ({len(data)} characters)."
    except Exception as e:
        print(f"[ERROR] Failed to export calendar data: {e}")
        return "Sorry, I encountered an error exporting calendar data."

def sync_calendar_now():
    """Force an immediate synchronization with Google Calendar"""
    try:
        result = calendar.refresh_cache()
        if result.get('success'):
            return f"Calendar synchronized successfully. {result.get('events_synced', 0)} events updated."
        else:
            return f"Calendar synchronization failed: {result.get('error', 'Unknown error')}"
    except Exception as e:
        print(f"[ERROR] Failed to sync calendar: {e}")
        return "Sorry, I encountered an error synchronizing the calendar."

# Outlook-specific commands
def create_outlook_event(summary, time, duration, description="", location=""):
    """Create an event specifically in Outlook"""
    try:
        if not outlook.is_authenticated:
            return "Sorry, Outlook is not connected. Please authenticate first."
        
        start_time = datetime.fromisoformat(time)
        end_time = start_time + timedelta(minutes=duration)
        
        return outlook.create_event(summary, start_time, end_time, description, location)
        
    except Exception as e:
        print(f"[ERROR] Failed to create Outlook event: {e}")
        return f"Sorry, I encountered an error creating the Outlook event: {str(e)}"

def get_outlook_events(date_str):
    """Get events for a date from Outlook"""
    try:
        if not outlook.is_authenticated:
            return "Sorry, Outlook is not connected. Please authenticate first."
        
        date_obj = dateparser.parse(date_str)
        if not date_obj:
            return "Sorry, I couldn't understand which date you're referring to."
        
        return outlook.get_events_for_date(date_obj)
        
    except Exception as e:
        print(f"[ERROR] Failed to get Outlook events: {e}")
        return f"Sorry, I encountered an error retrieving Outlook events: {str(e)}"

def authenticate_outlook():
    """Authenticate with Outlook"""
    try:
        success = outlook.authenticate()
        if success:
            return "Outlook authentication successful! You can now manage your Outlook calendar."
        else:
            return "Outlook authentication failed. Please check your setup and try again."
    except Exception as e:
        print(f"[ERROR] Failed to authenticate Outlook: {e}")
        return f"Sorry, I encountered an error during Outlook authentication: {str(e)}"
