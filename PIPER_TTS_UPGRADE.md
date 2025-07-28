# Piper TTS Upgrade Documentation

## Overview

The Assistant has been successfully upgraded from the robotic-sounding `pyttsx3` TTS engine to the much more natural-sounding **Piper TTS** system. This upgrade provides:

- **Natural sounding voices** with neural network-based speech synthesis
- **Better voice quality** compared to the previous robotic voice
- **Maintained compatibility** with all existing functionality including interrupts
- **Automatic setup** - downloads required components on first run

## What Changed

### Files Modified
- `requirements.txt` - Updated dependencies (removed pyttsx3, added audio libraries)
- `interruptible_tts.py` - Updated to use Piper TTS backend
- `config.json` - Added Piper TTS configuration section

### Files Added
- `piper_tts.py` - New Piper TTS implementation with full functionality
- `test_piper.py` - Test script for Piper TTS
- `test_integration.py` - Integration test script

## Features

### Voice Quality
- Uses the `en_US-lessac-medium` voice model by default
- Natural prosody and intonation 
- Clear pronunciation and speech rhythm
- Much more pleasant to listen to than the previous robotic voice

### Compatibility
- **Full backward compatibility** - no changes needed to existing code
- Same API as the previous InterruptibleTTS class
- All interrupt functionality preserved
- Same configuration options

### Automatic Setup
- Downloads Piper executable automatically on first run (~6MB)
- Downloads voice model automatically (~17MB)
- Creates necessary directory structure
- Handles Windows-specific audio playback

## Configuration

The new TTS system can be configured in `config.json`:

```json
{
  \"tts\": {
    \"engine\": \"piper\",
    \"piper\": {
      \"voice\": \"en_US-lessac-medium\",
      \"download_models\": true,
      \"models_dir\": \"piper/models\",
      \"chunk_size\": 50
    }
  }
}
```

## Available Voice Models

The system currently uses `en_US-lessac-medium` but can be extended to support other voices:

- `en_US-lessac-low` - Faster, smaller model
- `en_US-lessac-high` - Higher quality, larger model
- Additional voices available from the Piper voices repository

## Testing

Two test scripts are provided:

### Basic Test
```bash
python test_piper.py
```
Tests the core Piper TTS functionality.

### Integration Test
```bash
python test_integration.py
```
Tests the integration with the existing InterruptibleTTS interface.

## Technical Details

### Architecture
- `PiperTTS` class handles the core TTS functionality
- `InterruptibleTTS` class provides backward compatibility
- Audio playback uses Windows PowerShell Media.SoundPlayer
- Text chunking for responsive interrupts maintained

### Dependencies
- `numpy` - Audio processing
- `simpleaudio` - Audio playback support
- `requests` - Download voice models and executable
- Standard library modules for subprocess, file handling

### File Structure
```
piper/
├── piper/
│   └── piper.exe           # Piper TTS executable
└── models/
    ├── en_US-lessac-medium.onnx      # Voice model
    └── en_US-lessac-medium.onnx.json # Model configuration
```

## Troubleshooting

### Audio Issues
If you experience audio problems:
1. Check Windows audio settings
2. Ensure no other audio applications are blocking playback
3. Try restarting the application

### Model Download Issues  
If voice model downloads fail:
1. Check internet connection
2. Manually delete the `piper` folder and restart
3. Check firewall/antivirus settings

### Performance
- First synthesis may be slower due to model loading
- Subsequent synthesis should be fast
- Voice models are cached locally after first download

## Voice Comparison

**Before (pyttsx3):**
- Robotic, mechanical voice
- Limited naturalness
- Basic prosody

**After (Piper TTS):**
- Natural human-like voice
- Proper intonation and rhythm  
- Professional speech quality
- Much more pleasant listening experience

## Future Enhancements

Potential improvements for future versions:
- Support for multiple voice models
- Voice selection from config
- Speed/pitch adjustment options
- Additional language support
- Real-time voice switching

---

**Status:** ✅ Successfully implemented and tested
**Compatibility:** ✅ Full backward compatibility maintained  
**Quality:** ✅ Significant improvement over previous TTS system
