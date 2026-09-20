# AI Voice Assistant - Complete Documentation

A sophisticated voice-controlled AI assistant with advanced memory capabilities, Spotify integration, web search, smart home control, enhanced memory system, interrupt functionality, and modern GUI interface. Built with Python and powered by local LLM (Ollama) for privacy and offline operation.

## 🚀 Features

- **Voice Recognition**: Wake word detection and command processing
- **Enhanced Memory System**: Advanced contextual conversation memory with intelligent categorization and search
- **Piper TTS**: High-quality neural text-to-speech synthesis (British English female voice)
- **Spotify Integration**: Music control and playlist management
- **Web Search**: Real-time web search capabilities with intelligent result processing
- **Smart Home Control**: IoT device management including Tapo smart lights
- **GUI Interface**: Modern graphical user interface for enhanced interaction
- **Calendar Integration**: Google Calendar events management with smart time suggestions
- **Weather Information**: Real-time weather data via Open-Meteo API
- **Timer Functionality**: Set and manage countdowns
- **Interrupt Capability**: Stop the assistant mid-response
- **Intent Recognition**: Smart LLM-powered command understanding
- **Notion Integration**: Task and note management via Notion API
- **Smart Event Times**: Automatic time suggestions for calendar events
- **Silent Light Control**: Quiet operation for successful commands with error feedback

## 🛠️ Technology Stack

- **Python 3.7+**
- **Ollama** (Local LLM - Qwen2.5 7B Instruct by default, tool-calling capable)
- **Vosk** (Speech Recognition)
- **Piper TTS** (Neural Text-to-Speech)
- **Spotify Web API** (Music Integration)
- **Web Search APIs** (Real-time search capabilities)
- **Tapo Python Library** (Smart Light Control)
- **Tkinter/PyQt** (GUI Framework)
- **Google Calendar API**
- **SQLite** (Enhanced Memory Storage)
- **Open-Meteo API** (Weather Data)
- **Notion API** (Task Management)

## 📦 Installation

### Prerequisites

1. **Install Python 3.7+**
2. **Install Ollama**: [Download from ollama.ai](https://ollama.ai/)
3. **Download Vosk Model**:
   ```bash
   mkdir models
   cd models
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip
   ```

### Python Dependencies

```bash
pip install -r requirements.txt
```

### Google Calendar Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create credentials (OAuth 2.0)
5. Download `credentials.json` to project root

### Spotify Setup (Optional)

1. Create a Spotify app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Set redirect URI to `http://localhost:8888/callback`
3. Add environment variables:
   ```bash
   export SPOTIFY_CLIENT_ID="your_client_id"
   export SPOTIFY_CLIENT_SECRET="your_client_secret"
   export SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
   ```

### Navidrome + Chromecast Setup (Optional)

Room-targeted playback from a self-hosted [Navidrome](https://www.navidrome.org/) music server, cast to Google Cast/Chromecast speakers.

1. Add environment variables for your Navidrome server:
   ```bash
   export NAVIDROME_URL="http://your-mini-pc:4533"
   export NAVIDROME_USERNAME="your_username"
   export NAVIDROME_PASSWORD="your_password"
   ```
2. In `config.json`, map room names to each Chromecast device's actual Cast friendly name (Google Home app → device → settings shows this) and pick a default room:
   ```json
   "chromecast": {
     "rooms": {
       "kitchen": "Kitchen Speaker",
       "living room": "Living Room TV"
     },
     "default_room": "kitchen"
   }
   ```
3. The device running the assistant needs to be on the same network/subnet as the Chromecasts - device discovery uses mDNS, which doesn't cross subnets.

Plays one track per request rather than a continuous queue/playlist right now - see the Music/Chromecast section under Advanced Features for why, and what a fuller version would need.

### Ollama Setup

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

The first is the default chat model (`llm.model` in `config.json`), chosen to fit comfortably in 6GB of VRAM (~4.7GB at Q4_K_M) while still supporting native tool/function calling, which the assistant relies on. If you have more VRAM to spare, a larger Qwen2.5 or Llama 3.3 model will reason better - just `ollama pull` it and update `llm.model` to match.

The second (`llm.embed_model`) is a small, separate model used only for semantic memory search - it's tiny (~274MB) and doesn't compete for VRAM with the chat model. Not strictly required to start the assistant - if it's missing, memory search just falls back to plain keyword matching instead of failing.

## 🎯 Usage

### Basic Usage

```bash
python main.py
```

### Settings GUI

```bash
python settings_gui.py
```

### Example Commands

**Basic Controls:**
- **Weather**: "What's the weather like in London?"
- **Calendar**: "Schedule a meeting tomorrow at 3 PM"
- **Timer**: "Set a timer for 15 minutes"
- **Memory**: "What did we discuss about the project?"

**Smart Home (IoT):**
- "Turn on the living room light"
- "Set bedroom light to reading mode"
- "Dim the office light to 50%"
- "Turn off all lights"
- "Set the lounge light to warm white"

**Music Control (Spotify):**
- "Play my workout playlist"
- "Skip to the next song"
- "Pause the music"
- "Turn up the volume"

**Room-Targeted Music (Navidrome + Chromecast):**
- "Play some jazz in the kitchen"
- "Play my workout playlist in the living room"
- "Pause the kitchen"
- "Set the living room volume to 40%"

**Web Search:**
- "Search for the latest Python tutorials"
- "What is quantum computing?"
- "Tell me about the latest news in AI"

**Memory & Information:**
- "Remember that I like pizza"
- "What do you know about me?"
- "Search my memories for pizza"

**Notion Integration:**
- "Create a todo to buy groceries"
- "Add a note about the meeting"
- "Show my todos"

**Coding:**
- "Write me a script that renames all files in a folder to lowercase"
- "What does this code print: [describe or read out the code]"
- "Run that script you just wrote" (asks for confirmation first, then run again to confirm)

### Interrupt Commands

You can interrupt the assistant at any time by saying:
- "Stop"
- "Pause" 
- "Wait"
- "Interrupt"
- "Hold on"
- "Quiet"
- "Cancel"
- "Nevermind"

## 🔧 Advanced Features

### Enhanced Memory System

The assistant maintains conversation context using:
- **Recent Memory**: Last 5-50 interactions (configurable)
- **Contextual Search**: Real semantic search via embeddings (Ollama's `nomic-embed-text`), not keyword matching - stored interactions and long-term memories are ranked by cosine similarity to the query, so phrasing doesn't need to match what was originally said. Falls back to keyword (`LIKE`) search automatically if the embed model isn't pulled or Ollama is unreachable.
- **Categorized Storage**: Different types of interactions (weather, calendar, etc.)
- **Importance Scoring**: A 1-10 field on every stored item, used to rank results - set explicitly (e.g. the assistant's own `save_memory` tool saves at high importance), not computed automatically from content
- **Auto-summarization**: Not yet real - the current "conversation summary" is a placeholder that just lists recent topic labels, not an actual LLM-generated summary. Known gap, not yet fixed.
- **Dated Events & Reminders**: Birthdays, anniversaries, and appointments are stored separately from free-text memory (a real `event_date`, not just text) via the `save_event` tool, so "what's coming up" can actually be computed instead of guessed from keywords. Yearly-recurring events (birthdays, anniversaries) automatically roll forward to their next occurrence, including correct Feb 29 handling in non-leap years. The assistant checks for anything due within `memory.reminder_window_days` (default 3) the first time you say the wake word each day and works it into its greeting - once per event per day, not on every single wake-up. Ask `get_upcoming_events` any time for a full list regardless of what's already been mentioned.

Run `ollama pull nomic-embed-text` alongside your chat model - semantic search needs it separately.

#### Memory Configuration
```json
{
  "memory": {
    "max_recent_interactions": 5,
    "contextual_search_limit": 3,
    "short_term_max_items": 50,
    "short_term_context_limit": 10,
    "long_term_context_limit": 5,
    "reminder_window_days": 3
  },
  "llm": {
    "embed_model": "nomic-embed-text",
    "embed_timeout_seconds": 30
  }
}
```

### Smart Event Times

Automatically suggests appropriate default times and durations for calendar events:

#### Supported Event Types:
- **Meals**: Breakfast (8:00 AM, 30 min), Lunch (1:00 PM, 60 min), Dinner (7:00 PM, 90 min)
- **Business**: Meeting (10:00 AM, 60 min), Conference (9:00 AM, 120 min)
- **Medical**: Doctor (10:00 AM, 30 min), Dentist (2:00 PM, 60 min)
- **Social**: Coffee (10:00 AM, 60 min), Movie (7:30 PM, 150 min)

### Smart Home (IoT) Control

#### Tapo Smart Light Integration
- **Voice Control**: "Turn on the living room light"
- **Brightness**: "Set the lounge light to 75% brightness"
- **Color Temperature**: "Set bedroom to warm white" (2700K)
- **Scenes**: "Set reading mode", "Set movie mode"
- **Group Control**: "Turn on all lights", "Turn off all lights"

#### IoT Configuration
```json
{
  "iot": {
    "devices": [
      {
        "id": "living_room_tapo_l530",
        "name": "lounge light",
        "type": "light",
        "protocol": "tapo",
        "username": "your_tapo_email",
        "password": "your_password",
        "ip": "192.168.1.100",
        "model": "L530"
      }
    ]
  }
}
```

### Music: Navidrome + Chromecast (Room-Targeted Playback)

- **Voice Control**: "Play some jazz in the kitchen", "play my workout playlist", "pause the living room"
- **Library Search**: Matches songs, albums, and playlists in your self-hosted Navidrome library via the Subsonic API - nothing leaves your network except to the Chromecast devices themselves
- **Room Targeting**: `chromecast.rooms` maps room names to each Chromecast's actual device name; omitting a room falls back to `chromecast.default_room`
- **Discovery Caching**: Devices are found once via mDNS (a few-second scan) and cached for the rest of the session, not re-scanned on every command - if a cached device stops responding (rebooted, new IP), it automatically re-discovers once and retries
- **Current limitation**: plays one track per request, not a continuous queue - "play some jazz" plays one jazz track, not an endless jazz session. Chromecast does support real queueing (`enqueue`-based, with a status-listener pattern to auto-advance), but that's meaningfully more code to get right, so it's a deliberate follow-up rather than something guessed at and shipped unverified. Worth revisiting once the basic cast-and-play path is confirmed working on real hardware.

#### Navidrome/Chromecast Configuration
```json
{
  "navidrome": {
    "url_env": "NAVIDROME_URL",
    "username_env": "NAVIDROME_USERNAME",
    "password_env": "NAVIDROME_PASSWORD",
    "timeout_seconds": 10
  },
  "chromecast": {
    "rooms": {
      "kitchen": "Kitchen Speaker",
      "living room": "Living Room TV"
    },
    "default_room": "kitchen",
    "discovery_timeout_seconds": 8
  }
}
```

### Web Search Integration

- **Privacy-Focused**: Uses DuckDuckGo (no tracking)
- **Content Scraping**: Extracts detailed information from top results
- **LLM Analysis**: Synthesizes information from multiple sources
- **Source Attribution**: Maintains links to original sources

#### Web Search Configuration
```json
{
  "web_search": {
    "max_results": 5,
    "max_scrape_results": 3,
    "timeout_seconds": 10,
    "scrape_timeout_seconds": 15,
    "max_content_length": 3000
  }
}
```

### Python Code Execution

The assistant can write and run Python on request - "write me a script that renames these files", "what does this print". Not a real sandbox (no container, no resource limits beyond a timeout) - the trust model is your own request on your own machine, with two real safety measures instead:

- **Write is instant, run is gated**: Saving a script (`write_code_file`) needs no confirmation - a file on disk can't do anything by itself. Actually running code goes through `propose_code_run` (stages it, describes what it'll do, doesn't execute) then `confirm_code_run` (actually runs it) - the assistant always describes what it's about to run and waits for you to say yes before calling `confirm_code_run`.
- **The confirmation gate is enforced in code, not just prompted**: the LLM agent loop can chain several tool calls together within a single turn before you get to say anything - so a system-prompt instruction alone ("ask before running") isn't a real guarantee a 7B model won't occasionally skip. `confirm_code_run` refuses to run anything staged less than `coding.min_confirm_gap_seconds` ago (default 3s) - a same-turn propose-then-confirm chain happens in milliseconds (LLM inference only), while a real confirmation always takes longer (the question has to be spoken via TTS, then you have to hear it and reply, then STT has to process your answer). A stale proposal older than `coding.max_confirm_gap_seconds` (default 5 minutes) is refused too, so a leftover "yes" long after the fact can't trigger old code.
- **Execution limits**: a subprocess timeout (`coding.execution_timeout_seconds`, default 10s) and an output length cap (`coding.max_output_length`, default 1500 chars, since TTS reading back a huge wall of output isn't useful).
- Saved scripts live in `scripts/` (gitignored, created automatically) - filenames are restricted to a plain `name.py` pattern, no subfolders or path traversal.

#### Coding Configuration
```json
{
  "coding": {
    "execution_timeout_seconds": 10,
    "max_output_length": 1500,
    "min_confirm_gap_seconds": 3.0,
    "max_confirm_gap_seconds": 300.0
  }
}
```

### Text-to-Speech: Kokoro (default) or Piper

Two interchangeable TTS engines, picked via `tts.engine` - `interruptible_tts.py` builds whichever is configured and falls back to Piper automatically if Kokoro can't actually be used (package not installed, model download failed), so the assistant doesn't go silent over a TTS engine problem.

- **Kokoro** (`kokoro_tts.py`, default): an 82M-parameter StyleTTS2-based model - noticeably more natural than Piper (third-party benchmarks put it around 4.2 MOS, close to real narration quality) for a similar hardware footprint (~2-3GB VRAM or CPU-only). Needs `pip install kokoro-onnx` (see requirements.txt) plus its ONNX model + voice-pack files, which download automatically on first run (~88MB for the default `int8` variant) into `kokoro/models/`.
- **Piper** (`piper_tts.py`): smaller and faster (near-instant first audio), but audibly more robotic. Still available as `tts.engine: "piper"`, or as the automatic fallback if Kokoro isn't set up.

Both share the same behavior:
- **Streamed, sentence-by-sentence**: The assistant starts speaking as soon as the LLM finishes each sentence, instead of waiting for the whole response to generate - noticeably cuts the silence before you hear anything, especially on longer answers
- **In-process playback**: synthesized audio plays directly via `sounddevice`, no temp files or separate player subprocess per chunk
- **Interrupt Support**: `sd.stop()` halts audio immediately mid-sentence, not just at the next chunk boundary
- **Automatic Setup**: downloads whatever model files it needs on first run

#### TTS Configuration
```json
{
  "tts": {
    "engine": "kokoro",
    "piper": {
      "voice": "en_GB-southern_english_female-low"
    },
    "kokoro": {
      "model_variant": "int8",
      "voice": "bf_emma",
      "speed": 1.0,
      "lang": "en-gb"
    }
  }
}
```
`kokoro.model_variant` is `int8` (88MB, default), `fp16` (169MB) or `f32` (310MB, highest quality) - all trade download size and inference speed for fidelity. `kokoro.voice` picks from Kokoro's built-in voice packs (British: `bf_alice`/`bf_emma`/`bf_isabella`/`bf_lily` female, `bm_daniel`/`bm_fable`/`bm_george`/`bm_lewis` male; American voices use the `af_`/`am_` prefix instead, e.g. `af_heart`).

### Silent Light Control

The assistant uses **"silent success, noisy failure"** principle:
- **Successful Commands**: No verbal feedback (light control happens silently)
- **Error Messages**: Clear feedback when operations fail
- **Natural UX**: Like a good human assistant - quiet when things work

### Interrupt Functionality

#### Features:
- **Real-time listening**: Continuously monitors for interrupt commands
- **Voice Interrupt Detection**: Background processing in separate thread
- **LLM Response Interruption**: Can terminate long-running generations
- **Sentence-Level Speech**: Responses are spoken (and can be interrupted) one sentence at a time, streamed in as the LLM generates them rather than split by an arbitrary character count
- **Clean Resource Management**: Proper cleanup of audio and process resources

#### Configuration:
```python
self.interrupt_words = ["stop", "pause", "wait", "interrupt", "hold on", "quiet"]
```

## 📁 Project Structure

```
Assistant/
├── main.py                     # Main application entry point
├── voice_recognition.py        # Speech recognition and wake word detection
├── llm_interface.py           # Ollama LLM integration (agent loop, tool-calling)
├── ollama_client.py           # Ollama HTTP API client (streaming chat/embed)
├── tools.py                   # Tool schemas + dispatch for the agent
├── sentence_stream.py         # Sentence-boundary splitting for streamed TTS
├── commands.py                # Command implementations
├── interruptible_tts.py       # Text-to-speech with interrupt capability
├── calendar_interface.py      # Google Calendar integration
├── enhanced_memory.py         # Conversation memory + semantic search (memory.db)
├── settings_gui.py            # Standalone config-editing GUI
├── launch_settings.py         # Launcher for settings_gui.py
├── tapo_light_wrapper.py      # Tapo smart light control
├── iot_manager.py            # IoT device management
├── iot_commands.py           # IoT command processing
├── kokoro_tts.py             # Kokoro TTS implementation (default engine)
├── piper_tts.py             # Piper TTS implementation (fallback engine)
├── web_search.py            # Web search functionality
├── smart_event_times.py     # Smart calendar time suggestions
├── notion_interface.py      # Notion API integration
├── spotify_interface.py     # Spotify integration
├── navidrome_interface.py    # Navidrome/Subsonic API client (library search + stream URLs)
├── chromecast_interface.py   # Chromecast discovery/casting for room-targeted playback
├── calendar_cache_sync.py   # Local calendar caching + background sync with Google
├── local_calendar_db.py     # SQLite-backed local calendar cache
├── code_execution.py        # Python code writing/execution (propose-then-confirm gated)
├── scripts/                 # Saved/generated scripts (gitignored)
├── config.json             # Configuration file
└── README.md               # This comprehensive guide
```

## ⚙️ Configuration

### Voice Recognition
- Wake word: "Jarvis" (configurable)
- Model path: `models/vosk-model-small-en-us-0.15`
- Interrupt detection: 50ms polling interval
- Configurable in `config.json` under `voice`:
  - `command_timeout`: How long to wait for a command right after the wake word, default 10s
  - `follow_up_timeout`: How long to wait in silence after each reply before requiring the wake word again, default 5s - this is what lets you answer a clarifying question ("For how long?" → "five minutes") or keep talking without saying "Jarvis" every time. It's a silence timer, not a hard cutoff: as long as you're actively talking it keeps extending, so a long sentence isn't cut off - only a full `follow_up_timeout` seconds of actual silence falls back to wake-word mode.
  - `wake_word_timeout`: Only read by the old GUI settings screens - the core voice loop's wake-word listening blocks indefinitely and doesn't use this value

### LLM Settings
All configurable in `config.json` under `llm`:
- `model`: Default `qwen2.5:7b-instruct` (via Ollama) - needs tool-calling support
- `host`: Ollama server URL, default `http://localhost:11434`
- `timeout_seconds`: Per-call timeout, default 60
- `keep_alive`: How long Ollama keeps the model loaded between calls, default `10m`
- `num_ctx`: Context window size, default 4096
- `max_history_messages`: How many recent chat turns stay in the live conversation
- `agent_max_rounds`: Max chained tool-calling rounds per request, default 4
- `system_prompt`: Optional override for the assistant's personality/instructions

### Memory System
- Database: `memory.db` (SQLite - despite the old filename, this was never actually JSON) - not tracked in git, see `.gitignore`
- Semantic search via `nomic-embed-text` embeddings, with keyword fallback - see `llm.embed_model` above
- Context limits: Configurable per memory type
- Dated events (birthdays, anniversaries, appointments) live in a separate `events` table with a real date column and optional yearly recurrence - see `memory.reminder_window_days` above

### Audio Settings
- TTS: Piper neural synthesis
- Voice: British English female
- Audio format: raw 16-bit PCM piped directly to `sounddevice` (no intermediate WAV file)
- Chunking: sentence-level, streamed in as the LLM generates each one

## 📋 Requirements

See `requirements.txt` for the full, up-to-date dependency list - install with `pip install -r requirements.txt`.

## 🚨 Troubleshooting

### Common Issues

#### 1. Voice Recognition Not Working
- Check microphone permissions and system settings
- Verify Vosk model is downloaded correctly
- Test microphone with other applications
- Run audio diagnostics

#### 2. Ollama Connection Failed
- Ensure Ollama is running: `ollama serve`
- Check if the configured model is installed: `ollama list` (should show `qwen2.5:7b-instruct`, or whatever `llm.model` is set to)
- Verify network connectivity to Ollama

#### 3. Tapo Light Control Issues
- Verify devices are powered on and connected to WiFi
- Check IP addresses in configuration
- Test with diagnostic tools: `python tapo_debug_test.py`
- Ensure Tapo credentials are correct

#### 4. Calendar Integration Issues
- Verify `credentials.json` is present
- Check Google Calendar API is enabled
- Ensure proper OAuth scopes and token refresh

#### 5. Web Search Problems
- Check internet connection
- Verify DuckDuckGo accessibility
- Review search configuration and timeouts

#### 6. Import Errors
- Install all requirements: `pip install -r requirements.txt`
- Check Python version (3.7+)
- Verify all model files are downloaded

### Diagnostic Tools

```bash
# Run comprehensive system check
python -c "from tapo_debug_test import *; main()"

# Test audio system
python test_audio_format.py

# Test TTS system
python test_piper_optimization.py

# Test memory system
python -c "from enhanced_memory import EnhancedMemory; m = EnhancedMemory(); print(m.get_memory_stats()); m.close()"
```

## 📊 System Status

### Known Working Features ✅
- Voice recognition and wake word detection
- Interrupt functionality (stop mid-response)
- TTS with natural British English voice
- Memory system with contextual search
- Calendar integration with smart times
- Weather information
- Timer functionality
- Web search with DuckDuckGo
- Tapo smart light control
- Spotify integration
- Settings GUI
- Text assistant interface

### Configuration Status 🔧
- **Voice Model**: Vosk English model (downloaded)
- **LLM**: Qwen2.5 7B Instruct via Ollama (local, tool-calling enabled)
- **TTS**: Piper with British female voice (auto-downloaded)
- **Calendar**: Google Calendar (requires credentials)
- **Music**: Spotify (requires authentication)
- **Smart Home**: Tapo L530 lights (configured)
- **Search**: DuckDuckGo (working)

## 🔮 Recent Improvements & Enhancements

### ✅ **Successfully Implemented**
- **Piper TTS Integration**: High-quality neural text-to-speech synthesis
- **Smart Home Control**: Full Tapo light integration with voice commands
- **Web Search Capabilities**: Real-time search with intelligent result processing
- **Enhanced Memory System**: Advanced contextual search and categorization
- **Smart Event Times**: Automatic time suggestions for calendar events
- **Interrupt Functionality**: Comprehensive interruption of responses and processing
- **GUI Interface**: Modern settings and device management interface
- **Silent Light Control**: Natural UX with quiet success, noisy failure
- **Notion Integration**: Task and note management
- **Weather Integration**: Real-time weather data
- **Spotify Control**: Music playback management

### 🎯 **Performance Optimizations**
- Optimized interrupt detection (50ms polling)
- Enhanced error handling and timeouts
- Cleaned up imports and dependencies
- Added NLTK fallback tokenizer
- Improved memory search algorithms
- Better calendar integration
- Efficient async/sync bridging for IoT devices

## 🌐 Platform Support

### **Fully Supported**
- **Windows 10/11**: Primary platform with full feature support
- **Python 3.7+**: Core language requirement
- **Local LLM**: Ollama integration for privacy

### **Partially Supported**
- **macOS**: Core features work, some audio optimizations may differ
- **Linux**: Basic functionality, GUI may require additional dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM capabilities
- [Vosk](https://alphacephei.com/vosk/) for speech recognition
- [Piper TTS](https://github.com/rhasspy/piper) by the Rhasspy team for high-quality neural text-to-speech
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for music integration
- [Open-Meteo](https://open-meteo.com/) for weather data
- [DuckDuckGo](https://duckduckgo.com/) for privacy-focused web search
- Google Calendar API for calendar integration
- [Tapo Python Library](https://github.com/petermb/tapo) for smart home control

## 📜 License

This project is **commercial software** and is proprietary. All rights reserved.

### Commercial Use
- This software is intended for commercial use and distribution
- Unauthorized reproduction, distribution, or modification is prohibited
- For licensing inquiries, please contact the project maintainers

### Third-Party Components
This software incorporates several open-source components under their respective licenses:
- **Piper TTS**: MIT License - Copyright (c) 2023 Michael Hansen (Rhasspy)
- **Vosk**: Apache License 2.0
- **Ollama**: MIT License
- **Other dependencies**: See individual package licenses in `requirements.txt`

---

**Note**: This assistant runs entirely locally for privacy. Your conversations and data never leave your machine unless you explicitly use online services (weather, calendar, Spotify, web search). The LLM runs locally via Ollama, ensuring your data remains private.

## 🔗 Quick Reference

### **Start Commands**
- Main Assistant: `python main.py`
- Settings GUI: `python settings_gui.py` (or `python launch_settings.py`)

### **Test Commands**
- Full System Test: `python test_improvements.py`
- IoT Control Test: `python test_smart_bulb_integration.py`
- Audio Test: `python test_audio_format.py`
- Memory Test: `python -c "from enhanced_memory import EnhancedMemory; m = EnhancedMemory(); print(m.get_memory_stats()); m.close()"`

### **Configuration Files**
- Main Config: `config.json`
- Calendar Credentials: `credentials.json`
- Memory Data: `memory.db` (SQLite, gitignored)
- Spotify Cache: `.spotify_cache`

### **Model Files**
- Voice Recognition: `models/vosk-model-small-en-us-0.15/`
- TTS Voice Models: `piper/models/`
- Ollama Models: Run `ollama list` to see installed models

This comprehensive documentation covers all features, setup instructions, and troubleshooting for the AI Voice Assistant. The system is designed to be intuitive, privacy-focused, and highly capable for both personal and commercial use.
