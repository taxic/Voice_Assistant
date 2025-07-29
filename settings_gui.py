#!/usr/bin/env python3
"""
Settings GUI for the Enhanced Assistant
Allows users to configure various aspects of the assistant
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from datetime import datetime
from config_manager import config, ConfigManager
from spotify_interface import SpotifyInterface

class SettingsWindow:
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Assistant Settings")
        self.window.geometry("600x500")
        self.window.configure(bg='#2b2b2b')
        self.window.resizable(True, True)
        
        # Store original values for comparison
        self.original_values = {}
        self.changes_made = False
        
        # Initialize Spotify interface for testing
        self.spotify_interface = None
        
        self.setup_ui()
        self.load_current_settings()
        
        # Center the window
        self.center_window()
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Center the settings window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the settings user interface"""
        # Main container with scrollbar
        main_frame = tk.Frame(self.window, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Assistant Settings",
            font=('Arial', 18, 'bold'),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Configure notebook style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#2b2b2b')
        style.configure('TNotebook.Tab', padding=[12, 8])
        
        self.setup_general_tab()
        self.setup_spotify_tab()
        self.setup_weather_tab()
        self.setup_calendar_tab()
        self.setup_advanced_tab()
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Save button
        self.save_button = tk.Button(
            button_frame,
            text="Save Settings",
            command=self.save_settings,
            font=('Arial', 12, 'bold'),
            bg='#0078d4',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            cursor='hand2'
        )
        self.save_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_settings,
            font=('Arial', 12),
            bg='#404040',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            cursor='hand2'
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Reset to defaults button
        reset_button = tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            font=('Arial', 12),
            bg='#dc3545',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            cursor='hand2'
        )
        reset_button.pack(side=tk.LEFT)
    
    def create_tab_frame(self, parent, title):
        """Create a scrollable frame for a tab"""
        tab_frame = tk.Frame(parent, bg='#2b2b2b')
        
        # Create scrollable frame
        canvas = tk.Canvas(tab_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.notebook.add(tab_frame, text=title)
        return scrollable_frame
    
    def setup_general_tab(self):
        """Setup the general settings tab"""
        frame = self.create_tab_frame(self.notebook, "General")
        
        # Assistant Name
        self.create_setting_row(frame, "Assistant Name:", "assistant_name", "text", 
                               help_text="The name your assistant will use to identify itself")
        
        # Assistant Version (read-only)
        version_frame = tk.Frame(frame, bg='#2b2b2b')
        version_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(version_frame, text="Version:", font=('Arial', 10), 
                bg='#2b2b2b', fg='#ffffff', width=20, anchor='w').pack(side=tk.LEFT)
        
        version_label = tk.Label(version_frame, text=config.get('assistant.version', '1.0.0'),
                                font=('Arial', 10), bg='#404040', fg='#888888', 
                                relief=tk.FLAT, bd=1, padx=5, anchor='w')
        version_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # LLM Model
        self.create_setting_row(frame, "LLM Model:", "llm_model", "text",
                               help_text="The language model to use (e.g., mistral, llama2)")
        
        # Memory Settings
        separator = tk.Frame(frame, height=2, bg='#404040')
        separator.pack(fill=tk.X, pady=20)
        
        memory_title = tk.Label(frame, text="Memory Settings", font=('Arial', 12, 'bold'),
                               bg='#2b2b2b', fg='#ffffff')
        memory_title.pack(anchor='w', pady=(0, 10))
        
        self.create_setting_row(frame, "Max Recent Interactions:", "memory_recent", "number",
                               help_text="Number of recent interactions to keep in memory")
        
        self.create_setting_row(frame, "Short-term Memory Limit:", "memory_short_term", "number",
                               help_text="Maximum items in short-term memory")
        
        self.create_setting_row(frame, "Long-term Threshold:", "memory_long_term_threshold", "number",
                               help_text="Importance threshold for long-term memory (1-10)")
    
    def setup_spotify_tab(self):
        """Setup the Spotify settings tab"""
        frame = self.create_tab_frame(self.notebook, "Spotify")
        
        # Spotify Status
        status_frame = tk.Frame(frame, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(status_frame, text="Connection Status:", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='#ffffff').pack(anchor='w')
        
        self.spotify_status_label = tk.Label(status_frame, text="Checking...",
                                           font=('Arial', 10), bg='#2b2b2b', fg='#ffa500')
        self.spotify_status_label.pack(anchor='w', pady=(5, 0))
        
        # Test connection button
        test_button = tk.Button(
            status_frame,
            text="Test Connection",
            command=self.test_spotify_connection,
            font=('Arial', 10),
            bg='#28a745',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        test_button.pack(anchor='w', pady=(5, 0))
        
        # Spotify Credentials
        separator = tk.Frame(frame, height=2, bg='#404040')
        separator.pack(fill=tk.X, pady=20)
        
        cred_title = tk.Label(frame, text="Spotify Credentials", font=('Arial', 12, 'bold'),
                             bg='#2b2b2b', fg='#ffffff')
        cred_title.pack(anchor='w', pady=(0, 10))
        
        # Client ID
        self.create_setting_row(frame, "Client ID:", "spotify_client_id", "text",
                               help_text="Get this from your Spotify App in Spotify Developer Dashboard")
        
        # Client Secret
        self.create_setting_row(frame, "Client Secret:", "spotify_client_secret", "password",
                               help_text="Get this from your Spotify App in Spotify Developer Dashboard")
        
        # Redirect URI
        self.create_setting_row(frame, "Redirect URI:", "spotify_redirect_uri", "text",
                               help_text="Must match the redirect URI in your Spotify App settings",
                               default_value="http://localhost:8888/callback")
        
        # Instructions
        instructions_frame = tk.Frame(frame, bg='#1e1e1e', relief=tk.FLAT, bd=1)
        instructions_frame.pack(fill=tk.X, pady=20, padx=5)
        
        instructions_title = tk.Label(instructions_frame, text="Setup Instructions:",
                                    font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#87CEEB')
        instructions_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        instructions_text = """1. Go to https://developer.spotify.com/dashboard
2. Create a new app or use an existing one
3. Copy the Client ID and Client Secret
4. Add http://localhost:8888/callback to Redirect URIs
5. Paste the credentials above and click Test Connection"""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text,
                                    font=('Arial', 9), bg='#1e1e1e', fg='#ffffff',
                                    justify=tk.LEFT, wraplength=500)
        instructions_label.pack(anchor='w', padx=10, pady=(0, 10))
    
    def setup_weather_tab(self):
        """Setup the weather settings tab"""
        frame = self.create_tab_frame(self.notebook, "Weather")
        
        # Default Location
        self.create_setting_row(frame, "Default Location:", "weather_location", "text",
                               help_text="Default city for weather queries (e.g., London, New York)")
        
        # API Settings
        separator = tk.Frame(frame, height=2, bg='#404040')
        separator.pack(fill=tk.X, pady=20)
        
        api_title = tk.Label(frame, text="API Settings", font=('Arial', 12, 'bold'),
                            bg='#2b2b2b', fg='#ffffff')
        api_title.pack(anchor='w', pady=(0, 10))
        
        self.create_setting_row(frame, "Request Timeout (seconds):", "weather_timeout", "number",
                               help_text="How long to wait for weather API responses")
        
        # Test weather button
        test_frame = tk.Frame(frame, bg='#2b2b2b')
        test_frame.pack(fill=tk.X, pady=20)
        
        test_weather_button = tk.Button(
            test_frame,
            text="Test Weather Service",
            command=self.test_weather_service,
            font=('Arial', 10),
            bg='#28a745',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        test_weather_button.pack(anchor='w')
        
        self.weather_test_label = tk.Label(test_frame, text="",
                                         font=('Arial', 9), bg='#2b2b2b', fg='#888888')
        self.weather_test_label.pack(anchor='w', pady=(5, 0))
    
    def setup_calendar_tab(self):
        """Setup the calendar settings tab"""
        frame = self.create_tab_frame(self.notebook, "Calendar")
        
        # Calendar Status
        status_frame = tk.Frame(frame, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(status_frame, text="Google Calendar Status:", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='#ffffff').pack(anchor='w')
        
        self.calendar_status_label = tk.Label(status_frame, text="Checking...",
                                            font=('Arial', 10), bg='#2b2b2b', fg='#ffa500')
        self.calendar_status_label.pack(anchor='w', pady=(5, 0))
        
        # Timezone
        self.create_setting_row(frame, "Timezone:", "calendar_timezone", "text",
                               help_text="Your timezone (e.g., Europe/London, America/New_York)")
        
        # Credentials File
        separator = tk.Frame(frame, height=2, bg='#404040')
        separator.pack(fill=tk.X, pady=20)
        
        files_title = tk.Label(frame, text="Google API Files", font=('Arial', 12, 'bold'),
                              bg='#2b2b2b', fg='#ffffff')
        files_title.pack(anchor='w', pady=(0, 10))
        
        # Credentials file selector
        cred_frame = tk.Frame(frame, bg='#2b2b2b')
        cred_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cred_frame, text="Credentials File:", font=('Arial', 10),
                bg='#2b2b2b', fg='#ffffff', width=20, anchor='w').pack(side=tk.LEFT)
        
        self.calendar_cred_var = tk.StringVar()
        cred_entry = tk.Entry(cred_frame, textvariable=self.calendar_cred_var,
                             font=('Arial', 10), bg='#404040', fg='#ffffff',
                             relief=tk.FLAT, bd=1)
        cred_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        browse_button = tk.Button(
            cred_frame,
            text="Browse",
            command=self.browse_credentials_file,
            font=('Arial', 9),
            bg='#6c757d',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        browse_button.pack(side=tk.RIGHT)
        
        # Calendar Instructions
        instructions_frame = tk.Frame(frame, bg='#1e1e1e', relief=tk.FLAT, bd=1)
        instructions_frame.pack(fill=tk.X, pady=20, padx=5)
        
        instructions_title = tk.Label(instructions_frame, text="Setup Instructions:",
                                    font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#87CEEB')
        instructions_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        instructions_text = """1. Go to Google Cloud Console (console.cloud.google.com)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials.json file
6. Use Browse button to select the file"""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text,
                                    font=('Arial', 9), bg='#1e1e1e', fg='#ffffff',
                                    justify=tk.LEFT, wraplength=500)
        instructions_label.pack(anchor='w', padx=10, pady=(0, 10))
    
    def setup_advanced_tab(self):
        """Setup the advanced settings tab"""
        frame = self.create_tab_frame(self.notebook, "Advanced")
        
        # LLM Settings
        llm_title = tk.Label(frame, text="LLM Settings", font=('Arial', 12, 'bold'),
                            bg='#2b2b2b', fg='#ffffff')
        llm_title.pack(anchor='w', pady=(0, 10))
        
        self.create_setting_row(frame, "LLM Timeout (seconds):", "llm_timeout", "number",
                               help_text="How long to wait for LLM responses")
        
        self.create_setting_row(frame, "Ollama Command:", "ollama_command", "text",
                               help_text="Command to run Ollama (usually 'ollama')")
        
        # Web Search Settings
        separator = tk.Frame(frame, height=2, bg='#404040')
        separator.pack(fill=tk.X, pady=20)
        
        web_title = tk.Label(frame, text="Web Search Settings", font=('Arial', 12, 'bold'),
                            bg='#2b2b2b', fg='#ffffff')
        web_title.pack(anchor='w', pady=(0, 10))
        
        self.create_setting_row(frame, "Max Search Results:", "web_max_results", "number",
                               help_text="Maximum number of search results to return")
        
        self.create_setting_row(frame, "Search Timeout (seconds):", "web_timeout", "number",
                               help_text="How long to wait for web search responses")
        
        # Voice Settings
        separator2 = tk.Frame(frame, height=2, bg='#404040')
        separator2.pack(fill=tk.X, pady=20)
        
        voice_title = tk.Label(frame, text="Voice Settings", font=('Arial', 12, 'bold'),
                              bg='#2b2b2b', fg='#ffffff')
        voice_title.pack(anchor='w', pady=(0, 10))
        
        self.create_setting_row(frame, "Wake Word Timeout:", "voice_wake_timeout", "number",
                               help_text="Seconds to wait for wake word detection")
        
        self.create_setting_row(frame, "Command Timeout:", "voice_command_timeout", "number",
                               help_text="Seconds to wait for voice commands")
    
    def create_setting_row(self, parent, label_text, setting_key, setting_type, 
                          help_text=None, default_value=""):
        """Create a setting row with label, input, and optional help text"""
        row_frame = tk.Frame(parent, bg='#2b2b2b')
        row_frame.pack(fill=tk.X, pady=5)
        
        # Label
        label = tk.Label(row_frame, text=label_text, font=('Arial', 10),
                        bg='#2b2b2b', fg='#ffffff', width=20, anchor='w')
        label.pack(side=tk.LEFT)
        
        # Input field
        if setting_type == "text":
            var = tk.StringVar()
            entry = tk.Entry(row_frame, textvariable=var, font=('Arial', 10),
                           bg='#404040', fg='#ffffff', relief=tk.FLAT, bd=1)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        elif setting_type == "password":
            var = tk.StringVar()
            entry = tk.Entry(row_frame, textvariable=var, font=('Arial', 10),
                           bg='#404040', fg='#ffffff', relief=tk.FLAT, bd=1, show="*")
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        elif setting_type == "number":
            var = tk.StringVar()
            entry = tk.Entry(row_frame, textvariable=var, font=('Arial', 10),
                           bg='#404040', fg='#ffffff', relief=tk.FLAT, bd=1)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Store the variable for later access
        setattr(self, f"{setting_key}_var", var)
        
        # Help text
        if help_text:
            help_frame = tk.Frame(parent, bg='#2b2b2b')
            help_frame.pack(fill=tk.X, padx=(25, 0))
            help_label = tk.Label(help_frame, text=help_text, font=('Arial', 8),
                                bg='#2b2b2b', fg='#888888', wraplength=500, justify=tk.LEFT)
            help_label.pack(anchor='w')
    
    def load_current_settings(self):
        """Load current settings from config"""
        try:
            # General settings
            self.assistant_name_var.set(config.get('assistant.name', 'Assistant'))
            self.llm_model_var.set(config.get('llm.model', 'mistral'))
            self.memory_recent_var.set(str(config.get('memory.max_recent_interactions', 5)))
            self.memory_short_term_var.set(str(config.get('memory.short_term_max_items', 50)))
            self.memory_long_term_threshold_var.set(str(config.get('memory.long_term_threshold', 7)))
            
            # Spotify settings
            self.spotify_client_id_var.set(os.getenv('SPOTIFY_CLIENT_ID', ''))
            self.spotify_client_secret_var.set(os.getenv('SPOTIFY_CLIENT_SECRET', ''))
            self.spotify_redirect_uri_var.set(config.get('spotify.default_redirect_uri', 'http://localhost:8888/callback'))
            
            # Weather settings
            self.weather_location_var.set(config.get('weather.default_location', 'Guildford'))
            self.weather_timeout_var.set(str(config.get('weather.timeout_seconds', 10)))
            
            # Calendar settings
            self.calendar_timezone_var.set(config.get('calendar.timezone', 'Europe/London'))
            self.calendar_cred_var.set(config.get('calendar.credentials_file', 'credentials.json'))
            
            # Advanced settings
            self.llm_timeout_var.set(str(config.get('llm.timeout_seconds', 30)))
            self.ollama_command_var.set(config.get('llm.ollama_command', 'ollama'))
            self.web_max_results_var.set(str(config.get('web_search.max_results', 5)))
            self.web_timeout_var.set(str(config.get('web_search.timeout_seconds', 10)))
            self.voice_wake_timeout_var.set(str(config.get('voice.wake_word_timeout', 5.0)))
            self.voice_command_timeout_var.set(str(config.get('voice.command_timeout', 10.0)))
            
            # Store original values
            self.store_original_values()
            
            # Check service statuses
            self.check_service_statuses()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
    
    def store_original_values(self):
        """Store original values for comparison"""
        self.original_values = {
            'assistant_name': self.assistant_name_var.get(),
            'llm_model': self.llm_model_var.get(),
            'weather_location': self.weather_location_var.get(),
            'spotify_client_id': self.spotify_client_id_var.get(),
            'spotify_client_secret': self.spotify_client_secret_var.get(),
            'calendar_timezone': self.calendar_timezone_var.get(),
        }
    
    def check_service_statuses(self):
        """Check the status of various services"""
        # Check Spotify status
        try:
            spotify = SpotifyInterface()
            if spotify.is_authenticated:
                user = spotify.sp.current_user()
                username = user.get('display_name', user.get('id', 'Unknown'))
                self.spotify_status_label.config(text=f"✓ Connected as {username}", fg='#28a745')
            else:
                self.spotify_status_label.config(text="✗ Not connected", fg='#dc3545')
        except Exception as e:
            self.spotify_status_label.config(text=f"✗ Error: {str(e)}", fg='#dc3545')
        
        # Check Calendar status
        try:
            from calendar_interface import GoogleCalendar
            calendar = GoogleCalendar()
            self.calendar_status_label.config(text="✓ Connected to Google Calendar", fg='#28a745')
        except Exception as e:
            self.calendar_status_label.config(text=f"✗ Error: {str(e)}", fg='#dc3545')
    
    def test_spotify_connection(self):
        """Test Spotify connection with current settings"""
        try:
            # Temporarily set environment variables
            os.environ['SPOTIFY_CLIENT_ID'] = self.spotify_client_id_var.get()
            os.environ['SPOTIFY_CLIENT_SECRET'] = self.spotify_client_secret_var.get()
            
            # Test connection
            spotify = SpotifyInterface()
            if spotify.is_authenticated:
                user = spotify.sp.current_user()
                username = user.get('display_name', user.get('id', 'Unknown'))
                self.spotify_status_label.config(text=f"✓ Connected as {username}", fg='#28a745')
                messagebox.showinfo("Success", f"Successfully connected to Spotify as {username}")
            else:
                self.spotify_status_label.config(text="✗ Authentication failed", fg='#dc3545')
                messagebox.showerror("Error", "Failed to authenticate with Spotify. Please check your credentials.")
        except Exception as e:
            self.spotify_status_label.config(text=f"✗ Error: {str(e)}", fg='#dc3545')
            messagebox.showerror("Error", f"Spotify connection test failed: {str(e)}")
    
    def test_weather_service(self):
        """Test weather service with current settings"""
        try:
            from commands import get_weather
            location = self.weather_location_var.get() or "London"
            result = get_weather(location)
            self.weather_test_label.config(text=f"✓ Test successful: {result[:50]}...", fg='#28a745')
            messagebox.showinfo("Success", f"Weather test successful!\n\n{result}")
        except Exception as e:
            self.weather_test_label.config(text=f"✗ Test failed: {str(e)}", fg='#dc3545')
            messagebox.showerror("Error", f"Weather service test failed: {str(e)}")
    
    def browse_credentials_file(self):
        """Browse for Google Calendar credentials file"""
        filename = filedialog.askopenfilename(
            title="Select Google Calendar Credentials File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.calendar_cred_var.set(filename)
    
    def save_settings(self):
        """Save all settings to config file"""
        try:
            # Create new config data
            new_config = config._config.copy()
            
            # Update config values
            new_config['assistant']['name'] = self.assistant_name_var.get()
            new_config['llm']['model'] = self.llm_model_var.get()
            new_config['llm']['timeout_seconds'] = int(self.llm_timeout_var.get())
            new_config['llm']['ollama_command'] = self.ollama_command_var.get()
            
            new_config['memory']['max_recent_interactions'] = int(self.memory_recent_var.get())
            new_config['memory']['short_term_max_items'] = int(self.memory_short_term_var.get())
            new_config['memory']['long_term_threshold'] = int(self.memory_long_term_threshold_var.get())
            
            new_config['weather']['default_location'] = self.weather_location_var.get()
            new_config['weather']['timeout_seconds'] = int(self.weather_timeout_var.get())
            
            new_config['calendar']['timezone'] = self.calendar_timezone_var.get()
            new_config['calendar']['credentials_file'] = self.calendar_cred_var.get()
            
            new_config['web_search']['max_results'] = int(self.web_max_results_var.get())
            new_config['web_search']['timeout_seconds'] = int(self.web_timeout_var.get())
            
            new_config['voice']['wake_word_timeout'] = float(self.voice_wake_timeout_var.get())
            new_config['voice']['command_timeout'] = float(self.voice_command_timeout_var.get())
            
            # Save to file
            with open('config.json', 'w') as f:
                json.dump(new_config, f, indent=2)
            
            # Update environment variables for Spotify
            os.environ['SPOTIFY_CLIENT_ID'] = self.spotify_client_id_var.get()
            os.environ['SPOTIFY_CLIENT_SECRET'] = self.spotify_client_secret_var.get()
            
            # Reload config
            config._config = new_config
            
            messagebox.showinfo("Success", "Settings saved successfully!\n\nSome changes may require restarting the application to take effect.")
            self.changes_made = True
            
            if self.parent:
                self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid number format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def cancel_settings(self):
        """Cancel settings without saving"""
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Unsaved Changes", 
                                     "You have unsaved changes. Are you sure you want to cancel?"):
                return
        
        self.window.destroy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", 
                             "Are you sure you want to reset all settings to defaults?\n\nThis cannot be undone."):
            try:
                # Reset to default values
                self.assistant_name_var.set("Assistant")
                self.llm_model_var.set("mistral")
                self.llm_timeout_var.set("30")
                self.ollama_command_var.set("ollama")
                
                self.memory_recent_var.set("5")
                self.memory_short_term_var.set("50")
                self.memory_long_term_threshold_var.set("7")
                
                self.weather_location_var.set("Guildford")
                self.weather_timeout_var.set("10")
                
                self.spotify_client_id_var.set("")
                self.spotify_client_secret_var.set("")
                self.spotify_redirect_uri_var.set("http://localhost:8888/callback")
                
                self.calendar_timezone_var.set("Europe/London")
                self.calendar_cred_var.set("credentials.json")
                
                self.web_max_results_var.set("5")
                self.web_timeout_var.set("10")
                
                self.voice_wake_timeout_var.set("5.0")
                self.voice_command_timeout_var.set("10.0")
                
                messagebox.showinfo("Success", "All settings have been reset to defaults.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset settings: {str(e)}")
    
    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        try:
            current_values = {
                'assistant_name': self.assistant_name_var.get(),
                'llm_model': self.llm_model_var.get(),
                'weather_location': self.weather_location_var.get(),
                'spotify_client_id': self.spotify_client_id_var.get(),
                'spotify_client_secret': self.spotify_client_secret_var.get(),
                'calendar_timezone': self.calendar_timezone_var.get(),
            }
            
            return current_values != self.original_values
        except:
            return False
    
    def on_closing(self):
        """Handle window closing"""
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Unsaved Changes", 
                                     "You have unsaved changes. Are you sure you want to close?"):
                return
        
        self.window.destroy()

def main():
    """Main entry point for testing the settings window"""
    app = SettingsWindow()
    app.window.mainloop()

if __name__ == "__main__":
    main()
