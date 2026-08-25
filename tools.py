# tools.py
"""Tool (function-calling) registry for the LLM agent loop.

Wraps the assistant's existing command functions as Ollama-compatible tool
schemas plus a name -> callable dispatch table, so the LLM itself decides
which of these to call and with what arguments - replacing the ~30-branch
hardcoded if/elif intent dispatch that used to live in main.py.

Every tool here calls back into integrations that already existed in this
project (Ollama, Google Calendar, the local SQLite memory store, DuckDuckGo,
Spotify, Notion, local IoT devices). Nothing here introduces a paid or
cloud-only dependency - the point of this file is to make the *existing*
free, self-hosted capabilities usable by the model as tools, not to add new
external services.
"""

from datetime import datetime

import dateparser

import commands
from config_manager import config
from smart_event_times import smart_times
from iot_commands import (
    turn_on_light, turn_off_light, set_light_brightness, set_light_color,
    turn_on_all_lights, turn_off_all_lights, turn_on_switch, turn_off_switch,
    set_temperature, get_sensor_reading, get_device_status, list_all_devices,
)

END_CONVERSATION = object()  # sentinel result main.py checks for to exit the loop


def _resolve_event_time(summary, start_time, date, duration_minutes):
    """Turn the model's (possibly missing) time/date args into a concrete
    datetime. If no time is given, look for a free slot instead of failing
    the request - mirrors the old 'find a free slot for me' flow but without
    needing a separate clarifying voice round-trip."""
    if start_time:
        parsed = dateparser.parse(start_time, settings={"PREFER_DATES_FROM": "future"})
        if parsed:
            return parsed, False

    date_obj = datetime.now().date()
    if date:
        parsed_date = dateparser.parse(date)
        if parsed_date:
            date_obj = parsed_date.date()

    free_time = commands.calendar.find_free_time_slot(duration_minutes, date_obj)
    if not free_time:
        return None, False
    hour, minute = map(int, free_time.split(":"))
    return datetime.combine(date_obj, datetime.min.time()).replace(hour=hour, minute=minute), True


def tool_add_calendar_event(summary, start_time=None, duration_minutes=None, date=None):
    duration = duration_minutes or smart_times.get_smart_duration(summary)
    resolved, auto_scheduled = _resolve_event_time(summary, start_time, date, duration)
    if not resolved:
        return "I couldn't find a free slot or understand the time you meant - please give me a specific time."
    result = commands.add_calendar_event(summary, resolved.isoformat(), duration)
    if auto_scheduled:
        result += f" (No time was specified, so I found a free slot at {resolved.strftime('%H:%M')}.)"
    return result


def tool_get_weather(location=None, when=None):
    location = location or config.get('weather.default_location', 'Guildford')
    target_time = dateparser.parse(when, settings={"PREFER_DATES_FROM": "future"}) if when else None
    return commands.get_weather(location, target_time)


def tool_set_volume(volume_percent):
    return commands.set_volume(str(volume_percent))


def _make_search_web(llm):
    def tool_search_web(query):
        return commands.search_web_with_context(query, llm)
    return tool_search_web


def _make_save_memory():
    def tool_save_memory(title, content):
        return commands.save_important_info(title, content, category="user_saved")
    return tool_save_memory


def _make_end_conversation():
    def tool_end_conversation():
        return END_CONVERSATION
    return tool_end_conversation


TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_current_time",
        "description": "Get the current local date and time.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "Get the current or forecast weather for a location.",
        "parameters": {"type": "object", "properties": {
            "location": {"type": "string", "description": "City name. Omit to use the user's default location."},
            "when": {"type": "string", "description": "When, e.g. 'today', 'tomorrow', 'Friday'. Omit for right now."},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "tell_joke",
        "description": "Tell a random joke.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "start_timer",
        "description": "Start a countdown timer running in the background.",
        "parameters": {"type": "object", "properties": {
            "duration_minutes": {"type": "number", "description": "Length of the timer in minutes (convert other units, e.g. '2 hours' -> 120)."},
        }, "required": ["duration_minutes"]},
    }},

    {"type": "function", "function": {
        "name": "add_calendar_event",
        "description": "Create a new calendar event. If the user didn't give a time, omit start_time and a free slot will be found automatically.",
        "parameters": {"type": "object", "properties": {
            "summary": {"type": "string", "description": "Short title of the event."},
            "start_time": {"type": "string", "description": "ISO 8601 datetime (e.g. 2025-08-26T15:00:00), or omit if unspecified."},
            "duration_minutes": {"type": "number", "description": "Length in minutes. Omit to use a sensible default for the event type."},
            "date": {"type": "string", "description": "Date to search for a free slot on, only used when start_time is omitted."},
        }, "required": ["summary"]},
    }},
    {"type": "function", "function": {
        "name": "view_calendar_events",
        "description": "List the user's calendar events for a given date (defaults to today).",
        "parameters": {"type": "object", "properties": {
            "date": {"type": "string", "description": "Date to look up, e.g. 'today', 'tomorrow', 'next Monday'. Omit for today."},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "find_calendar_event",
        "description": "Find and describe a specific calendar event by name.",
        "parameters": {"type": "object", "properties": {
            "event_summary": {"type": "string", "description": "Title or partial title of the event to find."},
            "date_str": {"type": "string", "description": "Optional date to narrow the search."},
        }, "required": ["event_summary"]},
    }},
    {"type": "function", "function": {
        "name": "delete_calendar_event",
        "description": "Delete/cancel a calendar event by name.",
        "parameters": {"type": "object", "properties": {
            "event_summary": {"type": "string", "description": "Title or partial title of the event to delete."},
            "date_str": {"type": "string", "description": "Optional date to narrow which event is deleted."},
        }, "required": ["event_summary"]},
    }},
    {"type": "function", "function": {
        "name": "update_calendar_event",
        "description": "Update a calendar event's title, time, and/or date - also use this to move or reschedule an event.",
        "parameters": {"type": "object", "properties": {
            "event_summary": {"type": "string", "description": "Title or partial title of the event to update."},
            "date_str": {"type": "string", "description": "Date to help locate the event, if known."},
            "new_summary": {"type": "string", "description": "New title, if renaming."},
            "new_time": {"type": "string", "description": "New time, if rescheduling."},
            "new_date": {"type": "string", "description": "New date, if moving to a different day."},
        }, "required": ["event_summary"]},
    }},
    {"type": "function", "function": {
        "name": "list_upcoming_calendar_events",
        "description": "List the user's next upcoming calendar events, regardless of date.",
        "parameters": {"type": "object", "properties": {
            "max_results": {"type": "number", "description": "Maximum number of events to return. Default 10."},
        }, "required": []},
    }},

    {"type": "function", "function": {
        "name": "play_music",
        "description": "Play a song, artist, album, or playlist on Spotify.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to play, e.g. 'Bohemian Rhapsody by Queen' or 'my workout playlist'."},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "queue_music",
        "description": "Add a song to the Spotify play queue.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to queue up next."},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "pause_music",
        "description": "Pause Spotify playback.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "resume_music",
        "description": "Resume paused Spotify playback.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "next_song",
        "description": "Skip to the next track on Spotify.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "previous_song",
        "description": "Go back to the previous track on Spotify.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_current_song",
        "description": "Get the song currently playing on Spotify.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "set_volume",
        "description": "Set the Spotify playback volume.",
        "parameters": {"type": "object", "properties": {
            "volume_percent": {"type": "number", "description": "Volume from 0 to 100."},
        }, "required": ["volume_percent"]},
    }},

    {"type": "function", "function": {
        "name": "search_web",
        "description": "Search the web for current information and summarize the results. Use this for anything you don't already know or that may have changed recently.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to search for."},
        }, "required": ["query"]},
    }},

    {"type": "function", "function": {
        "name": "save_memory",
        "description": "Save a specific fact or preference to the user's long-term memory for later recall.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Short label for this memory."},
            "content": {"type": "string", "description": "The information to remember."},
        }, "required": ["title", "content"]},
    }},
    {"type": "function", "function": {
        "name": "search_memory",
        "description": "Search the user's long-term memory and past conversations.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to search for."},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "get_memory_stats",
        "description": "Get statistics about the memory system (how many items are stored, categories, etc).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},

    {"type": "function", "function": {
        "name": "create_notion_todo",
        "description": "Create a new to-do item in Notion.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Title of the to-do."},
            "description": {"type": "string", "description": "Optional extra detail."},
            "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format, if any."},
            "priority": {"type": "string", "enum": ["High", "Medium", "Low"], "description": "Priority, defaults to Medium."},
        }, "required": ["title"]},
    }},
    {"type": "function", "function": {
        "name": "create_notion_note",
        "description": "Create a new note/page in Notion.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Title of the note."},
            "content": {"type": "string", "description": "Body content of the note."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags."},
        }, "required": ["title", "content"]},
    }},
    {"type": "function", "function": {
        "name": "search_notion_pages",
        "description": "Search for pages/notes in the user's Notion workspace.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to search for."},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "search_notion_todos",
        "description": "List or search the user's Notion to-do items, optionally filtered by status.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Optional search text."},
            "status": {"type": "string", "enum": ["Not started", "In progress", "Done"], "description": "Optional status filter."},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "append_to_notion_page",
        "description": "Append content to an existing Notion page.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Name or search term identifying the page."},
            "content": {"type": "string", "description": "Content to append."},
        }, "required": ["query", "content"]},
    }},
    {"type": "function", "function": {
        "name": "get_notion_page_content",
        "description": "Read the content of a Notion page.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Name or search term identifying the page."},
        }, "required": ["query"]},
    }},

    {"type": "function", "function": {
        "name": "end_conversation",
        "description": "Call this ONLY when the user is clearly ending the interaction (e.g. 'goodbye', 'that's all, thanks', 'bye').",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
]

IOT_TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "turn_on_light",
        "description": "Turn on a smart light, optionally setting brightness and/or color.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string", "description": "Name of the light, e.g. 'living room light'."},
            "brightness": {"type": "number", "description": "Optional brightness 0-100."},
            "color": {"type": "string", "description": "Optional color or scene, e.g. 'warm white', 'reading mode'."},
        }, "required": ["device_name"]},
    }},
    {"type": "function", "function": {
        "name": "turn_off_light",
        "description": "Turn off a smart light.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string", "description": "Name of the light."},
        }, "required": ["device_name"]},
    }},
    {"type": "function", "function": {
        "name": "set_light_brightness",
        "description": "Set a smart light's brightness.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
            "brightness": {"type": "number", "description": "Brightness 0-100."},
        }, "required": ["device_name", "brightness"]},
    }},
    {"type": "function", "function": {
        "name": "set_light_color",
        "description": "Set a smart light's color or color temperature.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
            "color": {"type": "string", "description": "e.g. 'warm white', 'blue', 'reading mode'."},
        }, "required": ["device_name", "color"]},
    }},
    {"type": "function", "function": {
        "name": "turn_on_all_lights",
        "description": "Turn on every configured smart light.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "turn_off_all_lights",
        "description": "Turn off every configured smart light.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "turn_on_switch",
        "description": "Turn on a smart switch/plug.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
        }, "required": ["device_name"]},
    }},
    {"type": "function", "function": {
        "name": "turn_off_switch",
        "description": "Turn off a smart switch/plug.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
        }, "required": ["device_name"]},
    }},
    {"type": "function", "function": {
        "name": "set_temperature",
        "description": "Set a smart thermostat's target temperature.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
            "temperature": {"type": "number"},
        }, "required": ["device_name", "temperature"]},
    }},
    {"type": "function", "function": {
        "name": "get_sensor_reading",
        "description": "Read a sensor device's current value.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
        }, "required": ["device_name"]},
    }},
    {"type": "function", "function": {
        "name": "get_device_status",
        "description": "Get the current status of a specific smart home device.",
        "parameters": {"type": "object", "properties": {
            "device_name": {"type": "string"},
        }, "required": ["device_name"]},
    }},
    {"type": "function", "function": {
        "name": "list_all_devices",
        "description": "List all configured smart home devices.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
]


def build_tools(llm):
    """Return (schemas, dispatch) for the current config - LLM instance is
    bound in so tools like search_web can use it for summarization."""
    dispatch = {
        "get_current_time": commands.get_time,
        "get_weather": tool_get_weather,
        "tell_joke": commands.tell_joke,
        "start_timer": commands.start_timer,

        "add_calendar_event": tool_add_calendar_event,
        "view_calendar_events": commands.show_calendar_events,
        "find_calendar_event": commands.find_calendar_event,
        "delete_calendar_event": commands.delete_calendar_event,
        "update_calendar_event": commands.update_calendar_event,
        "list_upcoming_calendar_events": commands.list_upcoming_calendar_events,

        "play_music": commands.play_music,
        "queue_music": commands.queue_music,
        "pause_music": commands.pause_music,
        "resume_music": commands.resume_music,
        "next_song": commands.next_song,
        "previous_song": commands.previous_song,
        "get_current_song": commands.get_current_song,
        "set_volume": tool_set_volume,

        "search_web": _make_search_web(llm),

        "save_memory": _make_save_memory(),
        "search_memory": commands.search_my_memory,
        "get_memory_stats": commands.get_memory_stats,

        "create_notion_todo": commands.create_notion_todo,
        "create_notion_note": commands.create_notion_note,
        "search_notion_pages": commands.search_notion_pages,
        "search_notion_todos": commands.search_notion_todos,
        "append_to_notion_page": commands.append_to_notion_page,
        "get_notion_page_content": commands.get_notion_page_content,

        "end_conversation": _make_end_conversation(),
    }
    schemas = list(TOOL_SCHEMAS)

    # Only spend context budget on IoT tools when devices are actually
    # configured - otherwise they're ~12 tool definitions describing
    # capabilities that would just fail with "no such device" every time.
    if config.get('iot.devices', []):
        schemas += IOT_TOOL_SCHEMAS
        dispatch.update({
            "turn_on_light": turn_on_light,
            "turn_off_light": turn_off_light,
            "set_light_brightness": set_light_brightness,
            "set_light_color": set_light_color,
            "turn_on_all_lights": turn_on_all_lights,
            "turn_off_all_lights": turn_off_all_lights,
            "turn_on_switch": turn_on_switch,
            "turn_off_switch": turn_off_switch,
            "set_temperature": set_temperature,
            "get_sensor_reading": get_sensor_reading,
            "get_device_status": get_device_status,
            "list_all_devices": list_all_devices,
        })

    return schemas, dispatch
