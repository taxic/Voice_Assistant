# commands.py
import requests
from datetime import datetime, timedelta
from calendar_interface import GoogleCalendar
import dateparser
import time
import threading

calendar = GoogleCalendar()

def get_weather(location, target_time=None):
    try:
        # Step 1: Get latitude and longitude from location name
        geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}\u0026count=1"
        
        # Add timeout and better error handling for geocoding request
        try:
            geo_response = requests.get(geocoding_url, timeout=10).json()
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
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}\u0026longitude={lon}"
            f"\u0026hourly=temperature_2m,precipitation_probability,weather_code"
            f"\u0026timezone=auto"
            f"\u0026start_date={date_str}\u0026end_date={date_str}"
        )
        
        # Add timeout and better error handling for weather request
        try:
            weather_response = requests.get(weather_url, timeout=10).json()
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
        # Use a simple joke API
        joke_url = "https://official-joke-api.appspot.com/random_joke"
        response = requests.get(joke_url, timeout=5)
        
        if response.status_code == 200:
            joke_data = response.json()
            return f"{joke_data['setup']} ... {joke_data['punchline']}"
        else:
            # Fallback to a simple built-in joke if API fails
            return "Why don't scientists trust atoms? Because they make up everything!"
            
    except requests.RequestException:
        # Fallback joke if network request fails
        return "Why did the programmer quit his job? Because he didn't get arrays!"
    except Exception:
        # Another fallback
        return "Why do programmers prefer dark mode? Because light attracts bugs!"
