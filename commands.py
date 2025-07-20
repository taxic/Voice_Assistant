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
        geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
        geo_response = requests.get(geocoding_url).json()

        if "results" not in geo_response or not geo_response["results"]:
            return f"Sorry, I couldn't find the location '{location}'."

        lat = geo_response["results"][0]["latitude"]
        lon = geo_response["results"][0]["longitude"]
        city_name = geo_response["results"][0]["name"]

        # Default to now if no target_time provided
        if not target_time:
            target_time = datetime.now()

        # Format for URL
        date_str = target_time.strftime("%Y-%m-%d")

        # Step 2: Get hourly weather forecast
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,precipitation_probability"
            f"&timezone=auto"
            f"&start_date={date_str}&end_date={date_str}"
        )
        weather_response = requests.get(weather_url).json()

        # Extract timestamps and find the closest hour to the target time
        timestamps = weather_response["hourly"]["time"]
        temperatures = weather_response["hourly"]["temperature_2m"]
        precipitation = weather_response["hourly"]["precipitation_probability"]

        # Find index of closest time
        target_iso = target_time.strftime("%Y-%m-%dT%H:00")
        if target_iso in timestamps:
            idx = timestamps.index(target_iso)
        else:
            return f"Sorry, no weather data available for {target_iso}."

        temp = temperatures[idx]
        precip = precipitation[idx]

        if target_time is None:
            return (
                f"The temperature in {city_name} is {temp}°C. "
                f"The chance of precipitation is {precip}%."
            )
        else:
            return (
                f"The temperature in {city_name} on {target_time.strftime('%A %H:%M')} is {temp}°C. "
                f"The chance of precipitation is {precip}%."
            )

    except Exception as e:
        return f"Sorry, I had trouble getting the weather. Error: {e}"

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
    # Logic to start the timer
    def countdown():
        print(f"Timer started for {duration_minutes} minutes.")
        time.sleep(duration_minutes * 60)
        print("⏰ Timer complete!")
    thread = threading.Thread(target=countdown)
    thread.start()
    return f"Starting a {duration_minutes}-minute timer."