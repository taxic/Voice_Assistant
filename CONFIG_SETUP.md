# Configuration Setup Guide

Your assistant now uses a centralized configuration system that makes it easy to customize settings without modifying code files.

## Configuration File Structure

The `config.json` file contains all configurable settings organized into logical sections:

### LLM Settings (`llm`)
- `model`: Ollama model to use (default: "mistral")
- `timeout_seconds`: Maximum time to wait for LLM responses (default: 30)
- `ollama_command`: Command to run Ollama (default: "ollama")

### Weather Settings (`weather`)
- `default_location`: Default location for weather queries (default: "Guildford")
- `geocoding_api_url`: URL for location geocoding service
- `weather_api_url`: URL for weather data service
- `timeout_seconds`: Timeout for weather API requests (default: 10)

### Calendar Settings (`calendar`)
- `scopes`: Google Calendar API scopes
- `credentials_file`: Path to Google credentials file (default: "credentials.json")
- `token_file`: Path to token file (default: "token.pickle")  
- `timezone`: Default timezone (default: "Europe/London")

### Spotify Settings (`spotify`)
- `client_id_env`: Environment variable name for Spotify client ID
- `client_secret_env`: Environment variable name for Spotify client secret
- `redirect_uri_env`: Environment variable name for redirect URI
- `default_redirect_uri`: Default redirect URI
- `scopes`: Spotify API scopes
- `cache_file`: Path to Spotify auth cache file

### Jokes Settings (`jokes`)
- `api_url`: URL for joke API
- `timeout_seconds`: Timeout for joke API requests
- `fallback_jokes`: Array of backup jokes if API fails

### Voice Settings (`voice`)
- `wake_word_timeout`: Timeout for wake word detection
- `command_timeout`: Timeout for command listening
- `interrupt_check_interval`: How often to check for interrupts

### Memory Settings (`memory`)
- `max_recent_interactions`: Number of recent interactions to keep in context
- `contextual_search_limit`: Number of contextual memories to include

### Assistant Settings (`assistant`)
- `name`: Assistant name for display
- `version`: Assistant version
- `interrupt_phrases`: List of phrases that trigger interrupts

### Path Settings (`paths`)
- `config_file`: Path to configuration file
- `memory_file`: Path to memory file
- `logs_directory`: Directory for log files

## Customizing Your Configuration

### 1. Basic Customization

Edit `config.json` to change settings:

```json
{
  "llm": {
    "model": "llama2",
    "timeout_seconds": 45
  },
  "weather": {
    "default_location": "London"
  },
  "assistant": {
    "name": "MyAssistant",
    "version": "1.1.0"
  }
}
```

### 2. Advanced Customization

You can modify any setting in the configuration file. The assistant will automatically use your custom values.

#### Change Default Weather Location
```json
{
  "weather": {
    "default_location": "New York"
  }
}
```

#### Use Different LLM Model
```json
{
  "llm": {
    "model": "codellama",
    "timeout_seconds": 60
  }
}
```

#### Customize Interrupt Phrases
```json
{
  "assistant": {
    "interrupt_phrases": [
      "stop", "pause", "halt", "quiet", "enough", "cancel"
    ]
  }
}
```

#### Change Memory Limits
```json
{
  "memory": {
    "max_recent_interactions": 10,
    "contextual_search_limit": 5
  }
}
```

### 3. Environment-Specific Configurations

You can create different config files for different environments:

- `config.json` - Production config
- `config-dev.json` - Development config
- `config-test.json` - Testing config

To use a different config file, you can modify the `config_manager.py` or create environment-specific startup scripts.

## Configuration Benefits

### 1. **No Code Changes Required**
- Modify settings without touching Python code
- Safer than hardcoded values
- Easy to maintain and version control

### 2. **Centralized Management**
- All settings in one place
- Easy to backup and restore
- Clear overview of all configurable options

### 3. **Default Fallbacks**
- If config file is missing or corrupted, defaults are used
- Individual missing values fall back to sensible defaults
- Robust error handling

### 4. **Easy Deployment**
- Different configurations for different environments
- Simple to customize for different users
- No need to modify source code

## Configuration Validation

The system includes automatic validation:

- **File Not Found**: Uses built-in defaults
- **Invalid JSON**: Falls back to defaults with error message
- **Missing Keys**: Uses default values for missing settings
- **Invalid Values**: Type checking and sensible limits

## Backup and Migration

### Backing Up Configuration
```bash
cp config.json config-backup.json
```

### Restoring Configuration
```bash
cp config-backup.json config.json
```

### Migration Between Versions
The configuration system is designed to be backward compatible. New versions may add new settings, but existing configurations will continue to work.

## Troubleshooting

### Config Not Loading
1. Check that `config.json` exists in the assistant directory
2. Verify JSON syntax with a JSON validator
3. Check console output for error messages

### Settings Not Taking Effect
1. Restart the assistant after changing configuration
2. Verify the setting name matches the documentation
3. Check data types (strings vs numbers vs arrays)

### Reset to Defaults
Delete or rename `config.json` - the assistant will use built-in defaults and you can create a new config file.

## Security Considerations

### Sensitive Information
- **Never** put API keys or passwords in `config.json`
- Use environment variables for secrets (like Spotify credentials)
- Add `config.json` to `.gitignore` if it contains sensitive data

### File Permissions
Ensure `config.json` has appropriate file permissions:
```bash
chmod 600 config.json  # Read/write for owner only
```

## Example Complete Configuration

Here's a complete example `config.json` with custom settings:

```json
{
  "llm": {
    "model": "mistral:7b",
    "timeout_seconds": 45,
    "ollama_command": "ollama"
  },
  "weather": {
    "default_location": "London",
    "timeout_seconds": 15
  },
  "calendar": {
    "timezone": "America/New_York"
  },
  "jokes": {
    "timeout_seconds": 3,
    "fallback_jokes": [
      "Custom joke 1",
      "Custom joke 2"
    ]
  },
  "assistant": {
    "name": "PersonalAssistant",
    "version": "2.0.0",
    "interrupt_phrases": [
      "stop", "pause", "quiet", "enough"
    ]
  },
  "memory": {
    "max_recent_interactions": 8,
    "contextual_search_limit": 4
  }
}
```

This configuration system makes your assistant highly customizable while maintaining code simplicity and reliability.
