# main.py

from voice_recognition import VoiceRecognizer
from llm_interface import LLMInterface
from memory import Memory
from commands import get_weather, get_time, add_calendar_event, get_calendar_events_for_date, start_timer
from interruptible_tts import InterruptibleTTS
from command_parser import parse_calendar_add
from intent_parser import IntentParser
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
    timeout = 30  # Maximum time to wait for LLM
    
    while not recognizer.check_interrupt():
        if not llm.current_process:  # LLM finished
            break
        if time.time() - start_time > timeout:
            print("[WARN] LLM processing timeout")
            break
        time.sleep(0.05)  # Reduced sleep time for better responsiveness
    
    if recognizer.check_interrupt():
        print("[INFO] Interrupt detected during processing")
        llm.interrupt_llm()
        tts.interrupt()
        recognizer.clear_interrupt()
    
    recognizer.stop_interrupt_detection()

def is_interrupt_command(command):
    """Check if the command is an interrupt-related command"""
    interrupt_phrases = [
        "stop", "pause", "wait", "interrupt", "hold on", "quiet", 
        "shut up", "enough", "cancel", "nevermind", "never mind"
    ]
    return any(phrase in command.lower() for phrase in interrupt_phrases)

def main():
    memory = Memory()
    recognizer = VoiceRecognizer()
    llm = LLMInterface(model="mistral", memory=memory)
    tts = InterruptibleTTS(voice_recognizer=recognizer)
    
    print("[INFO] Assistant initialized with interrupt functionality")
    print("[INFO] You can interrupt the assistant by saying: stop, pause, wait, interrupt, hold on, quiet")

    while True:
        recognizer.listen_for_wake_word()
        tts.speak("Yes? I'm listening.", check_interrupts=False)

        command = recognizer.listen_for_command()
        if not command:
            tts.speak("I didn't catch that.", check_interrupts=False)
            continue

        print(f"[Heard command]: {command}")
        
        # Parse intent with improved system
        intent = intent_parser.parse_intent(command)
        print(f"[Detected intent]: {intent}")
        
        # Check if this is an interrupt command
        if intent == "interrupt" or is_interrupt_command(command):
            tts.speak("Okay, I'll stop talking.", check_interrupts=False)
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
                print("[Memory-related query detected]")
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
                location = "Guildford"  # default fallback
                target_time = extract_datetime(command)
                print("Target datetime:", target_time)
                
                # Enhanced location extraction using LLM
                location_prompt = f"""Extract the location from this weather request. If no location is mentioned, respond with 'Guildford' as a one word answer.
                
User request: "{command}"
                
Location:"""
                
                extracted_location = llm._call_llm(location_prompt).strip()
                if extracted_location and extracted_location.lower() != "Guildford":
                    location = extracted_location
                
                response = get_weather(location, target_time)
                memory.save_interaction(command, response, "weather")
            elif intent == "time":
                response = get_time()
                memory.save_interaction(command, response, "time")
            elif intent == "calendar_add":
                event_data = parse_calendar_add(llm, command)
                if event_data:
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
                tts.speak("I was interrupted. What would you like me to do?")
                continue
            
            # Speak the response with interrupt detection
            tts.speak(response, check_interrupts=True)
            
        except Exception as e:
            print(f"[ERROR] Error during command processing: {e}")
            tts.speak("I encountered an error processing your request.", check_interrupts=False)
        
        finally:
            # Clean up interrupt detection
            recognizer.stop_interrupt_detection()
            recognizer.clear_interrupt()

if __name__ == "__main__":
    main()
