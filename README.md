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

### Ollama Setup

```bash
ollama pull qwen2.5:7b-instruct
```

This is the default model (`llm.model` in `config.json`), chosen to fit comfortably in 6GB of VRAM (~4.7GB at Q4_K_M) while still supporting native tool/function calling, which the assistant relies on. If you have more VRAM to spare, a larger Qwen2.5 or Llama 3.3 model will reason better - just `ollama pull` it and update `llm.model` to match.

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

**Music Control:**
- "Play my workout playlist"
- "Skip to the next song"
- "Pause the music"
- "Turn up the volume"

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
- **Contextual Search**: Semantic search through conversation history
- **Categorized Storage**: Different types of interactions (weather, calendar, etc.)
- **Importance Scoring**: Automatic prioritization of important information
- **Auto-summarization**: Memory compression for long conversations

#### Memory Configuration
```json
{
  "memory": {
    "max_recent_interactions": 5,
    "contextual_search_limit": 3,
    "short_term_max_items": 50,
    "short_term_context_limit": 10,
    "long_term_context_limit": 5,
    "long_term_threshold": 7,
    "importance_decay_days": 30,
    "auto_summarize_threshold": 100
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
    "max_content_length": 3000,
    "delay_between_requests": 2
  }
}
```

### Piper TTS (Text-to-Speech)

- **Natural Voices**: Neural network-based speech synthesis
- **British English**: Default voice is `en_GB-southern_english_female-low`
- **Interrupt Support**: Can be stopped mid-sentence
- **Automatic Setup**: Downloads voice models on first run

#### TTS Configuration
```json
{
  "tts": {
    "engine": "piper",
    "piper": {
      "voice": "en_GB-southern_english_female-low",
      "download_models": true,
      "models_dir": "piper/models",
      "chunk_size": 50
    }
  }
}
```

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
- **Chunked Speech**: Long responses broken into smaller chunks
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
├── llm_interface.py           # Ollama LLM integration
├── commands.py                # Command implementations
├── interruptible_tts.py       # Text-to-speech with interrupt capability
├── intent_parser.py           # Intent classification and parsing
├── command_parser.py          # Command parsing utilities
├── calendar_interface.py      # Google Calendar integration
├── memory.py                  # Conversation memory management
├── settings_gui.py            # Settings and device management GUI
├── tapo_light_wrapper.py      # Tapo smart light control
├── iot_manager.py            # IoT device management
├── iot_commands.py           # IoT command processing
├── piper_tts.py             # Piper TTS implementation
├── web_search.py            # Web search functionality
├── memory_system.py         # Enhanced memory system
├── smart_event_times.py     # Smart calendar time suggestions
├── notion_interface.py      # Notion API integration
├── spotify_interface.py     # Spotify integration
├── weather_interface.py     # Weather data interface
├── unified_calendar.py      # Calendar management
├── test_*.py               # Test files for various features
├── config.json             # Configuration file
└── README.md               # This comprehensive guide
```

## 🧪 Testing

### Test Core Functionality
```bash
python test_improvements.py
```

### Test Interrupt Functionality
```bash
python test_interrupt.py
```

### Test Smart Home Integration
```bash
python test_smart_bulb_integration.py
```

### Test Calendar Features
```bash
python test_calendar_gui.py
```

### Test Web Search
```bash
python test_web_search.py
```

## ⚙️ Configuration

### Voice Recognition
- Wake word: "Jarvis" (configurable)
- Model path: `models/vosk-model-small-en-us-0.15`
- Interrupt detection: 50ms polling interval

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
- Database: `memory.json` (JSON storage)
- Context limits: Configurable per memory type
- Automatic cleanup and categorization

### Audio Settings
- TTS: Piper neural synthesis
- Voice: British English female
- Audio format: WAV, optimized for Windows
- Chunk size: 50 characters for responsive interrupts

## 📋 Requirements

Create a `requirements.txt` file with dependencies:

```
vosk==0.3.45
sounddevice==0.4.6
requests==2.31.0
dateparser==1.1.8
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
pytz==2023.3
nltk==3.8.1
numpy==1.24.0
simpleaudio==1.0.4
beautifulsoup4==4.12.0
spotipy==2.22.0
notion-client==2.0.0
```

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
python -c "from memory_system import *; test_memory()"
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
- Settings GUI: `python settings_gui.py`
- Text Assistant: `python text_assistant_gui.py`

### **Test Commands**
- Full System Test: `python test_improvements.py`
- IoT Control Test: `python test_smart_bulb_integration.py`
- Audio Test: `python test_audio_format.py`
- Memory Test: `python -c "from memory_system import test_memory; test_memory()"`

### **Configuration Files**
- Main Config: `config.json`
- Calendar Credentials: `credentials.json`
- Memory Data: `memory.json`
- Spotify Cache: `.spotify_cache`

### **Model Files**
- Voice Recognition: `models/vosk-model-small-en-us-0.15/`
- TTS Voice Models: `piper/models/`
- Ollama Models: Run `ollama list` to see installed models

This comprehensive documentation covers all features, setup instructions, and troubleshooting for the AI Voice Assistant. The system is designed to be intuitive, privacy-focused, and highly capable for both personal and commercial use.
