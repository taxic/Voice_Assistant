# AI Voice Assistant

A sophisticated voice-controlled AI assistant with advanced memory capabilities, Spotify integration, web search, enhanced memory system, interrupt functionality, and modern GUI interface. Built with Python and powered by local LLM (Ollama) for privacy and offline operation.

## 🚀 Features

- **Voice Recognition**: Wake word detection and command processing
- **Enhanced Memory System**: Advanced contextual conversation memory with intelligent categorization and search
- **Piper TTS**: High-quality neural text-to-speech synthesis
- **Spotify Integration**: Music control and playlist management
- **Web Search**: Real-time web search capabilities with intelligent result processing
- **GUI Interface**: Modern graphical user interface for enhanced interaction
- **Calendar Integration**: Google Calendar events management
- **Weather Information**: Real-time weather data via Open-Meteo API
- **Timer Functionality**: Set and manage countdowns
- **Interrupt Capability**: Stop the assistant mid-response
- **Intent Recognition**: Smart LLM-powered command understanding

## 🛠️ Technology Stack

- **Python 3.7+**
- **Ollama** (Local LLM - Mistral)
- **Vosk** (Speech Recognition)
- **Piper TTS** (Neural Text-to-Speech)
- **Spotify Web API** (Music Integration)
- **Web Search APIs** (Real-time search capabilities)
- **Tkinter/PyQt** (GUI Framework)
- **Google Calendar API**
- **SQLite** (Enhanced Memory Storage)
- **Open-Meteo API** (Weather Data)

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

### Ollama Setup

```bash
ollama pull mistral
```

## 🎯 Usage

### Basic Usage

```bash
python main.py
```

Say the wake word "Jarvis" and then give your command.

### Example Commands

- **Weather**: "What's the weather like in London?"
- **Calendar**: "Schedule a meeting tomorrow at 3 PM"
- **Timer**: "Set a timer for 15 minutes"
- **Memory**: "What did we discuss about the project?"
- **Spotify**: "Play my workout playlist" or "Skip to the next song"
- **Web Search**: "Search for the latest Python tutorials"
- **Time**: "What time is it?"
- **General**: "Tell me about Python programming"

### Interrupt Commands

You can interrupt the assistant at any time by saying:
- "Stop"
- "Pause" 
- "Wait"
- "Interrupt"
- "Hold on"
- "Quiet"

## 📁 Project Structure

```
Assistant/
├── main.py                 # Main application entry point
├── voice_recognition.py    # Speech recognition and wake word detection
├── llm_interface.py        # Ollama LLM integration
├── memory.py              # Conversation memory management
├── commands.py            # Command implementations (weather, time, etc.)
├── interruptible_tts.py   # Text-to-speech with interrupt capability
├── intent_parser.py       # Intent classification and parsing
├── command_parser.py      # Command parsing utilities
├── calendar_interface.py  # Google Calendar integration
├── test_improvements.py   # Testing script for improvements
├── test_interrupt.py      # Interrupt functionality tests
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🧪 Testing

### Test Intent Parsing
```bash
python test_improvements.py
```

### Test Interrupt Functionality
```bash
python test_interrupt.py
```

## ⚙️ Configuration

### Voice Recognition
- Wake word: "Jarvis" (configurable in `voice_recognition.py`)
- Model path: `models/vosk-model-small-en-us-0.15`

### LLM Settings
- Default model: Mistral (via Ollama)
- Timeout: 30 seconds
- Configurable in `llm_interface.py`

### Memory
- Database: `memory.db` (SQLite)
- Context limit: 5 recent interactions
- Automatic cleanup and categorization

## 🔧 Advanced Features

### Memory System
The assistant maintains conversation context using:
- **Recent Memory**: Last 5 interactions
- **Contextual Search**: Semantic search through conversation history
- **Categorized Storage**: Different types of interactions (weather, calendar, etc.)

### Intent Recognition
Dual-mode intent parsing:
1. **LLM-based**: Semantic understanding via Mistral
2. **Keyword-based**: Fallback pattern matching

### Interrupt Handling
Real-time interrupt detection:
- Background voice monitoring
- Process termination capabilities
- Graceful response handling

## 📋 Requirements

Create a `requirements.txt` file:

```
vosk==0.3.45
sounddevice==0.4.6
pyttsx3==2.90
requests==2.31.0
dateparser==1.1.8
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
pytz==2023.3
nltk==3.8.1
sqlite3
```

## 🚨 Troubleshooting

### Common Issues

1. **Voice Recognition Not Working**
   - Check microphone permissions
   - Verify Vosk model is downloaded correctly
   - Test microphone with other applications

2. **Ollama Connection Failed**
   - Ensure Ollama is running: `ollama serve`
   - Check if Mistral model is installed: `ollama list`

3. **Calendar Integration Issues**
   - Verify `credentials.json` is present
   - Check Google Calendar API is enabled
   - Ensure proper OAuth scopes

4. **Import Errors**
   - Install all requirements: `pip install -r requirements.txt`
   - Check Python version (3.7+)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Recent Improvements

- ✅ **Piper TTS Integration**: High-quality neural text-to-speech synthesis
- ✅ **Spotify Integration**: Complete music control and playlist management
- ✅ **Web Search Capabilities**: Real-time web search with intelligent result processing
- ✅ **Enhanced Memory System**: Advanced contextual search and categorization
- ✅ **GUI Interface**: Modern graphical user interface for enhanced interaction
- ✅ Optimized interrupt detection (50ms polling)
- ✅ Enhanced error handling and timeouts
- ✅ Cleaned up imports and dependencies
- ✅ Added NLTK fallback tokenizer
- ✅ Improved memory search algorithms
- ✅ Better calendar integration

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM capabilities
- [Vosk](https://alphacephei.com/vosk/) for speech recognition
- [Piper TTS](https://github.com/rhasspy/piper) by the Rhasspy team for high-quality neural text-to-speech
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for music integration
- [Open-Meteo](https://open-meteo.com/) for weather data
- Google Calendar API for calendar integration

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Plugin system for custom commands  
- [ ] Web interface for configuration
- [ ] Smart home integration
- [ ] Voice training for better recognition
- [ ] Encrypted conversation storage

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

**Note**: This assistant runs entirely locally for privacy. Your conversations and data never leave your machine unless you explicitly use online services (weather, calendar, Spotify, web search).
