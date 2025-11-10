# main.py

from voice_recognition import VoiceRecognizer
from llm_interface import LLMInterface
from enhanced_memory import EnhancedMemory
from commands import get_weather, get_time, add_calendar_event, get_calendar_events_for_date, start_timer, tell_joke, play_music, queue_music, pause_music, resume_music, next_song, previous_song, get_current_song, set_volume, search_web, search_web_with_context, get_memory_stats, save_important_info, search_my_memory, create_notion_todo, create_notion_note, search_notion_pages, search_notion_todos, append_to_notion_page, get_notion_page_content,  get_calendar_status, authenticate_calendars, authenticate_outlook, refresh_calendar_cache, get_calendar_cache_status, cleanup_calendar_cache, export_calendar_data, sync_calendar_now, delete_calendar_event, update_calendar_event, list_upcoming_calendar_events, move_calendar_event, reschedule_calendar_event, find_calendar_event, show_calendar_events, cancel_calendar_event, modify_calendar_event
from iot_commands import handle_iot_command
from calendar_interface import GoogleCalendar
from interruptible_tts import InterruptibleTTS
from command_parser import parse_calendar_add
from intent_parser import IntentParser
from config_manager import config
from response_variations import response_variations
import dateparser
from datetime import datetime
import threading
import time

# Initialize intent parser
intent_parser = IntentParser()

def extract_datetime(command):
    parsed = dateparser.parse(
        command,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now(),
            "PARSERS": ["relative-time", "absolute-time", "timestamp"],
        }
    )
    return parsed

def extract_date_with_llm(command, llm):
    """Use LLM to extract date/time information from calendar commands"""
    try:
        # First try the basic dateparser
        basic_parsed = extract_datetime(command)
        if basic_parsed:
            return basic_parsed
        
        # If basic parsing fails, use LLM to help extract the date
        current_time = datetime.now()
        date_prompt = f"""Extract the date/time information from this calendar request. Today is {current_time.strftime('%A, %B %d, %Y')} and the current time is {current_time.strftime('%H:%M')}.

User request: "{command}"

If the request mentions:
- "today" - respond with "today"
- "tomorrow" - respond with "tomorrow"
- "yesterday" - respond with "yesterday"
- "Monday", "Tuesday", etc. - respond with the day name
- A specific date like "July 25th" - respond with that date
- "this week", "next week" - respond with the relative week reference
- If NO date/time is mentioned, respond with "today"

Respond with ONLY the date/time reference (e.g., "tomorrow", "Monday", "July 25th", "today"):"""
        
        extracted_date_text = llm._call_llm(date_prompt).strip().lower()
        print(f"[DEBUG] LLM extracted date text: '{extracted_date_text}'")
        
        # Now parse the extracted date text
        if extracted_date_text:
            parsed_date = dateparser.parse(
                extracted_date_text,
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": current_time,
                    "PARSERS": ["relative-time", "absolute-time", "timestamp"],
                }
            )
            print(f"[DEBUG] Parsed date from LLM text: {parsed_date}")
            return parsed_date
            
    except Exception as e:
        print(f"[WARN] LLM date extraction failed: {e}")
    
    return None

def handle_interrupt_during_processing(recognizer, llm, tts):
    """Monitor for interrupts during LLM processing"""
    recognizer.start_interrupt_detection()
    
    # More efficient interrupt checking with event-based approach
    start_time = time.time()
    timeout = config.get('llm.timeout_seconds', 30)  # Maximum time to wait for LLM
    
    while not recognizer.check_interrupt():
        if not llm.current_process:  # LLM finished
            break
        if time.time() - start_time > timeout:
            print("[WARN] LLM processing timeout")
            break
        time.sleep(config.get('voice.interrupt_check_interval', 0.05))  # Configurable sleep time
    
    if recognizer.check_interrupt():
        print("[INFO] Interrupt detected during processing")
        llm.interrupt_llm()
        tts.interrupt()
        recognizer.clear_interrupt()
    
    recognizer.stop_interrupt_detection()

def is_interrupt_command(command):
    """Check if the command is an interrupt-related command"""
    interrupt_phrases = config.get('assistant.interrupt_phrases', [
        "stop", "pause", "wait", "interrupt", "hold on", "quiet", 
        "shut up", "enough", "cancel", "nevermind", "never mind"
    ])
    return any(phrase in command.lower() for phrase in interrupt_phrases)

def main():
    memory = EnhancedMemory()
    recognizer = VoiceRecognizer()
    llm = LLMInterface(memory=memory)  # Will use config for model
    tts = InterruptibleTTS(voice_recognizer=recognizer)
    calendar = GoogleCalendar()  # Initialize calendar interface
    
    assistant_name = config.get('assistant.name', 'Assistant')
    assistant_version = config.get('assistant.version', '1.0.0')
    interrupt_phrases = config.get('assistant.interrupt_phrases', ['stop', 'pause', 'wait'])
    
    print(f"[INFO] {assistant_name} v{assistant_version} initialized with interrupt functionality")
    print(f"[INFO] You can interrupt the assistant by saying: {', '.join(interrupt_phrases[:6])}")

    while True:
        recognizer.listen_for_wake_word()
        wake_response = response_variations.get_wake_response()
        tts.speak(wake_response, check_interrupts=False)

        command = recognizer.listen_for_command()
        if not command:
            clarification_response = response_variations.get_clarification_response()
            tts.speak(clarification_response, check_interrupts=False)
            continue

        print(f"[Heard command]: {command}")
        
        # Parse intent with improved system
        intent = intent_parser.parse_intent(command)
        print(f"[Detected intent]: {intent}")
        
        # Check if this is an interrupt command
        if intent == "interrupt" or is_interrupt_command(command):
            interrupt_response = response_variations.get_interrupt_response()
            tts.speak(interrupt_response, check_interrupts=False)
            continue
        
        # Start interrupt monitoring in a separate thread
        interrupt_thread = threading.Thread(
            target=handle_interrupt_during_processing,
            args=(recognizer, llm, tts),
            daemon=True
        )
        interrupt_thread.start()
        
        try:
            # Handle memory-related queries first
            if intent == "memory_recall" or intent_parser.is_memory_related(command):
                print("[Memory-related query detected")
                response = llm.get_response_with_memory_search(command)
                memory.save_interaction(command, response, "memory_query")
            # Handle specific command intents
            elif intent == "timer":
                duration = IntentParser.extract_timer_duration(command)
                if duration:
                    response = start_timer(duration)
                    memory.save_interaction(command, response, "timer")
                else:
                    response = "Sorry, I couldn't understand the timer duration." 
                    memory.save_interaction(command, response, "timer_error")
            elif intent == "get_weather":
                default_location = config.get('weather.default_location', 'Guildford')
                location = default_location  # default fallback
                target_time = extract_datetime(command)
                print("Target datetime:", target_time)
                
                # Enhanced location extraction using LLM
                location_prompt = f"""Extract the location from this weather request. If no location is mentioned, respond with '{default_location}' as a one word answer.
                
User request: "{command}"
                
Location:"""
                
                extracted_location = llm._call_llm(location_prompt).strip()
                if extracted_location and extracted_location.lower() != default_location.lower():
                    location = extracted_location
                
                response = get_weather(location, target_time)
                memory.save_interaction(command, response, "weather")
            elif intent == "time":
                response = get_time()
                memory.save_interaction(command, response, "time")
            elif intent == "joke":
                response = tell_joke()
                memory.save_interaction(command, response, "joke")
            elif intent == "play_music":
                music_query = IntentParser.extract_music_query(command)
                if music_query:
                    response = play_music(music_query)
                    memory.save_interaction(command, response, "music_play")
                else:
                    response = "Sorry, I couldn't understand what music you want to play."
                    memory.save_interaction(command, response, "music_error")
            elif intent == "queue_music":
                music_query = IntentParser.extract_music_query(command)
                if music_query:
                    response = queue_music(music_query)
                    memory.save_interaction(command, response, "music_queue")
                else:
                    response = "Sorry, I couldn't understand what music you want to queue."
                    memory.save_interaction(command, response, "music_error")
            elif intent == "pause_music":
                response = pause_music()
                memory.save_interaction(command, response, "music_pause")
            elif intent == "resume_music":
                response = resume_music()
                memory.save_interaction(command, response, "music_resume")
            elif intent == "next_song":
                response = next_song()
                memory.save_interaction(command, response, "music_next")
            elif intent == "previous_song":
                response = previous_song()
                memory.save_interaction(command, response, "music_previous")
            elif intent == "current_song":
                response = get_current_song()
                memory.save_interaction(command, response, "music_current")
            elif intent == "volume_control":
                response = set_volume(command)
                memory.save_interaction(command, response, "music_volume")
            elif intent == "web_search":
                search_query = IntentParser.extract_search_query(command)
                if search_query:
                    # Use contextual web search with LLM for better responses
                    response = search_web_with_context(search_query, llm)
                    memory.save_interaction(command, response, "web_search")
                else:
                    response = "Sorry, I couldn't understand what you want me to search for."
                    memory.save_interaction(command, response, "search_error")
            elif intent == "memory_stats":
                response = get_memory_stats()
                memory.save_interaction(command, response, "memory_stats")
            elif intent == "save_memory":
                content = IntentParser.extract_memory_content(command)
                if content and len(content) > 5:  # Ensure there's meaningful content
                    # Generate a title from the content
                    title = content[:50] + "..." if len(content) > 50 else content
                    response = save_important_info(title, content, "user_saved")
                    memory.save_interaction(command, response, "save_memory", importance=8)
                else:
                    response = "Sorry, I couldn't understand what you want me to remember. Please be more specific."
                    memory.save_interaction(command, response, "save_memory_error")
            elif intent == "search_memory":
                search_query = IntentParser.extract_search_query(command)
                if not search_query:
                    # Try to extract from memory search patterns
                    memory_patterns = ["about", "regarding", "concerning"]
                    for pattern in memory_patterns:
                        if pattern in command.lower():
                            parts = command.lower().split(pattern, 1)
                            if len(parts) > 1:
                                search_query = parts[1].strip()
                                break
                    if not search_query:
                        search_query = command
                
                if search_query:
                    response = search_my_memory(search_query)
                    memory.save_interaction(command, response, "search_memory")
                else:
                    response = "Sorry, I couldn't understand what to search for in your memories."
                    memory.save_interaction(command, response, "search_memory_error")
            elif intent == "calendar_add":
                event_data = parse_calendar_add(llm, command)
                if event_data:
                    # Check if time was extracted or if we need to prompt/find space
                    if not event_data.get("start_time") or "default" in str(event_data.get("start_time", "")).lower():
                        tts.speak("I notice you didn't specify a time for this event. Would you like me to find a free time slot for you, or would you prefer to specify a time?")
                        
                        time_command = recognizer.listen_for_command()
                        if time_command and any(word in time_command.lower() for word in ["find", "free", "slot", "automatic", "yes"]):
                            # Find free time slot
                            try:
                                from datetime import datetime, timedelta
                                import dateparser
                                
                                # Parse the date from the original command or use today
                                event_date = datetime.now().date()
                                if "tomorrow" in command.lower():
                                    event_date = (datetime.now() + timedelta(days=1)).date()
                                
                                duration = event_data.get("duration_minutes", 60)
                                free_time = calendar.find_free_time_slot(duration, event_date)
                                
                                if free_time:
                                    # Update event data with found time
                                    start_datetime = datetime.combine(event_date, datetime.strptime(free_time, "%H:%M").time())
                                    event_data["start_time"] = start_datetime.isoformat()
                                    response = add_calendar_event(
                                        summary=event_data["summary"],
                                        time=event_data["start_time"],
                                        duration=duration
                                    )
                                    response += f" I found a free slot at {free_time}."
                                else:
                                    response = f"I couldn't find a free {duration}-minute slot. Please specify a time."
                            except Exception as e:
                                response = f"Error finding free time: {str(e)}"
                        else:
                            # Ask for specific time
                            tts.speak("Please tell me what time you'd like to schedule this event.")
                            time_command = recognizer.listen_for_command()
                            if time_command:
                                # Re-parse with the time information
                                full_command = f"{command} at {time_command}"
                                event_data = parse_calendar_add(llm, full_command)
                                if event_data and event_data.get("start_time"):
                                    response = add_calendar_event(
                                        summary=event_data["summary"],
                                        time=event_data["start_time"],
                                        duration=event_data.get("duration_minutes", 60)
                                    )
                                else:
                                    response = "I couldn't understand the time. Please try again."
                            else:
                                response = "No time specified. Event not created."
                    else:
                        # Time was provided, create event using unified calendar
                        response = add_calendar_event(
                            summary=event_data["summary"],
                            time=event_data["start_time"],
                            duration=event_data.get("duration_minutes", 60)
                        )
                    memory.save_interaction(command, response, "calendar_add")
                else:
                    response = "Invalid calendar event format."
                    memory.save_interaction(command, response, "calendar_error")
            elif intent == "calendar_view":
                # Extract date from the command using LLM assistance
                target_date = extract_date_with_llm(command, llm)
                print("Target date extracted:", target_date)
                if target_date:
                    date_str = target_date.strftime('%Y-%m-%d')
                    print(f"Using date: {date_str}")
                    response = get_calendar_events_for_date(date_str)
                else:
                    # If no specific date found, default to today
                    from datetime import datetime
                    today = datetime.now()
                    date_str = today.strftime('%Y-%m-%d')
                    print(f"No date found in command, defaulting to today: {date_str}")
                    response = get_calendar_events_for_date(date_str)
                memory.save_interaction(command, response, "calendar_view")
            elif intent == "calendar_delete":
                # Extract event details for deletion using specialized method
                delete_details = IntentParser.extract_calendar_delete_details(command)
                event_summary = delete_details.get('event_summary')
                date_str = delete_details.get('date')

                if not event_summary:
                    response = "I need to know which event you want to delete. Please specify the event title or name."
                else:
                    response = delete_calendar_event(event_summary, date_str)
                memory.save_interaction(command, response, "calendar_delete")
            elif intent == "calendar_update":
                # Try move details first (more specific for rescheduling)
                move_details = IntentParser.extract_calendar_move_details(command)
                if move_details.get('event_summary') and (move_details.get('new_time') or move_details.get('new_date')):
                    # This is a move/reschedule command
                    event_summary = move_details.get('event_summary')
                    new_time = move_details.get('new_time')
                    new_date = move_details.get('new_date')

                    if new_time and new_date:
                        response = reschedule_calendar_event(event_summary, new_date, new_time)
                    elif new_time:
                        response = move_calendar_event(event_summary, new_time)
                    elif new_date:
                        response = reschedule_calendar_event(event_summary, new_date)
                    else:
                        response = "Please specify the new time or date for the event."
                else:
                    # Fall back to general update extraction
                    update_details = IntentParser.extract_calendar_update_details(command)
                    event_summary = update_details.get('event_summary')
                    date_str = update_details.get('date')
                    update_type = update_details.get('update_type')
                    new_value = update_details.get('new_value')

                    if not event_summary:
                        response = "I need to know which event you want to update. Please specify the event title or name."
                    elif not update_type or not new_value:
                        response = "Please specify what you want to update and the new value. For example: 'change meeting to 3 PM' or 'move dentist appointment to tomorrow'."
                    else:
                        if update_type == "summary":
                            response = update_calendar_event(event_summary, date_str, new_summary=new_value)
                        elif update_type in ["time", "date"]:
                            if update_type == "time":
                                response = update_calendar_event(event_summary, date_str, new_time=new_value)
                            else:  # date
                                response = update_calendar_event(event_summary, date_str, new_date=new_value)
                        else:
                            response = f"I can update event titles, times, or dates. Please specify what you want to change about '{event_summary}'."

                memory.save_interaction(command, response, "calendar_update")
            elif intent == "calendar_find":
                # Extract event details for finding
                event_details = IntentParser.extract_calendar_event_details(command)
                event_summary = event_details.get('event_summary')
                date_str = event_details.get('date')

                if not event_summary:
                    response = "I need to know which event you're looking for. Please specify the event title or name."
                else:
                    response = find_calendar_event(event_summary, date_str)
                memory.save_interaction(command, response, "calendar_find")
            elif intent == "calendar_list":
                # Extract date for listing events
                target_date = extract_date_with_llm(command, llm)
                if target_date:
                    date_str = target_date.strftime('%Y-%m-%d')
                    response = show_calendar_events(date_str)
                else:
                    # Default to today
                    response = show_calendar_events()
                memory.save_interaction(command, response, "calendar_list")
            elif intent == "notion_todo":
                # Extract todo details using LLM
                todo_prompt = f"""Extract the todo item details from this request:

User request: "{command}"

Please extract:
1. Title (required)
2. Description (optional)
3. Priority (High/Medium/Low, default: Medium)
4. Due date (if mentioned, in YYYY-MM-DD format)

Respond in this format:
Title: [title]
Description: [description or "none"]
Priority: [priority]
Due Date: [date or "none"]"""
                
                extracted_details = llm._call_llm(todo_prompt).strip()
                print(f"[DEBUG] LLM extracted todo details: {extracted_details}")
                
                # Parse the extracted details
                title = "New Todo Item"
                description = ""
                priority = "Medium"
                due_date = None
                
                try:
                    lines = extracted_details.split('\n')
                    for line in lines:
                        if line.startswith('Title:'):
                            title = line.replace('Title:', '').strip()
                        elif line.startswith('Description:'):
                            desc_text = line.replace('Description:', '').strip()
                            if desc_text.lower() != 'none':
                                description = desc_text
                        elif line.startswith('Priority:'):
                            priority_text = line.replace('Priority:', '').strip()
                            if priority_text in ['High', 'Medium', 'Low']:
                                priority = priority_text
                        elif line.startswith('Due Date:'):
                            date_text = line.replace('Due Date:', '').strip()
                            if date_text.lower() != 'none':
                                try:
                                    # Validate date format
                                    datetime.strptime(date_text, '%Y-%m-%d')
                                    due_date = date_text
                                except:
                                    pass
                except Exception as e:
                    print(f"[WARN] Failed to parse todo details: {e}")
                
                response = create_notion_todo(title, description, due_date, priority)
                memory.save_interaction(command, response, "notion_todo")
            elif intent == "notion_note":
                # Extract note details using LLM
                note_prompt = f"""Extract the note details from this request:

User request: "{command}"

Please extract:
1. Title (required)
2. Content (required)
3. Tags (optional, comma-separated)

Respond in this format:
Title: [title]
Content: [content]
Tags: [tags or "none"]"""
                
                extracted_details = llm._call_llm(note_prompt).strip()
                print(f"[DEBUG] LLM extracted note details: {extracted_details}")
                
                # Parse the extracted details
                title = "New Note"
                content = ""
                tags = None
                
                try:
                    lines = extracted_details.split('\n')
                    for line in lines:
                        if line.startswith('Title:'):
                            title = line.replace('Title:', '').strip()
                        elif line.startswith('Content:'):
                            content = line.replace('Content:', '').strip()
                        elif line.startswith('Tags:'):
                            tags_text = line.replace('Tags:', '').strip()
                            if tags_text.lower() != 'none':
                                tags = [tag.strip() for tag in tags_text.split(',')]
                except Exception as e:
                    print(f"[WARN] Failed to parse note details: {e}")
                
                if not content:
                    content = command  # Use the original command as content if no specific content extracted
                
                response = create_notion_note(title, content, tags)
                memory.save_interaction(command, response, "notion_note")
            elif intent == "notion_search":
                search_query = IntentParser.extract_search_query(command)
                if not search_query:
                    # Try to extract search terms from Notion-specific patterns
                    notion_patterns = ["find", "search for", "look for", "show me"]
                    for pattern in notion_patterns:
                        if pattern in command.lower():
                            parts = command.lower().split(pattern, 1)
                            if len(parts) > 1:
                                search_query = parts[1].strip().replace("in notion", "").strip()
                                break
                    if not search_query:
                        search_query = command.replace("notion", "").strip()
                
                response = search_notion_pages(search_query)
                memory.save_interaction(command, response, "notion_search")
            elif intent == "notion_todos":
                # Extract search parameters
                search_query = ""
                status = None
                
                # Check for status keywords
                status_keywords = {
                    "not started": "Not started",
                    "in progress": "In progress", 
                    "done": "Done",
                    "completed": "Done",
                    "finished": "Done"
                }
                
                for keyword, status_value in status_keywords.items():
                    if keyword in command.lower():
                        status = status_value
                        break
                
                # Extract search query
                todo_search_query = IntentParser.extract_search_query(command)
                if todo_search_query:
                    search_query = todo_search_query
                
                response = search_notion_todos(search_query, status)
                memory.save_interaction(command, response, "notion_todos")
            elif intent == "notion_append":
                # Extract page and content details using LLM
                append_prompt = f"""Extract the details for appending content to a Notion page:

User request: "{command}"

Please extract:
1. Page name or search term (required)
2. Content to append (required)

Respond in this format:
Page: [page name or search term]
Content: [content to append]"""
                
                extracted_details = llm._call_llm(append_prompt).strip()
                print(f"[DEBUG] LLM extracted append details: {extracted_details}")
                
                # Parse the extracted details
                page_query = ""
                content = ""
                
                try:
                    lines = extracted_details.split('\n')
                    for line in lines:
                        if line.startswith('Page:'):
                            page_query = line.replace('Page:', '').strip()
                        elif line.startswith('Content:'):
                            content = line.replace('Content:', '').strip()
                except Exception as e:
                    print(f"[WARN] Failed to parse append details: {e}")
                
                if page_query and content:
                    response = append_to_notion_page(page_query, content)
                    memory.save_interaction(command, response, "notion_append")
                else:
                    response = "Sorry, I couldn't understand which page to update or what content to add."
                    memory.save_interaction(command, response, "notion_append_error")
            elif intent == "notion_read":
                # Extract page search query
                read_query = IntentParser.extract_search_query(command)
                if not read_query:
                    # Try to extract from read-specific patterns
                    read_patterns = ["read", "show", "get content from", "what's in"]
                    for pattern in read_patterns:
                        if pattern in command.lower():
                            parts = command.lower().split(pattern, 1)
                            if len(parts) > 1:
                                read_query = parts[1].strip().replace("page", "").replace("in notion", "").strip()
                                break
                    if not read_query:
                        read_query = command.replace("notion", "").strip()
                
                if read_query:
                    response = get_notion_page_content(read_query)
                    memory.save_interaction(command, response, "notion_read")
                else:
                    response = "Sorry, I couldn't understand which page you want me to read."
                    memory.save_interaction(command, response, "notion_read_error")
            elif intent == "iot_control" or intent == "iot_status":
                # Handle IoT device control and status commands
                response = handle_iot_command(command)
                memory.save_interaction(command, response, intent)
            elif intent == "greeting":
                response = llm.get_response(command, use_memory_context=False)
                memory.save_interaction(command, response, "greeting")
            elif intent == "goodbye":
                response = llm.get_response(command, use_memory_context=False)
                memory.save_interaction(command, response, "goodbye")
                tts.speak(response)
                break  # Exit the loop
            else:
                # For general questions, use memory context
                print("[General query - using memory context]")
                response = llm.get_response(command, use_memory_context=True)
                memory.save_interaction(command, response, "general")
            
            # Wait for interrupt thread to complete
            interrupt_thread.join(timeout=1)
            
            # Check if the response was interrupted
            if llm.interrupt_requested:
                print("[INFO] Response generation was interrupted")
                interrupted_response = response_variations.get_interrupt_response() + " What would you like me to do?"
                tts.speak(interrupted_response)
                continue
            
            # Add personality to response before speaking
            enhanced_response = response_variations.add_personality_to_response(response, intent)
            
            # Speak the response with interrupt detection
            tts.speak(enhanced_response, check_interrupts=True)
            
        except Exception as e:
            print(f"[ERROR] Error during command processing: {e}")
            error_response = response_variations.get_error_response()
            tts.speak(error_response, check_interrupts=False)
        
        finally:
            # Clean up interrupt detection
            recognizer.stop_interrupt_detection()
            recognizer.clear_interrupt()
    
    # Clean up memory system when exiting
    try:
        memory.close()
        print("[INFO] Memory system closed successfully")
    except Exception as e:
        print(f"[WARN] Error closing memory system: {e}")

if __name__ == "__main__":
    # Run the main voice assistant by default
    main()
