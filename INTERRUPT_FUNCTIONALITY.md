# Interrupt Functionality Documentation

## Overview

The assistant now supports comprehensive interrupt functionality that allows users to stop the assistant mid-conversation, cancel ongoing operations, or provide additional information during processing. This feature makes the assistant more interactive and user-friendly.

## Features

### 1. Voice Interrupt Detection
- **Real-time listening**: The assistant continuously listens for interrupt commands while speaking or processing
- **Interrupt words**: "stop", "pause", "wait", "interrupt", "hold on", "quiet", "shut up", "enough", "cancel", "nevermind", "never mind"
- **Background processing**: Interrupt detection runs in a separate thread to ensure responsiveness

### 2. Interruptible Text-to-Speech
- **Chunked speech**: Long responses are broken into smaller chunks for more responsive interruption
- **Immediate stopping**: Speech can be stopped mid-sentence when an interrupt is detected
- **Clean cleanup**: Proper cleanup of TTS resources when interrupted

### 3. LLM Response Interruption
- **Process termination**: Can interrupt long-running LLM generation processes
- **Graceful handling**: Proper cleanup of subprocess resources
- **User feedback**: Informs user when generation was interrupted

### 4. Intent Recognition
- **Interrupt intent**: New "interrupt" intent added to the intent parser
- **Keyword fallback**: Multiple fallback methods ensure interrupt commands are recognized
- **Context awareness**: Handles interrupt commands appropriately based on current state

## Components

### VoiceRecognizer Updates
- `start_interrupt_detection()`: Starts background interrupt listening
- `stop_interrupt_detection()`: Stops background interrupt listening
- `check_interrupt()`: Checks if an interrupt was detected
- `clear_interrupt()`: Clears the interrupt flag
- `_interrupt_listener()`: Background thread for interrupt detection

### InterruptibleTTS
- `speak(text, check_interrupts=True)`: Speaks text with optional interrupt checking
- `interrupt()`: Manually interrupts current speech
- `_split_text_into_chunks()`: Breaks text into smaller chunks for responsiveness
- `is_currently_speaking()`: Checks if currently speaking

### LLMInterface Updates
- `interrupt_llm()`: Interrupts current LLM process
- `_call_llm_interruptible()`: Interruptible version of LLM calls
- Process management for graceful termination

### IntentParser Updates
- Added "interrupt" intent definition
- Added interrupt keywords to fallback patterns
- Enhanced intent recognition for interrupt commands

## Usage

### Basic Interrupt Commands
Users can interrupt the assistant at any time by saying:
- "Stop"
- "Pause"
- "Wait"
- "Interrupt"
- "Hold on"
- "Quiet"
- "Shut up"
- "Enough"
- "Cancel"
- "Nevermind"/"Never mind"

### During Response Generation
When the assistant is generating a response:
1. The system starts monitoring for interrupts
2. If an interrupt is detected, the LLM process is terminated
3. The user is informed that the response was interrupted
4. The assistant asks what the user would like to do next

### During Speech Output
When the assistant is speaking:
1. Speech is broken into chunks for responsiveness
2. Each chunk is checked for interrupts before speaking
3. If interrupted, speech stops immediately
4. The assistant acknowledges the interrupt

## Implementation Details

### Thread Safety
- Interrupt detection runs in daemon threads
- Proper synchronization between threads
- Clean resource cleanup in all scenarios

### Error Handling
- Graceful handling of subprocess termination
- Proper cleanup of audio resources
- User feedback for error conditions

### Performance
- Minimal overhead during normal operation
- Efficient background processing
- Quick response to interrupt commands

## Testing

Run the test script to verify interrupt functionality:

```bash
python test_interrupt.py
```

This will test:
1. Basic TTS without interruption
2. Manual interrupt simulation
3. Voice recognition interrupt simulation

## Configuration

### Interrupt Words
Modify the `interrupt_words` list in `VoiceRecognizer` to customize interrupt commands:

```python
self.interrupt_words = ["stop", "pause", "wait", "interrupt", "hold on", "quiet"]
```

### TTS Chunking
Adjust the `max_chunk_size` parameter in `InterruptibleTTS._split_text_into_chunks()` for different responsiveness levels:

```python
def _split_text_into_chunks(self, text, max_chunk_size=50):
```

### Interrupt Detection Sensitivity
Modify the timeout in `VoiceRecognizer._interrupt_listener()` for different sensitivity:

```python
data = self.q.get(timeout=0.1)  # Shorter timeout = more responsive
```

## Future Enhancements

1. **Visual Interrupts**: Support for keyboard shortcuts or UI buttons
2. **Context-Aware Interrupts**: Different behaviors based on current activity
3. **Interrupt Queuing**: Handle multiple rapid interrupts gracefully
4. **Customizable Responses**: User-configurable interrupt acknowledgments
5. **Interrupt Analytics**: Track interrupt patterns for UX improvements

## Troubleshooting

### Common Issues

1. **Interrupt not detected**: Check microphone permissions and voice model
2. **Speech not stopping**: Verify TTS engine compatibility
3. **Process not terminating**: Check subprocess handling in LLM interface

### Debug Mode
Enable debug logging by setting:
```python
print("[DEBUG] Interrupt listener started")
```

### Performance Issues
If interrupt detection causes performance problems:
1. Increase the timeout in `_interrupt_listener()`
2. Reduce the frequency of interrupt checks
3. Consider using a more efficient voice recognition model

## API Reference

### VoiceRecognizer
- `start_interrupt_detection()`: Start background interrupt detection
- `stop_interrupt_detection()`: Stop background interrupt detection
- `check_interrupt() -> bool`: Check if interrupt was detected
- `clear_interrupt()`: Clear interrupt flag

### InterruptibleTTS
- `speak(text: str, check_interrupts: bool = True)`: Speak with interrupt support
- `interrupt()`: Manually interrupt speech
- `is_currently_speaking() -> bool`: Check if speaking

### LLMInterface
- `interrupt_llm() -> bool`: Interrupt current LLM process
- `interrupt_requested: bool`: Flag indicating if interrupt was requested
