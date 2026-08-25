# main.py

from voice_recognition import VoiceRecognizer
from llm_interface import LLMInterface
from enhanced_memory import EnhancedMemory
from interruptible_tts import InterruptibleTTS
from tools import build_tools
from config_manager import config
from response_variations import response_variations
import threading
import time

# response_variations.add_personality_to_response() still keys off the old
# intent-string vocabulary (e.g. "calendar_add", "music_play") from before
# tool-calling replaced the intent classifier. Map the new tool names onto
# those buckets so the existing personality touches keep firing instead of
# silently going dark on a naming mismatch.
_PERSONALITY_INTENT_MAP = {
    "start_timer": "timer",
    "add_calendar_event": "calendar_add",
    "play_music": "music_play",
    "save_memory": "save_memory",
    "get_weather": "weather",
    "get_current_time": "time",
    "search_web": "web_search",
    "search_memory": "memory_recall",
}


def handle_interrupt_during_processing(recognizer, llm, tts):
    """Monitor for interrupts during LLM/tool processing"""
    recognizer.start_interrupt_detection()

    start_time = time.time()
    # An agent turn can involve several tool-calling rounds, each a full LLM
    # round-trip - give the monitor enough headroom to keep listening across
    # all of them instead of giving up after a single round's timeout.
    timeout = config.get('llm.timeout_seconds', 60) * config.get('llm.agent_max_rounds', 4)

    while not recognizer.check_interrupt():
        if not llm.current_process:  # Agent turn finished
            break
        if time.time() - start_time > timeout:
            print("[WARN] LLM processing timeout")
            break
        time.sleep(config.get('voice.interrupt_check_interval', 0.05))

    if recognizer.check_interrupt():
        print("[INFO] Interrupt detected during processing")
        llm.interrupt_llm()
        tts.interrupt()
        recognizer.clear_interrupt()

    recognizer.stop_interrupt_detection()


def is_interrupt_command(command):
    """Check if the command is an interrupt-related command.

    Kept as a fast, deterministic keyword check rather than routed through
    the LLM: this needs to preempt whatever's happening immediately, so it
    can't wait on a model round-trip.
    """
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
    tool_schemas, dispatch = build_tools(llm)

    assistant_name = config.get('assistant.name', 'Assistant')
    assistant_version = config.get('assistant.version', '1.0.0')
    interrupt_phrases = config.get('assistant.interrupt_phrases', ['stop', 'pause', 'wait'])

    print(f"[INFO] {assistant_name} v{assistant_version} initialized with interrupt functionality")
    print(f"[INFO] You can interrupt the assistant by saying: {', '.join(interrupt_phrases[:6])}")
    print(f"[INFO] {len(tool_schemas)} tools available to the agent")

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

        if is_interrupt_command(command):
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
            result = llm.run_agent_turn(command, tool_schemas, dispatch)
            response = result["response"]
            tool_names = [call["name"] for call in result["tool_calls"]]

            memory.save_interaction(command, response, tool_names[0] if tool_names else "general", tags=tool_names)

            # Wait for interrupt thread to complete
            interrupt_thread.join(timeout=1)

            # Check if the response was interrupted
            if llm.interrupt_requested:
                print("[INFO] Response generation was interrupted")
                interrupted_response = response_variations.get_interrupt_response() + " What would you like me to do?"
                tts.speak(interrupted_response)
                continue

            # Add personality to response before speaking
            personality_intent = _PERSONALITY_INTENT_MAP.get(tool_names[0]) if tool_names else None
            enhanced_response = response_variations.add_personality_to_response(response, personality_intent)

            # Speak the response with interrupt detection
            tts.speak(enhanced_response, check_interrupts=True)

            if result.get("ended_conversation"):
                break

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
