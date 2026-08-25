# config_manager.py

import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    """Centralized configuration management for the assistant"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = "config.json"):
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file '{config_path}' not found")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            print(f"[INFO] Configuration loaded from {config_path}")
            
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            print("[INFO] Using default configuration")
            self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in config file: {e}")
            print("[INFO] Using default configuration")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            print("[INFO] Using default configuration")
            self._config = self._get_default_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation (e.g., 'llm.model')
        
        Args:
            key_path: Dot-separated path to the config value
            default: Default value if key is not found
        
        Returns:
            Configuration value or default
        """
        if self._config is None:
            return default
        
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str, default: Any = None) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, default or {})
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        if self._config is None:
            self._config = {}
        
        keys = key_path.split('.')
        current = self._config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def save_config(self, config_path: str = "config.json"):
        """Save current configuration to file"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Configuration saved to {config_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
    
    def reload_config(self, config_path: str = "config.json"):
        """Reload configuration from file"""
        self._config = None
        self.load_config(config_path)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file loading fails"""
        return {
            "llm": {
                "model": "qwen2.5:7b-instruct",
                "host": "http://localhost:11434",
                "timeout_seconds": 60,
                "keep_alive": "10m",
                "num_ctx": 4096,
                "max_history_messages": 20,
                "agent_max_rounds": 4,
                "embed_model": "nomic-embed-text",
                "embed_timeout_seconds": 30
            },
            "weather": {
                "default_location": "Guildford",
                "geocoding_api_url": "https://geocoding-api.open-meteo.com/v1/search",
                "weather_api_url": "https://api.open-meteo.com/v1/forecast",
                "timeout_seconds": 10
            },
            "calendar": {
                "scopes": [
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/tasks"
                ],
                "credentials_file": "credentials.json",
                "token_file": "token.pickle",
                "timezone": "Europe/London"
            },
            "spotify": {
                "client_id_env": "SPOTIFY_CLIENT_ID",
                "client_secret_env": "SPOTIFY_CLIENT_SECRET",
                "redirect_uri_env": "SPOTIFY_REDIRECT_URI",
                "default_redirect_uri": "http://localhost:8888/callback",
                "scopes": "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,streaming",
                "cache_file": ".spotify_cache"
            },
            "jokes": {
                "api_url": "https://official-joke-api.appspot.com/random_joke",
                "timeout_seconds": 5,
                "fallback_jokes": [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "Why did the programmer quit his job? Because he didn't get arrays!",
                    "Why do programmers prefer dark mode? Because light attracts bugs!"
                ]
            },
            "voice": {
                "wake_word_timeout": 5.0,
                "command_timeout": 10.0,
                "interrupt_check_interval": 0.05
            },
            "memory": {
                "max_recent_interactions": 5,
                "contextual_search_limit": 3,
                "short_term_max_items": 50,
                "short_term_context_limit": 10,
                "long_term_context_limit": 5,
                "importance_decay_days": 30,
                "auto_summarize_threshold": 100
            },
            "assistant": {
                "name": "Assistant",
                "version": "1.0.0",
                "interrupt_phrases": [
                    "stop", "pause", "wait", "interrupt", "hold on", "quiet",
                    "shut up", "enough", "cancel", "nevermind", "never mind"
                ]
            },
            "web_search": {
                "max_results": 5,
                "max_scrape_results": 3,
                "timeout_seconds": 10,
                "scrape_timeout_seconds": 15,
                "max_content_length": 3000,
                "delay_between_requests": 2,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "paths": {
                "config_file": "config.json",
                "memory_file": "memory.db",
                "logs_directory": "logs"
            }
        }

# Global config instance for easy access
config = ConfigManager()
