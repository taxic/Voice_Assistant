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


def handle_command(command, recognizer, llm, tts, tool_schemas, dispatch, memory):
    """Process one recognized command through the agent and speak the reply.

    Returns True if the conversation should end (the assistant said goodbye).
    """
    if is_interrupt_command(command):
        interrupt_response = response_variations.get_interrupt_response()
        tts.speak(interrupt_response, check_interrupts=False)
        return False

    # Start interrupt monitoring in a separate thread
    interrupt_thread = threading.Thread(
        target=handle_interrupt_during_processing,
        args=(recognizer, llm, tts),
        daemon=True
    )
    interrupt_thread.start()

    try:
        # Speak each sentence as soon as the model finishes it, instead
        # of waiting for the whole response - this fires from inside
        # run_agent_turn while the rest of the reply is still streaming.
        def speak_sentence(sentence):
            tts.speak(sentence, check_interrupts=True)

        result = llm.run_agent_turn(command, tool_schemas, dispatch, on_sentence=speak_sentence)
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
            return False

        # The model's own reply carries its personality now - no canned
        # suffix bolted on afterward (see response_variations.py / the
        # system prompt in llm_interface.py for where that voice comes from).
        # Only speak it here if it wasn't already spoken sentence-by-sentence
        # above (error/timeout paths never stream, so still need this).
        if not result.get("streamed"):
            tts.speak(response, check_interrupts=True)

        return bool(result.get("ended_conversation"))

    except Exception as e:
        print(f"[ERROR] Error during command processing: {e}")
        error_response = response_variations.get_error_response()
        tts.speak(error_response, check_interrupts=False)
        return False

    finally:
        # Clean up interrupt detection
        recognizer.stop_interrupt_detection()
        recognizer.clear_interrupt()


def main():
    memory = EnhancedMemory()
    recognizer = VoiceRecognizer()
    llm = LLMInterface(memory=memory)  # Will use config for model
    tts = InterruptibleTTS(voice_recognizer=recognizer)
    tool_schemas, dispatch = build_tools(llm)

    assistant_name = config.get('assistant.name', 'Assistant')
    assistant_version = config.get('assistant.version', '1.0.0')
    interrupt_phrases = config.get('assistant.interrupt_phrases', ['stop', 'pause', 'wait'])
    command_timeout = config.get('voice.command_timeout', 10.0)
    follow_up_timeout = config.get('voice.follow_up_timeout', 5.0)

    print(f"[INFO] {assistant_name} v{assistant_version} initialized with interrupt functionality")
    print(f"[INFO] You can interrupt the assistant by saying: {', '.join(interrupt_phrases[:6])}")
    print(f"[INFO] {len(tool_schemas)} tools available to the agent")

    should_exit = False
    while not should_exit:
        recognizer.listen_for_wake_word()
        wake_response = response_variations.get_wake_response()
        tts.speak(wake_response, check_interrupts=False)

        command = recognizer.listen_for_command(timeout=command_timeout)
        first_listen = True

        # Keep listening for a bit after every reply instead of immediately
        # going back to requiring the wake word - so answering a clarifying
        # question (or just continuing to talk) doesn't need "Jarvis" said
        # again each time. One silent follow-up window with nothing heard
        # falls back to wake-word mode.
        while True:
            if not command:
                if first_listen:
                    clarification_response = response_variations.get_clarification_response()
                    tts.speak(clarification_response, check_interrupts=False)
                # else: the follow-up window just elapsed with nothing said -
                # go back to sleep quietly rather than nagging the user.
                break

            first_listen = False
            print(f"[Heard command]: {command}")

            if handle_command(command, recognizer, llm, tts, tool_schemas, dispatch, memory):
                should_exit = True
                break

            command = recognizer.listen_for_command(timeout=follow_up_timeout)

    # Clean up memory system when exiting
    try:
        memory.close()
        print("[INFO] Memory system closed successfully")
    except Exception as e:
        print(f"[WARN] Error closing memory system: {e}")

if __name__ == "__main__":
    # Run the main voice assistant by default
    main()
