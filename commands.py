# commands.py
import requests
from datetime import datetime, timedelta
from calendar_interface import GoogleCalendar
from spotify_interface import SpotifyInterface
from web_search import web_searcher
from config_manager import config
import dateparser
import time
import threading
import re
from datetime import timedelta

calendar = GoogleCalendar()
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
        
        # Format search context for LLM
        search_context = web_searcher.format_search_context(search_data)
        
        # Create prompt for LLM with web context
        llm_prompt = f"""You are a helpful assistant that can search the web for information. A user has asked you to look up information about: "{query}"

I have gathered the following information from web search results:

{search_context}

Based on this information, please provide a comprehensive and helpful response to the user's query. Include relevant details from the search results and cite sources when appropriate. If the search results don't fully answer the question, mention what additional information might be needed.

User query: {query}

Response:"""
        
        # Get LLM response with web context
        response = llm_interface._call_llm(llm_prompt)
        
        return response
        
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
