#!/usr/bin/env python3
"""
Test script for settings functionality
"""

import os
import json
from config_manager import config

def test_settings_integration():
    """Test that settings can be loaded and modified"""
    print("=== Testing Settings Integration ===")
    print()
    
    # Test 1: Load current settings
    print("1. Testing configuration loading:")
    print(f"   Assistant Name: {config.get('assistant.name', 'N/A')}")
    print(f"   Weather Location: {config.get('weather.default_location', 'N/A')}")
    print(f"   LLM Model: {config.get('llm.model', 'N/A')}")
    print(f"   Memory Threshold: {config.get('memory.long_term_threshold', 'N/A')}")
    print()
    
    # Test 2: Check if config file exists and is readable
    print("2. Testing config file access:")
    try:
        with open('config.json', 'r') as f:
            config_data = json.load(f)
        print("   ✓ Config file readable")
        print(f"   ✓ Contains {len(config_data)} top-level sections")
    except Exception as e:
        print(f"   ✗ Config file error: {e}")
    print()
    
    # Test 3: Check environment variables
    print("3. Testing environment variables:")
    spotify_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if spotify_id:
        print(f"   ✓ SPOTIFY_CLIENT_ID is set (length: {len(spotify_id)})")
    else:
        print("   ✗ SPOTIFY_CLIENT_ID not set")
        
    if spotify_secret:
        print(f"   ✓ SPOTIFY_CLIENT_SECRET is set (length: {len(spotify_secret)})")
    else:
        print("   ✗ SPOTIFY_CLIENT_SECRET not set")
    print()
    
    # Test 4: Test backup and restore functionality
    print("4. Testing configuration modification:")
    original_name = config.get('assistant.name', 'Assistant')
    test_name = "TestAssistant"
    
    try:
        # Create modified config
        with open('config.json', 'r') as f:
            config_data = json.load(f)
        
        # Modify the name
        config_data['assistant']['name'] = test_name
        
        # Write back (this simulates what the settings GUI would do)
        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Reload config (simulate config reload)
        config._config = config_data
        
        # Verify change
        new_name = config.get('assistant.name')
        if new_name == test_name:
            print(f"   ✓ Successfully modified assistant name to '{test_name}'")
        else:
            print(f"   ✗ Failed to modify assistant name (got '{new_name}')")
        
        # Restore original
        config_data['assistant']['name'] = original_name
        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        config._config = config_data
        
        print(f"   ✓ Restored original name '{original_name}'")
        
    except Exception as e:
        print(f"   ✗ Configuration modification failed: {e}")
    print()
    
    # Test 5: Test settings that would be configurable
    print("5. Testing configurable settings:")
    
    settings_to_test = [
        ('assistant.name', 'Assistant Name'),
        ('weather.default_location', 'Weather Location'),
        ('llm.model', 'LLM Model'),
        ('llm.timeout_seconds', 'LLM Timeout'),
        ('memory.max_recent_interactions', 'Recent Interactions'),
        ('memory.short_term_max_items', 'Short-term Memory'),
        ('memory.long_term_threshold', 'Long-term Threshold'),
        ('calendar.timezone', 'Calendar Timezone'),
        ('web_search.max_results', 'Web Search Results'),
        ('voice.wake_word_timeout', 'Wake Word Timeout'),
    ]
    
    for setting_key, setting_name in settings_to_test:
        value = config.get(setting_key)
        if value is not None:
            print(f"   ✓ {setting_name}: {value}")
        else:
            print(f"   ✗ {setting_name}: Not found")
    
    print()
    print("=== Settings Test Complete ===")

def test_spotify_settings():
    """Test Spotify-specific settings"""
    print("=== Testing Spotify Settings ===")
    print()
    
    # Test environment variable detection
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    print("Environment Variables:")
    print(f"   SPOTIFY_CLIENT_ID: {'✓ Set' if client_id else '✗ Not set'}")
    print(f"   SPOTIFY_CLIENT_SECRET: {'✓ Set' if client_secret else '✗ Not set'}")
    print()
    
    # Test config settings
    spotify_config = config.get_section('spotify')
    print("Spotify Configuration:")
    for key, value in spotify_config.items():
        if 'secret' in key.lower():
            print(f"   {key}: [HIDDEN]")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Test setting environment variables programmatically
    print("Testing programmatic environment variable setting:")
    try:
        os.environ['SPOTIFY_CLIENT_ID'] = 'test_client_id'
        os.environ['SPOTIFY_CLIENT_SECRET'] = 'test_client_secret'
        
        new_id = os.getenv('SPOTIFY_CLIENT_ID')
        new_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if new_id == 'test_client_id' and new_secret == 'test_client_secret':
            print("   ✓ Successfully set environment variables")
        else:
            print("   ✗ Failed to set environment variables")
            
        # Clean up test values
        if client_id:
            os.environ['SPOTIFY_CLIENT_ID'] = client_id
        else:
            del os.environ['SPOTIFY_CLIENT_ID']
            
        if client_secret:
            os.environ['SPOTIFY_CLIENT_SECRET'] = client_secret
        else:
            del os.environ['SPOTIFY_CLIENT_SECRET']
            
    except Exception as e:
        print(f"   ✗ Environment variable test failed: {e}")
    
    print()

if __name__ == "__main__":
    test_settings_integration()
    test_spotify_settings()
