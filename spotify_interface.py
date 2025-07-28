# spotify_interface.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
from typing import Optional, Dict, List
from config_manager import config

class SpotifyInterface:
    def __init__(self):
        """Initialize Spotify interface with authentication"""
        self.sp = None
        self.is_authenticated = False
        self._initialize_spotify()
    
    def _initialize_spotify(self):
        """Initialize Spotify API client with OAuth authentication"""
        try:
            # Get configuration values
            spotify_config = config.get_section('spotify')
            
            # Get credentials from environment variables
            client_id = os.getenv(spotify_config['client_id_env'])
            client_secret = os.getenv(spotify_config['client_secret_env'])
            redirect_uri = os.getenv(
                spotify_config['redirect_uri_env'], 
                spotify_config['default_redirect_uri']
            )
            
            if not client_id or not client_secret:
                env_vars = f"{spotify_config['client_id_env']} and {spotify_config['client_secret_env']}"
                print(f"[WARN] Spotify credentials not found. Please set {env_vars} environment variables.")
                return
            
            # Set up OAuth
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=spotify_config['scopes'],
                cache_path=spotify_config['cache_file']
            )
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection
            user = self.sp.current_user()
            if user:
                self.is_authenticated = True
                print(f"[INFO] Successfully authenticated with Spotify as {user['display_name']}")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Spotify: {e}")
            self.is_authenticated = False
    
    def search_track(self, query: str, limit: int = 10) -> Optional[Dict]:
        """Search for tracks on Spotify"""
        if not self.is_authenticated:
            return None
        
        try:
            results = self.sp.search(q=query, type='track', limit=limit)
            return results
        except Exception as e:
            print(f"[ERROR] Failed to search tracks: {e}")
            return None
    
    def play_track(self, track_uri: str) -> bool:
        """Play a specific track"""
        if not self.is_authenticated:
            return False
        
        try:
            # Get available devices
            devices = self.sp.devices()
            if not devices['devices']:
                return False
            
            # Use the first available device
            device_id = devices['devices'][0]['id']
            
            # Start playback
            self.sp.start_playback(device_id=device_id, uris=[track_uri])
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to play track: {e}")
            return False
    
    def queue_track(self, track_uri: str) -> bool:
        """Add a track to the playback queue"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.add_to_queue(track_uri)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to queue track: {e}")
            return False
    
    def pause_playback(self) -> bool:
        """Pause current playback"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.pause_playback()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to pause playback: {e}")
            return False
    
    def resume_playback(self) -> bool:
        """Resume current playback"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.start_playback()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to resume playback: {e}")
            return False
    
    def next_track(self) -> bool:
        """Skip to next track"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.next_track()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to skip track: {e}")
            return False
    
    def previous_track(self) -> bool:
        """Skip to previous track"""
        if not self.is_authenticated:
            return False
        
        try:
            self.sp.previous_track()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to go to previous track: {e}")
            return False
    
    def get_current_track(self) -> Optional[Dict]:
        """Get information about the currently playing track"""
        if not self.is_authenticated:
            return None
        
        try:
            current = self.sp.current_playback()
            return current
        except Exception as e:
            print(f"[ERROR] Failed to get current track: {e}")
            return None
    
    def set_volume(self, volume_percent: int) -> bool:
        """Set playback volume (0-100)"""
        if not self.is_authenticated:
            return False
        
        try:
            # Ensure volume is within valid range
            volume_percent = max(0, min(100, volume_percent))
            self.sp.volume(volume_percent)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set volume: {e}")
            return False
    
    def get_devices(self) -> Optional[List[Dict]]:
        """Get available Spotify devices"""
        if not self.is_authenticated:
            return None
        
        try:
            devices = self.sp.devices()
            return devices['devices']
        except Exception as e:
            print(f"[ERROR] Failed to get devices: {e}")
            return None
    
    def search_and_play(self, query: str, play_immediately: bool = True) -> str:
        """Search for a song and either play it immediately or queue it"""
        if not self.is_authenticated:
            return "Sorry, Spotify is not connected. Please check your authentication."
        
        # Search for the track
        results = self.search_track(query, limit=1)
        if not results or not results['tracks']['items']:
            return f"Sorry, I couldn't find any songs matching '{query}'."
        
        # Get the first result
        track = results['tracks']['items'][0]
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        track_uri = track['uri']
        
        # Check if we have active devices
        devices = self.get_devices()
        if not devices:
            return "Sorry, no Spotify devices are available. Please open Spotify on a device first."
        
        # Play or queue the track
        if play_immediately:
            success = self.play_track(track_uri)
            if success:
                return f"Now playing '{track_name}' by {artist_name}."
            else:
                return "Sorry, I couldn't start playback. Please make sure Spotify is running on a device."
        else:
            success = self.queue_track(track_uri)
            if success:
                return f"Added '{track_name}' by {artist_name} to your queue."
            else:
                return "Sorry, I couldn't add the song to your queue."
