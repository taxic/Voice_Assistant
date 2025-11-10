#!/usr/bin/env python3
"""
Voice Assistant Settings GUI
Configuration interface for the voice assistant
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
import platform
from pathlib import Path

# Import configuration manager
from config_manager import config

class VoiceAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant Settings - Jarvis")
        self.root.geometry("900x600")
        self.root.configure(bg='#2c3e50')

        # GUI state
        self.is_listening = False

        # Create GUI components
        self.create_menu_bar()
        self.create_main_interface()
        self.create_control_panel()
        self.create_status_bar()

        # Load current settings
        self.load_current_settings()

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save All Settings", command=self.save_all_settings)
        file_menu.add_command(label="Reload Settings", command=self.load_current_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Voice Recognition", command=self.test_voice_recognition)
        tools_menu.add_command(label="Test TTS", command=self.test_tts)
        tools_menu.add_command(label="Check Dependencies", command=self.check_dependencies)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_interface(self):
        """Create the main tabbed interface"""
        # Create notebook for settings tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create all settings tabs
        self.create_assistant_settings()
        self.create_llm_settings()
        self.create_tts_settings()
        self.create_voice_settings()
        self.create_memory_settings()
        self.create_api_settings()
        self.create_service_settings()
        self.create_iot_settings()

    def create_assistant_settings(self):
        """Create assistant basic settings tab"""
        assistant_frame = ttk.Frame(self.notebook)
        self.notebook.add(assistant_frame, text="Assistant")

        # Main settings frame
        main_frame = tk.LabelFrame(assistant_frame, text="Basic Settings", padx=10, pady=10)
        main_frame.pack(fill=tk.X, padx=10, pady=5)

        # Assistant name
        tk.Label(main_frame, text="Assistant Name:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.assistant_name_var = tk.StringVar(value=config.get('assistant.name', 'Jarvis'))
        tk.Entry(main_frame, textvariable=self.assistant_name_var, width=30).grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Assistant version
        tk.Label(main_frame, text="Version:", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.version_var = tk.StringVar(value=config.get('assistant.version', '1.0.0'))
        tk.Entry(main_frame, textvariable=self.version_var, width=30).grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Interrupt phrases
        tk.Label(main_frame, text="Interrupt Phrases:", font=("Helvetica", 10)).grid(row=2, column=0, sticky="nw", pady=5)
        self.interrupt_phrases_text = tk.Text(main_frame, height=4, width=30, font=("Helvetica", 9))
        self.interrupt_phrases_text.grid(row=2, column=1, padx=(10, 0), sticky="w")
        phrases = config.get('assistant.interrupt_phrases', [
            "stop", "pause", "wait", "interrupt", "hold on", "quiet",
            "shut up", "enough", "cancel", "nevermind", "never mind"
        ])
        self.interrupt_phrases_text.insert("1.0", "\n".join(phrases))

    def create_llm_settings(self):
        """Create LLM settings tab"""
        llm_frame = ttk.Frame(self.notebook)
        self.notebook.add(llm_frame, text="LLM")

        # LLM settings frame
        settings_frame = tk.LabelFrame(llm_frame, text="Language Model Settings", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Model selection
        tk.Label(settings_frame, text="Model:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.llm_model_var = tk.StringVar(value=config.get('llm.model', 'mistral'))
        ttk.Combobox(settings_frame, textvariable=self.llm_model_var, values=['mistral', 'llama2', 'codellama']).grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Timeout
        tk.Label(settings_frame, text="Timeout (seconds):", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.llm_timeout_var = tk.IntVar(value=config.get('llm.timeout_seconds', 30))
        tk.Spinbox(settings_frame, from_=10, to=120, textvariable=self.llm_timeout_var, width=10).grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Ollama command
        tk.Label(settings_frame, text="Ollama Command:", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.ollama_command_var = tk.StringVar(value=config.get('llm.ollama_command', 'ollama'))
        tk.Entry(settings_frame, textvariable=self.ollama_command_var, width=30).grid(row=2, column=1, padx=(10, 0), sticky="w")

    def create_tts_settings(self):
        """Create TTS settings tab"""
        tts_frame = ttk.Frame(self.notebook)
        self.notebook.add(tts_frame, text="TTS")

        # TTS settings frame
        settings_frame = tk.LabelFrame(tts_frame, text="Text-to-Speech Settings", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Engine
        tk.Label(settings_frame, text="Engine:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.tts_engine_var = tk.StringVar(value=config.get('tts.engine', 'piper'))
        ttk.Combobox(settings_frame, textvariable=self.tts_engine_var, values=['piper'], state='readonly').grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Voice selection
        tk.Label(settings_frame, text="Voice:", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.tts_voice_var = tk.StringVar(value=config.get('tts.piper.voice', 'en_GB-southern_english_female-low'))
        voice_combo = ttk.Combobox(settings_frame, textvariable=self.tts_voice_var, width=25)
        voice_combo['values'] = ['en_GB-southern_english_female-low', 'en_US-lessac-medium', 'en_US-hfc-female', 'en_US-hfc-male']
        voice_combo.grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Download models
        self.download_models_var = tk.BooleanVar(value=config.get('tts.piper.download_models', True))
        tk.Checkbutton(settings_frame, text="Auto-download models", variable=self.download_models_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        # Chunk size
        tk.Label(settings_frame, text="Chunk Size:", font=("Helvetica", 10)).grid(row=3, column=0, sticky="w", pady=5)
        self.chunk_size_var = tk.IntVar(value=config.get('tts.piper.chunk_size', 50))
        tk.Spinbox(settings_frame, from_=20, to=100, textvariable=self.chunk_size_var, width=10).grid(row=3, column=1, padx=(10, 0), sticky="w")

    def create_voice_settings(self):
        """Create voice recognition settings tab"""
        voice_frame = ttk.Frame(self.notebook)
        self.notebook.add(voice_frame, text="Voice Control")

        # Voice settings frame
        settings_frame = tk.LabelFrame(voice_frame, text="Voice Recognition Settings", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Wake word timeout
        tk.Label(settings_frame, text="Wake Word Timeout (s):", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.wake_timeout_var = tk.DoubleVar(value=config.get('voice.wake_word_timeout', 5.0))
        tk.Spinbox(settings_frame, from_=1.0, to=30.0, increment=0.5, textvariable=self.wake_timeout_var, width=10).grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Command timeout
        tk.Label(settings_frame, text="Command Timeout (s):", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.cmd_timeout_var = tk.DoubleVar(value=config.get('voice.command_timeout', 10.0))
        tk.Spinbox(settings_frame, from_=5.0, to=60.0, increment=1.0, textvariable=self.cmd_timeout_var, width=10).grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Interrupt check interval
        tk.Label(settings_frame, text="Interrupt Check (s):", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.interrupt_interval_var = tk.DoubleVar(value=config.get('voice.interrupt_check_interval', 0.05))
        tk.Spinbox(settings_frame, from_=0.01, to=0.5, increment=0.01, textvariable=self.interrupt_interval_var, width=10).grid(row=2, column=1, padx=(10, 0), sticky="w")

    def create_memory_settings(self):
        """Create memory settings tab"""
        memory_frame = ttk.Frame(self.notebook)
        self.notebook.add(memory_frame, text="Memory")

        # Memory settings frame
        settings_frame = tk.LabelFrame(memory_frame, text="Memory Configuration", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Max recent interactions
        tk.Label(settings_frame, text="Max Recent Interactions:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.max_recent_var = tk.IntVar(value=config.get('memory.max_recent_interactions', 5))
        tk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.max_recent_var, width=10).grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Short term max items
        tk.Label(settings_frame, text="Short Term Max Items:", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.short_term_max_var = tk.IntVar(value=config.get('memory.short_term_max_items', 50))
        tk.Spinbox(settings_frame, from_=10, to=200, textvariable=self.short_term_max_var, width=10).grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Long term threshold
        tk.Label(settings_frame, text="Long Term Threshold:", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.long_term_threshold_var = tk.IntVar(value=config.get('memory.long_term_threshold', 7))
        tk.Spinbox(settings_frame, from_=3, to=15, textvariable=self.long_term_threshold_var, width=10).grid(row=2, column=1, padx=(10, 0), sticky="w")

        # Importance decay days
        tk.Label(settings_frame, text="Importance Decay (days):", font=("Helvetica", 10)).grid(row=3, column=0, sticky="w", pady=5)
        self.decay_days_var = tk.IntVar(value=config.get('memory.importance_decay_days', 30))
        tk.Spinbox(settings_frame, from_=7, to=90, textvariable=self.decay_days_var, width=10).grid(row=3, column=1, padx=(10, 0), sticky="w")

    def create_api_settings(self):
        """Create API settings tab"""
        api_frame = ttk.Frame(self.notebook)
        self.notebook.add(api_frame, text="APIs")

        # Weather API settings
        weather_frame = tk.LabelFrame(api_frame, text="Weather API", padx=10, pady=10)
        weather_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(weather_frame, text="Default Location:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.weather_location_var = tk.StringVar(value=config.get('weather.default_location', 'Guildford'))
        tk.Entry(weather_frame, textvariable=self.weather_location_var, width=30).grid(row=0, column=1, padx=(10, 0), sticky="w")

        tk.Label(weather_frame, text="Timeout (seconds):", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.weather_timeout_var = tk.IntVar(value=config.get('weather.timeout_seconds', 10))
        tk.Spinbox(weather_frame, from_=5, to=30, textvariable=self.weather_timeout_var, width=10).grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Calendar API settings
        calendar_frame = tk.LabelFrame(api_frame, text="Calendar API", padx=10, pady=10)
        calendar_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(calendar_frame, text="Credentials File:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.calendar_creds_var = tk.StringVar(value=config.get('calendar.credentials_file', 'credentials.json'))
        tk.Entry(calendar_frame, textvariable=self.calendar_creds_var, width=25).grid(row=0, column=1, padx=(10, 0), sticky="w")
        tk.Button(calendar_frame, text="Browse", command=self.browse_credentials).grid(row=0, column=2, padx=(10, 0))

        tk.Label(calendar_frame, text="Timezone:", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.timezone_var = tk.StringVar(value=config.get('calendar.timezone', 'Europe/London'))
        tk.Entry(calendar_frame, textvariable=self.timezone_var, width=25).grid(row=1, column=1, padx=(10, 0), sticky="w")

    def create_service_settings(self):
        """Create service integration settings tab"""
        service_frame = ttk.Frame(self.notebook)
        self.notebook.add(service_frame, text="Services")

        # Spotify settings
        spotify_frame = tk.LabelFrame(service_frame, text="Spotify Integration", padx=10, pady=10)
        spotify_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(spotify_frame, text="Client ID (env var):", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.spotify_client_var = tk.StringVar(value=config.get('spotify.client_id_env', 'SPOTIFY_CLIENT_ID'))
        tk.Entry(spotify_frame, textvariable=self.spotify_client_var, width=25).grid(row=0, column=1, padx=(10, 0), sticky="w")

        tk.Label(spotify_frame, text="Client Secret (env var):", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.spotify_secret_var = tk.StringVar(value=config.get('spotify.client_secret_env', 'SPOTIFY_CLIENT_SECRET'))
        tk.Entry(spotify_frame, textvariable=self.spotify_secret_var, width=25).grid(row=1, column=1, padx=(10, 0), sticky="w")

        tk.Label(spotify_frame, text="Redirect URI (env var):", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.spotify_redirect_var = tk.StringVar(value=config.get('spotify.redirect_uri_env', 'SPOTIFY_REDIRECT_URI'))
        tk.Entry(spotify_frame, textvariable=self.spotify_redirect_var, width=25).grid(row=2, column=1, padx=(10, 0), sticky="w")

        # Notion settings
        notion_frame = tk.LabelFrame(service_frame, text="Notion Integration", padx=10, pady=10)
        notion_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(notion_frame, text="Database ID:", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.notion_db_var = tk.StringVar(value=config.get('notion.default_database_id', ''))
        tk.Entry(notion_frame, textvariable=self.notion_db_var, width=35).grid(row=0, column=1, padx=(10, 0), sticky="w")

        tk.Label(notion_frame, text="Page ID:", font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.notion_page_var = tk.StringVar(value=config.get('notion.default_page_id', ''))
        tk.Entry(notion_frame, textvariable=self.notion_page_var, width=35).grid(row=1, column=1, padx=(10, 0), sticky="w")

        tk.Label(notion_frame, text="Timeout (seconds):", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.notion_timeout_var = tk.IntVar(value=config.get('notion.timeout_seconds', 15))
        tk.Spinbox(notion_frame, from_=5, to=60, textvariable=self.notion_timeout_var, width=10).grid(row=2, column=1, padx=(10, 0), sticky="w")

    def create_iot_settings(self):
        """Create IoT control settings tab"""
        iot_frame = ttk.Frame(self.notebook)
        self.notebook.add(iot_frame, text="IoT Control")

        # Create main IoT control interface
        self.create_iot_control_interface(iot_frame)

    def create_iot_control_interface(self, parent):
        """Create the IoT device control interface"""
        # Device list frame
        device_frame = tk.LabelFrame(parent, text="IoT Devices", padx=10, pady=10)
        device_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Device listbox with scrollbar
        listbox_frame = tk.Frame(device_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(listbox_frame, text="Available Devices:", font=("Helvetica", 10, "bold")).pack(anchor="w")

        # Create listbox with scrollbar
        listbox_container = tk.Frame(listbox_frame)
        listbox_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.device_listbox = tk.Listbox(
            listbox_container,
            font=("Helvetica", 9),
            bg='white',
            selectmode=tk.SINGLE,
            height=8
        )
        device_scrollbar = tk.Scrollbar(listbox_container, orient=tk.VERTICAL, command=self.device_listbox.yview)
        self.device_listbox.config(yscrollcommand=device_scrollbar.set)

        self.device_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        device_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Refresh button
        refresh_frame = tk.Frame(device_frame)
        refresh_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Button(
            refresh_frame,
            text="🔄 Refresh Devices",
            command=self.refresh_iot_devices,
            bg='#3498db',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=15
        ).pack()

        # Control buttons frame
        control_frame = tk.LabelFrame(parent, text="Device Controls", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Light controls
        light_frame = tk.LabelFrame(control_frame, text="Light Controls", padx=10, pady=10)
        light_frame.pack(fill=tk.X, pady=(0, 10))

        light_button_frame = tk.Frame(light_frame)
        light_button_frame.pack(fill=tk.X)

        self.light_on_btn = tk.Button(
            light_button_frame,
            text="💡 Turn On",
            command=self.turn_on_selected_light,
            bg='#27ae60',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.light_on_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.light_off_btn = tk.Button(
            light_button_frame,
            text="💡 Turn Off",
            command=self.turn_off_selected_light,
            bg='#e74c3c',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.light_off_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Brightness control
        brightness_frame = tk.Frame(light_frame)
        brightness_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(brightness_frame, text="Brightness (0-100):", font=("Helvetica", 9)).pack(side=tk.LEFT)
        self.brightness_var = tk.IntVar(value=50)
        brightness_spinbox = tk.Spinbox(
            brightness_frame,
            from_=0,
            to=100,
            textvariable=self.brightness_var,
            width=5,
            font=("Helvetica", 9)
        )
        brightness_spinbox.pack(side=tk.LEFT, padx=(10, 0))

        self.set_brightness_btn = tk.Button(
            brightness_frame,
            text="Set Brightness",
            command=self.set_selected_light_brightness,
            bg='#f39c12',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.set_brightness_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Color selection
        color_frame = tk.Frame(light_frame)
        color_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Label(color_frame, text="Color:", font=("Helvetica", 9)).pack(side=tk.LEFT)
        self.color_var = tk.StringVar(value='white')
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=['white', 'red', 'green', 'blue', 'yellow', 'purple', 'orange'],
            state='readonly',
            width=10,
            font=("Helvetica", 9)
        )
        color_combo.pack(side=tk.LEFT, padx=(10, 0))

        self.set_color_btn = tk.Button(
            color_frame,
            text="Set Color",
            command=self.set_selected_light_color,
            bg='#9b59b6',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.set_color_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Switch controls
        switch_frame = tk.LabelFrame(control_frame, text="Switch Controls", padx=10, pady=10)
        switch_frame.pack(fill=tk.X, pady=(0, 10))

        switch_button_frame = tk.Frame(switch_frame)
        switch_button_frame.pack(fill=tk.X)

        self.switch_on_btn = tk.Button(
            switch_button_frame,
            text="🔌 Turn On",
            command=self.turn_on_selected_switch,
            bg='#27ae60',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.switch_on_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.switch_off_btn = tk.Button(
            switch_button_frame,
            text="🔌 Turn Off",
            command=self.turn_off_selected_switch,
            bg='#e74c3c',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.switch_off_btn.pack(side=tk.LEFT)

        # Thermostat controls
        thermostat_frame = tk.LabelFrame(control_frame, text="Thermostat Controls", padx=10, pady=10)
        thermostat_frame.pack(fill=tk.X, pady=(0, 10))

        temp_frame = tk.Frame(thermostat_frame)
        temp_frame.pack(fill=tk.X)

        tk.Label(temp_frame, text="Temperature (°C):", font=("Helvetica", 9)).pack(side=tk.LEFT)
        self.temperature_var = tk.DoubleVar(value=22.0)
        temp_spinbox = tk.Spinbox(
            temp_frame,
            from_=10.0,
            to=30.0,
            increment=0.5,
            textvariable=self.temperature_var,
            width=5,
            font=("Helvetica", 9)
        )
        temp_spinbox.pack(side=tk.LEFT, padx=(10, 0))

        self.set_temp_btn = tk.Button(
            temp_frame,
            text="Set Temperature",
            command=self.set_selected_thermostat,
            bg='#e67e22',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            state=tk.DISABLED
        )
        self.set_temp_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Group controls
        group_frame = tk.LabelFrame(control_frame, text="Group Controls", padx=10, pady=10)
        group_frame.pack(fill=tk.X)

        group_button_frame = tk.Frame(group_frame)
        group_button_frame.pack(fill=tk.X)

        self.all_lights_on_btn = tk.Button(
            group_button_frame,
            text="💡 All Lights On",
            command=self.turn_on_all_lights,
            bg='#27ae60',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10
        )
        self.all_lights_on_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.all_lights_off_btn = tk.Button(
            group_button_frame,
            text="💡 All Lights Off",
            command=self.turn_off_all_lights,
            bg='#e74c3c',
            fg='white',
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10
        )
        self.all_lights_off_btn.pack(side=tk.LEFT)

        # Status display
        status_frame = tk.Frame(parent, bg='#34495e', pady=5)
        status_frame.pack(fill=tk.X, padx=10)

        self.iot_status_label = tk.Label(
            status_frame,
            text="IoT Status: Ready",
            bg='#34495e',
            fg='white',
            font=("Helvetica", 9)
        )
        self.iot_status_label.pack(side=tk.LEFT)

        # Bind listbox selection event
        self.device_listbox.bind('<<ListboxSelect>>', self.on_device_select)

    def refresh_iot_devices(self):
        """Refresh the list of IoT devices"""
        try:
            from iot_manager import iot_manager

            # Clear current list
            self.device_listbox.delete(0, tk.END)

            # Get all devices
            devices = iot_manager.list_devices()

            if not devices:
                self.device_listbox.insert(tk.END, "No IoT devices configured")
                self.iot_status_label.config(text="IoT Status: No devices found")
                return

            # Add devices to listbox
            for device in devices:
                status = "Unknown"
                try:
                    # Try to get device status
                    status_result = iot_manager.get_device_status(device.name)
                    if "is" in status_result:
                        status = status_result.split(" is ")[-1].replace(".", "")
                except:
                    pass

                display_text = f"{device.name.title()} ({device.device_type}) - {status}"
                self.device_listbox.insert(tk.END, display_text)

            self.iot_status_label.config(text=f"IoT Status: {len(devices)} devices loaded")

        except Exception as e:
            self.iot_status_label.config(text=f"IoT Status: Error - {str(e)}")
            messagebox.showerror("IoT Error", f"Failed to load IoT devices: {e}")

    def on_device_select(self, event=None):
        """Handle device selection from listbox"""
        if not self.device_listbox.curselection():
            return

        # Get selected device info
        selected_index = self.device_listbox.curselection()[0]
        selected_text = self.device_listbox.get(selected_index)

        # Extract device name and type from display text
        # Format: "Device Name (device_type) - status"
        device_info = selected_text.split(" (")
        if len(device_info) >= 2:
            device_name = device_info[0].lower()
            device_type = device_info[1].split(")")[0]

            # Enable/disable controls based on device type
            self.enable_controls_for_device_type(device_type)

    def enable_controls_for_device_type(self, device_type):
        """Enable appropriate controls based on device type"""
        # Reset all buttons to disabled
        self.light_on_btn.config(state=tk.DISABLED)
        self.light_off_btn.config(state=tk.DISABLED)
        self.set_brightness_btn.config(state=tk.DISABLED)
        self.set_color_btn.config(state=tk.DISABLED)
        self.switch_on_btn.config(state=tk.DISABLED)
        self.switch_off_btn.config(state=tk.DISABLED)
        self.set_temp_btn.config(state=tk.DISABLED)

        # Enable controls based on device type
        if device_type == 'light':
            self.light_on_btn.config(state=tk.NORMAL)
            self.light_off_btn.config(state=tk.NORMAL)
            self.set_brightness_btn.config(state=tk.NORMAL)
            self.set_color_btn.config(state=tk.NORMAL)
        elif device_type == 'switch':
            self.switch_on_btn.config(state=tk.NORMAL)
            self.switch_off_btn.config(state=tk.NORMAL)
        elif device_type == 'thermostat':
            self.set_temp_btn.config(state=tk.NORMAL)

    def get_selected_device_name(self):
        """Get the name of the currently selected device"""
        if not self.device_listbox.curselection():
            return None

        selected_index = self.device_listbox.curselection()[0]
        selected_text = self.device_listbox.get(selected_index)

        # Extract device name from display text
        device_name = selected_text.split(" (")[0].lower()
        return device_name

    def turn_on_selected_light(self):
        """Turn on the selected light"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                result = iot_manager.turn_on_light(device_name)
                self.iot_status_label.config(text=f"Light: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to turn on light: {e}")

    def turn_off_selected_light(self):
        """Turn off the selected light"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                result = iot_manager.turn_off_light(device_name)
                self.iot_status_label.config(text=f"Light: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to turn off light: {e}")

    def set_selected_light_brightness(self):
        """Set brightness for the selected light"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                brightness = self.brightness_var.get()
                result = iot_manager.set_brightness(device_name, brightness)
                self.iot_status_label.config(text=f"Brightness: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to set brightness: {e}")

    def set_selected_light_color(self):
        """Set color for the selected light"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                color = self.color_var.get()
                result = iot_manager.set_color(device_name, color)
                self.iot_status_label.config(text=f"Color: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to set color: {e}")

    def turn_on_selected_switch(self):
        """Turn on the selected switch"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                result = iot_manager.turn_on_switch(device_name)
                self.iot_status_label.config(text=f"Switch: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to turn on switch: {e}")

    def turn_off_selected_switch(self):
        """Turn off the selected switch"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                result = iot_manager.turn_off_switch(device_name)
                self.iot_status_label.config(text=f"Switch: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to turn off switch: {e}")

    def set_selected_thermostat(self):
        """Set temperature for the selected thermostat"""
        device_name = self.get_selected_device_name()
        if device_name:
            try:
                from iot_manager import iot_manager
                temperature = self.temperature_var.get()
                result = iot_manager.set_temperature(device_name, temperature)
                self.iot_status_label.config(text=f"Thermostat: {result}")
                self.refresh_iot_devices()  # Refresh to show updated status
            except Exception as e:
                self.iot_status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("IoT Error", f"Failed to set temperature: {e}")

    def turn_on_all_lights(self):
        """Turn on all lights"""
        try:
            from iot_manager import iot_manager
            result = iot_manager.turn_on_all_lights()
            self.iot_status_label.config(text=f"All Lights: {result}")
            self.refresh_iot_devices()  # Refresh to show updated status
        except Exception as e:
            self.iot_status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("IoT Error", f"Failed to turn on all lights: {e}")

    def turn_off_all_lights(self):
        """Turn off all lights"""
        try:
            from iot_manager import iot_manager
            result = iot_manager.turn_off_all_lights()
            self.iot_status_label.config(text=f"All Lights: {result}")
            self.refresh_iot_devices()  # Refresh to show updated status
        except Exception as e:
            self.iot_status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("IoT Error", f"Failed to turn off all lights: {e}")

    def create_control_panel(self):
        """Create voice control panel"""
        control_frame = tk.Frame(self.root, bg='#34495e', pady=10)
        control_frame.pack(fill=tk.X, padx=10)

        # Voice activity indicator
        self.voice_indicator = tk.Canvas(
            control_frame,
            width=30,
            height=30,
            bg='#34495e',
            highlightthickness=0
        )
        self.voice_indicator.pack(side=tk.LEFT, padx=(0, 20))
        self.voice_circle = self.voice_indicator.create_oval(5, 5, 25, 25, fill='#95a5a6')

        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="Voice Assistant Ready",
            bg='#34495e',
            fg='white',
            font=("Helvetica", 12, "bold")
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#34495e')
        button_frame.pack(side=tk.RIGHT)

        self.start_button = tk.Button(
            button_frame,
            text="🎤 Start Voice Assistant",
            command=self.start_voice_assistant,
            bg='#27ae60',
            fg='white',
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            state=tk.NORMAL
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = tk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_voice_assistant,
            bg='#e74c3c',
            fg='white',
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = tk.Label(
            self.root,
            text="Voice Assistant Settings | Configure your assistant and click 'Start Voice Assistant' to begin",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg='#34495e',
            fg='white',
            font=("Helvetica", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_current_settings(self):
        """Load current settings from config"""
        # Update all variables with current config values
        self.assistant_name_var.set(config.get('assistant.name', 'Jarvis'))
        self.version_var.set(config.get('assistant.version', '1.0.0'))
        self.llm_model_var.set(config.get('llm.model', 'mistral'))
        self.llm_timeout_var.set(config.get('llm.timeout_seconds', 30))
        self.ollama_command_var.set(config.get('llm.ollama_command', 'ollama'))
        self.tts_engine_var.set(config.get('tts.engine', 'piper'))
        self.tts_voice_var.set(config.get('tts.piper.voice', 'en_GB-southern_english_female-low'))
        self.download_models_var.set(config.get('tts.piper.download_models', True))
        self.chunk_size_var.set(config.get('tts.piper.chunk_size', 50))
        self.wake_timeout_var.set(config.get('voice.wake_word_timeout', 5.0))
        self.cmd_timeout_var.set(config.get('voice.command_timeout', 10.0))
        self.interrupt_interval_var.set(config.get('voice.interrupt_check_interval', 0.05))
        self.max_recent_var.set(config.get('memory.max_recent_interactions', 5))
        self.short_term_max_var.set(config.get('memory.short_term_max_items', 50))
        self.long_term_threshold_var.set(config.get('memory.long_term_threshold', 7))
        self.decay_days_var.set(config.get('memory.importance_decay_days', 30))
        self.weather_location_var.set(config.get('weather.default_location', 'Guildford'))
        self.weather_timeout_var.set(config.get('weather.timeout_seconds', 10))
        self.calendar_creds_var.set(config.get('calendar.credentials_file', 'credentials.json'))
        self.timezone_var.set(config.get('calendar.timezone', 'Europe/London'))
        self.spotify_client_var.set(config.get('spotify.client_id_env', 'SPOTIFY_CLIENT_ID'))
        self.spotify_secret_var.set(config.get('spotify.client_secret_env', 'SPOTIFY_CLIENT_SECRET'))
        self.spotify_redirect_var.set(config.get('spotify.redirect_uri_env', 'SPOTIFY_REDIRECT_URI'))
        self.notion_db_var.set(config.get('notion.default_database_id', ''))
        self.notion_page_var.set(config.get('notion.default_page_id', ''))
        self.notion_timeout_var.set(config.get('notion.timeout_seconds', 15))

        # Load interrupt phrases
        phrases = config.get('assistant.interrupt_phrases', [
            "stop", "pause", "wait", "interrupt", "hold on", "quiet",
            "shut up", "enough", "cancel", "nevermind", "never mind"
        ])
        self.interrupt_phrases_text.delete("1.0", tk.END)
        self.interrupt_phrases_text.insert("1.0", "\n".join(phrases))

    def save_all_settings(self):
        """Save all settings to config file"""
        try:
            # Save assistant settings
            config.set('assistant.name', self.assistant_name_var.get())
            config.set('assistant.version', self.version_var.get())

            # Save interrupt phrases
            phrases_text = self.interrupt_phrases_text.get("1.0", tk.END).strip()
            phrases = [phrase.strip() for phrase in phrases_text.split('\n') if phrase.strip()]
            config.set('assistant.interrupt_phrases', phrases)

            # Save LLM settings
            config.set('llm.model', self.llm_model_var.get())
            config.set('llm.timeout_seconds', self.llm_timeout_var.get())
            config.set('llm.ollama_command', self.ollama_command_var.get())

            # Save TTS settings
            config.set('tts.engine', self.tts_engine_var.get())
            config.set('tts.piper.voice', self.tts_voice_var.get())
            config.set('tts.piper.download_models', self.download_models_var.get())
            config.set('tts.piper.chunk_size', self.chunk_size_var.get())

            # Save voice settings
            config.set('voice.wake_word_timeout', self.wake_timeout_var.get())
            config.set('voice.command_timeout', self.cmd_timeout_var.get())
            config.set('voice.interrupt_check_interval', self.interrupt_interval_var.get())

            # Save memory settings
            config.set('memory.max_recent_interactions', self.max_recent_var.get())
            config.set('memory.short_term_max_items', self.short_term_max_var.get())
            config.set('memory.long_term_threshold', self.long_term_threshold_var.get())
            config.set('memory.importance_decay_days', self.decay_days_var.get())

            # Save weather settings
            config.set('weather.default_location', self.weather_location_var.get())
            config.set('weather.timeout_seconds', self.weather_timeout_var.get())

            # Save calendar settings
            config.set('calendar.credentials_file', self.calendar_creds_var.get())
            config.set('calendar.timezone', self.timezone_var.get())

            # Save Spotify settings
            config.set('spotify.client_id_env', self.spotify_client_var.get())
            config.set('spotify.client_secret_env', self.spotify_secret_var.get())
            config.set('spotify.redirect_uri_env', self.spotify_redirect_var.get())

            # Save Notion settings
            config.set('notion.default_database_id', self.notion_db_var.get())
            config.set('notion.default_page_id', self.notion_page_var.get())
            config.set('notion.timeout_seconds', self.notion_timeout_var.get())

            # Save to file
            config.save()

            # Update status
            self.status_bar.config(text="Settings saved successfully!")
            messagebox.showinfo("Settings Saved", "All settings have been saved successfully!")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")
            self.status_bar.config(text=f"Error saving settings: {e}")

    def browse_credentials(self):
        """Browse for Google credentials file"""
        filename = filedialog.askopenfilename(
            title="Select Google Credentials File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.calendar_creds_var.set(filename)

    def start_voice_assistant(self):
        """Start the voice assistant"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.voice_indicator.itemconfig(self.voice_circle, fill='#27ae60')
        self.status_label.config(text="Voice Assistant Active - Listening for commands...")
        self.status_bar.config(text="Voice assistant started - Say your wake word to begin")

        # Start voice recognition in a separate thread
        voice_thread = threading.Thread(target=self._voice_assistant_thread, daemon=True)
        voice_thread.start()

    def stop_voice_assistant(self):
        """Stop the voice assistant"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.voice_indicator.itemconfig(self.voice_circle, fill='#95a5a6')
        self.status_label.config(text="Voice Assistant Stopped")
        self.status_bar.config(text="Voice assistant stopped - Configure settings or click 'Start' to begin")

    def _voice_assistant_thread(self):
        """Voice assistant main thread"""
        try:
            # Import here to avoid GUI blocking
            from voice_recognition import VoiceRecognizer
            from interruptible_tts import InterruptibleTTS
            from llm_interface import LLMInterface
            from enhanced_memory import EnhancedMemory

            # Initialize components
            memory = EnhancedMemory()
            recognizer = VoiceRecognizer()
            llm = LLMInterface(memory=memory)
            tts = InterruptibleTTS(voice_recognizer=recognizer)

            # Main voice assistant loop (simplified for GUI)
            while self.is_listening:
                try:
                    # Listen for wake word
                    self.root.after(0, lambda: self.status_bar.config(text="Listening for wake word..."))

                    # This would integrate with your actual voice recognition
                    # For now, we'll simulate the process
                    import time
                    time.sleep(1)

                    if not self.is_listening:
                        break

                    # Simulate voice command processing
                    self.root.after(0, lambda: self.status_bar.config(text="Processing voice command..."))

                    # Here you would integrate with your actual voice recognition system
                    # For demonstration, we'll just show it's working
                    time.sleep(2)

                except Exception as e:
                    print(f"[ERROR] Voice assistant error: {e}")
                    self.root.after(0, lambda: self.status_bar.config(text=f"Voice error: {e}"))
                    break

        except Exception as e:
            print(f"[ERROR] Failed to start voice assistant: {e}")
            self.root.after(0, lambda: self.status_bar.config(text=f"Failed to start: {e}"))
        finally:
            self.root.after(0, self._reset_voice_state)

    def _reset_voice_state(self):
        """Reset voice state after stopping"""
        if not self.is_listening:
            self.voice_indicator.itemconfig(self.voice_circle, fill='#95a5a6')
            self.status_label.config(text="Voice Assistant Stopped")

    def test_voice_recognition(self):
        """Test voice recognition functionality"""
        messagebox.showinfo("Voice Test", "Voice recognition test feature would be implemented here.")

    def test_tts(self):
        """Test TTS functionality"""
        try:
            from interruptible_tts import InterruptibleTTS
            tts = InterruptibleTTS()
            tts.speak("This is a test of the text-to-speech system.")
            messagebox.showinfo("TTS Test", "TTS test completed successfully!")
        except Exception as e:
            messagebox.showerror("TTS Test Error", f"TTS test failed: {e}")

    def check_dependencies(self):
        """Check if all dependencies are installed"""
        missing_deps = []

        try:
            import vosk
        except ImportError:
            missing_deps.append("vosk")

        try:
            import sounddevice
        except ImportError:
            missing_deps.append("sounddevice")


        if missing_deps:
            messagebox.showwarning(
                "Missing Dependencies",
                f"The following dependencies are missing:\n\n{chr(10).join(missing_deps)}\n\nPlease install them using pip."
            )
        else:
            messagebox.showinfo("Dependencies Check", "All required dependencies are installed!")

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Voice Assistant Settings",
            "Voice Assistant Configuration GUI\n\n"
            "Configure all aspects of your voice assistant:\n"
            "- Assistant settings (name, version, commands)\n"
            "- Language model settings\n"
            "- Text-to-speech configuration\n"
            "- Voice recognition settings\n"
            "- Memory management\n"
            "- API integrations (Weather, Calendar, Spotify, Notion)\n"
            "- Service configurations"
        )

    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

# Main entry point
if __name__ == "__main__":
    try:
        gui = VoiceAssistantGUI()
        gui.run()
    except Exception as e:
        print(f"[ERROR] GUI failed to start: {e}")
        messagebox.showerror("GUI Error", f"Failed to start GUI: {e}")

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Chat", command=self.export_chat)
        file_menu.add_command(label="Clear Chat", command=self.clear_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="API Keys", command=lambda: self.notebook.select(1))
        settings_menu.add_command(label="Voice Settings", command=lambda: self.notebook.select(2))
        settings_menu.add_command(label="Preferences", command=lambda: self.notebook.select(3))
        settings_menu.add_command(label="IoT Control", command=lambda: self.notebook.select(4))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_interface(self):
        """Create the main tabbed interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="Chat")

        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")

        # Voice tab
        self.voice_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.voice_frame, text="Voice")

        # IoT tab
        self.iot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.iot_frame, text="IoT Control")

        # Status tab
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="Status")

    def create_chat_interface(self):
        """Create the chat interface"""
        # Main chat container
        chat_container = tk.Frame(self.chat_frame, bg='#34495e')
        chat_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat display area with modern styling
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Helvetica", 11),
            bg='#ffffff',
            fg='#2c3e50',
            borderwidth=0,
            relief=tk.FLAT
        )

        # Configure chat display tags for styling
        self.chat_display.tag_configure("assistant", foreground="#7f8c8d", font=("Helvetica", 10, "italic"))
        self.chat_display.tag_configure("assistant_message", foreground="#2c3e50", font=("Helvetica", 11))
        self.chat_display.tag_configure("user", foreground="#3498db", font=("Helvetica", 10, "bold"))
        self.chat_display.tag_configure("user_message", foreground="#2c3e50", font=("Helvetica", 11))
        self.chat_display.tag_configure("timestamp", foreground="#95a5a6", font=("Helvetica", 8))
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_display.config(state=tk.DISABLED)

        # Input area
        input_frame = tk.Frame(chat_container, bg='#34495e')
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.message_input = tk.Text(
            input_frame,
            height=3,
            font=("Helvetica", 10),
            bg='white',
            fg='#2c3e50'
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_input.bind('<Return>', self.send_message)
        self.message_input.bind('<Shift-Return>', self.insert_newline)

        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg='#3498db',
            fg='white',
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=20
        )
        self.send_button.pack(side=tk.RIGHT)

        # Voice button
        self.voice_button = tk.Button(
            input_frame,
            text="🎤 Voice",
            command=self.toggle_voice_listening,
            bg='#95a5a6',
            fg='white',
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            state=tk.NORMAL
        )
        self.voice_button.pack(side=tk.RIGHT, padx=(0, 10))

        # Voice activity indicator
        self.voice_indicator = tk.Canvas(
            input_frame,
            width=20,
            height=20,
            bg='#34495e',
            highlightthickness=0
        )
        self.voice_indicator.pack(side=tk.RIGHT, padx=(0, 10))
        self.voice_circle = self.voice_indicator.create_oval(5, 5, 15, 15, fill='#95a5a6')

        # Control buttons
        control_frame = tk.Frame(chat_container, bg='#34495e')
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.start_button = tk.Button(
            control_frame,
            text="▶ Start Assistant",
            command=self.start_assistant,
            bg='#27ae60',
            fg='white',
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=15
        )
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(
            control_frame,
            text="⏹ Stop Assistant",
            command=self.stop_assistant,
            bg='#e74c3c',
            fg='white',
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(10, 0))

    def create_settings_interface(self):
        """Create the settings interface"""
        # Create notebook for settings tabs
        settings_notebook = ttk.Notebook(self.settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # API Keys tab
        api_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(api_frame, text="API Keys")

        # Voice Settings tab
        voice_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(voice_frame, text="Voice Settings")

        # Preferences tab
        prefs_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(prefs_frame, text="Preferences")

        # IoT tab
        self.iot_settings_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(self.iot_settings_frame, text="IoT Control")

        self.create_api_settings(api_frame)
        self.create_voice_settings(voice_frame)
        self.create_preferences_settings(prefs_frame)
        self.create_iot_chat_settings()

    def create_api_settings(self, parent):
        """Create API keys settings"""
        # OpenAI API Key
        openai_frame = tk.LabelFrame(parent, text="OpenAI API", padx=10, pady=10, bg='#ecf0f1')
        openai_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(openai_frame, text="API Key:", bg='#ecf0f1', font=("Helvetica", 10)).grid(row=0, column=0, sticky="w")
        self.openai_key_entry = tk.Entry(openai_frame, show="*", width=50, font=("Helvetica", 10))
        self.openai_key_entry.grid(row=0, column=1, padx=(10, 0), sticky="w")
        if config.get('openai.api_key'):
            self.openai_key_entry.insert(0, config.get('openai.api_key'))

        # Google Calendar API
        calendar_frame = tk.LabelFrame(parent, text="Google Calendar API", padx=10, pady=10, bg='#ecf0f1')
        calendar_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(calendar_frame, text="Credentials File:", bg='#ecf0f1', font=("Helvetica", 10)).grid(row=0, column=0, sticky="w")
        self.calendar_creds_entry = tk.Entry(calendar_frame, width=40, font=("Helvetica", 10))
        self.calendar_creds_entry.grid(row=0, column=1, padx=(10, 0), sticky="w")
        if config.get('google.credentials_file'):
            self.calendar_creds_entry.insert(0, config.get('google.credentials_file'))

        tk.Button(calendar_frame, text="Browse", command=self.browse_credentials).grid(row=0, column=2, padx=(10, 0))

        # Save button
        tk.Button(parent, text="Save API Settings", command=self.save_api_settings,
                 bg='#3498db', fg='white', font=("Helvetica", 10, "bold")).pack(pady=10)

    def create_voice_settings(self, parent):
        """Create voice settings"""
        # Voice selection
        voice_frame = tk.LabelFrame(parent, text="Voice Settings", padx=10, pady=10, bg='#ecf0f1')
        voice_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(voice_frame, text="Voice:", bg='#ecf0f1', font=("Helvetica", 10)).grid(row=0, column=0, sticky="w")
        self.voice_var = tk.StringVar(value=config.get('tts.voice', 'en_GB-southern_english_female-low'))
        voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, width=30)
        voice_combo['values'] = ['en_GB-southern_english_female-low', 'en_US-lessac-medium', 'en_US-hfc-female', 'en_US-hfc-male']
        voice_combo.grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Voice speed
        tk.Label(voice_frame, text="Speed:", bg='#ecf0f1', font=("Helvetica", 10)).grid(row=1, column=0, sticky="w")
        self.speed_var = tk.DoubleVar(value=config.get('tts.speed', 1.0))
        speed_scale = tk.Scale(voice_frame, from_=0.5, to=2.0, resolution=0.1,
                              orient=tk.HORIZONTAL, variable=self.speed_var, bg='#ecf0f1')
        speed_scale.grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Save button
        tk.Button(parent, text="Save Voice Settings", command=self.save_voice_settings,
                 bg='#3498db', fg='white', font=("Helvetica", 10, "bold")).pack(pady=10)

    def create_preferences_settings(self, parent):
        """Create general preferences"""
        # General settings
        general_frame = tk.LabelFrame(parent, text="General Preferences", padx=10, pady=10, bg='#ecf0f1')
        general_frame.pack(fill=tk.X, padx=10, pady=5)

        # Assistant name
        tk.Label(general_frame, text="Assistant Name:", bg='#ecf0f1', font=("Helvetica", 10)).grid(row=0, column=0, sticky="w")
        self.assistant_name_var = tk.StringVar(value=config.get('assistant.name', 'Assistant'))
        tk.Entry(general_frame, textvariable=self.assistant_name_var, width=30, font=("Helvetica", 10)).grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Weather location
        tk.Label(general_frame, text="Default Location:", bg='#ecf0f1', font=("Helvetica", 10)).grid(row=1, column=0, sticky="w")
        self.weather_location_var = tk.StringVar(value=config.get('weather.default_location', 'Guildford'))
        tk.Entry(general_frame, textvariable=self.weather_location_var, width=30, font=("Helvetica", 10)).grid(row=1, column=1, padx=(10, 0), sticky="w")

        # Save button
        tk.Button(parent, text="Save Preferences", command=self.save_preferences,
                 bg='#3498db', fg='white', font=("Helvetica", 10, "bold")).pack(pady=10)

    def create_iot_chat_settings(self):
        """Create IoT control settings for chat interface"""
        # Create IoT control interface in the IoT settings tab
        self.create_iot_control_interface(self.iot_settings_frame)

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = tk.Label(
            self.root,
            text="Voice Assistant Ready | Click 'Start Assistant' to begin",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg='#34495e',
            fg='white',
            font=("Helvetica", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def add_message(self, sender, message, timestamp=None):
        """Add a message to the chat display"""
        if timestamp is None:
            timestamp = datetime.now()

        # Format timestamp
        time_str = timestamp.strftime("%H:%M:%S")

        # Add to conversation history
        self.conversation_history.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp.isoformat()
        })

        # Update display
        self.chat_display.config(state=tk.NORMAL)

        # Add timestamp
        self.chat_display.insert(tk.END, f"[{time_str}] ", "timestamp")

        # Add sender and message
        if sender == "Assistant":
            self.chat_display.insert(tk.END, "Jarvis: ", "assistant")
            self.chat_display.insert(tk.END, f"{message}\n", "assistant_message")
        else:
            self.chat_display.insert(tk.END, "You: ", "user")
            self.chat_display.insert(tk.END, f"{message}\n", "user_message")

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

        # Speak the assistant's response
        if sender == "Assistant":
            # Use threading to avoid blocking the GUI
            speak_thread = threading.Thread(
                target=lambda: self.tts.speak(message, check_interrupts=True),
                daemon=True
            )
            speak_thread.start()

    def send_message(self, event=None):
        """Send a text message"""
        message = self.message_input.get("1.0", tk.END).strip()
        if message:
            self.add_message("User", message)
            self.message_input.delete("1.0", tk.END)
            self.process_user_message(message)

    def insert_newline(self, event=None):
        """Insert newline in text input"""
        self.message_input.insert(tk.INSERT, "\n")
        return "break"

    def toggle_voice_listening(self):
        """Toggle voice listening mode"""
        if self.is_listening:
            self.stop_voice_listening()
        else:
            self.start_voice_listening()

    def start_voice_listening(self):
        """Start voice listening"""
        if not self.is_listening:
            self.is_listening = True
            self.voice_button.config(text="🔴 Stop Voice", bg='#e74c3c')
            self.voice_indicator.itemconfig(self.voice_circle, fill='#e74c3c')
            self.status_bar.config(text="Listening for voice commands...")
            # Start voice recognition in a separate thread
            voice_thread = threading.Thread(target=self._voice_listening_thread, daemon=True)
            voice_thread.start()

    def stop_voice_listening(self):
        """Stop voice listening"""
        if self.is_listening:
            self.is_listening = False
            self.voice_button.config(text="🎤 Voice", bg='#95a5a6')
            self.voice_indicator.itemconfig(self.voice_circle, fill='#95a5a6')
            self.status_bar.config(text="Voice listening stopped")

    def _voice_listening_thread(self):
        """Voice listening thread"""
        try:
            # Listen for wake word first
            self.root.after(0, lambda: self.status_bar.config(text="Listening for wake word..."))

            # This would need to be implemented based on your voice recognition setup
            # For now, we'll simulate voice command processing
            self._simulate_voice_processing()

        except Exception as e:
            print(f"[ERROR] Voice listening error: {e}")
            self.root.after(0, lambda: self.status_bar.config(text=f"Voice error: {e}"))
        finally:
            self.root.after(0, self._reset_voice_state)

    def process_voice_command(self, command):
        """Process a voice command"""
        if command and self.is_listening:
            self.root.after(0, lambda: self.add_message("User", f"[Voice] {command}"))
            self.root.after(0, lambda: self.process_user_message(command))

    def _simulate_voice_processing(self):
        """Simulate voice command processing"""
        # This is a placeholder for actual voice recognition
        # In a real implementation, this would integrate with your voice recognition system
        import time
        time.sleep(2)  # Simulate listening time

        # Simulate a voice command
        if self.is_listening:
            self.root.after(0, lambda: self.add_message("User", "[Voice Command] Hello, how are you?"))
            self.root.after(0, lambda: self.process_user_message("Hello, how are you?"))

    def integrate_voice_recognition(self):
        """Integrate with the existing voice recognition system"""
        # This method would integrate with your existing voice_recognition.py
        # For now, we'll use a simplified version
        pass

    def _reset_voice_state(self):
        """Reset voice state after listening"""
        if self.is_listening:
            self.is_listening = False
            self.voice_button.config(text="🎤 Voice", bg='#95a5a6')
            self.voice_indicator.itemconfig(self.voice_circle, fill='#95a5a6')
            self.status_bar.config(text="Voice listening stopped")

    def start_assistant(self):
        """Start the assistant"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_bar.config(text="Assistant started - Ready for commands")
        self.add_message("Assistant", "Hello! I'm Jarvis, your voice assistant. How can I help you today?")

    def stop_assistant(self):
        """Stop the assistant"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_bar.config(text="Assistant stopped")
        self.stop_voice_listening()

    def process_user_message(self, message):
        """Process a user message"""
        try:
            # Parse intent
            intent = self.intent_parser.parse_intent(message)

            # Handle different intents
            if intent == "memory_recall" or self.intent_parser.is_memory_related(message):
                response = self.llm.get_response_with_memory_search(message)
                self.memory.save_interaction(message, response, "memory_query")

            elif intent == "weather":
                location = config.get('weather.default_location', 'Guildford')
                target_time = dateparser.parse(message) if any(word in message.lower() for word in ['today', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']) else None
                response = get_weather(location, target_time)
                self.memory.save_interaction(message, response, "weather")

            elif intent == "time":
                response = get_time()
                self.memory.save_interaction(message, response, "time")

            elif intent == "joke":
                response = tell_joke()
                self.memory.save_interaction(message, response, "joke")

            # Add more intent handlers as needed...

            else:
                # General conversation
                response = self.llm.get_response(message, use_memory_context=True)
                self.memory.save_interaction(message, response, "general")

            # Add response to chat
            self.add_message("Assistant", response)

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.add_message("Assistant", error_msg)
            print(f"[ERROR] Processing message: {e}")

    def process_messages(self):
        """Process messages from queue (for threading)"""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                self.add_message("Assistant", message)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_messages)

    def save_api_settings(self):
        """Save API settings"""
        # Update config
        config.set('openai.api_key', self.openai_key_entry.get())
        config.set('google.credentials_file', self.calendar_creds_entry.get())

        # Save to file
        config.save()
        messagebox.showinfo("Settings Saved", "API settings have been saved successfully!")

    def save_voice_settings(self):
        """Save voice settings"""
        config.set('tts.voice', self.voice_var.get())
        config.set('tts.speed', self.speed_var.get())
        config.save()
        messagebox.showinfo("Settings Saved", "Voice settings have been saved successfully!")

    def save_preferences(self):
        """Save general preferences"""
        config.set('assistant.name', self.assistant_name_var.get())
        config.set('weather.default_location', self.weather_location_var.get())
        config.save()
        messagebox.showinfo("Settings Saved", "Preferences have been saved successfully!")

    def browse_credentials(self):
        """Browse for Google credentials file"""
        filename = filedialog.askopenfilename(
            title="Select Google Credentials File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.calendar_creds_entry.delete(0, tk.END)
            self.calendar_creds_entry.insert(0, filename)

    def load_conversation_history(self):
        """Load conversation history from memory"""
        try:
            # Get recent interactions from memory
            interactions = self.memory.get_recent_interactions(50)

            for interaction in interactions:
                timestamp = datetime.fromisoformat(interaction.get('timestamp', datetime.now().isoformat()))
                sender = "Assistant" if interaction.get('type') == 'assistant_response' else "User"
                message = interaction.get('user_input', interaction.get('response', ''))

                if message:
                    self.add_message(sender, message, timestamp)

        except Exception as e:
            print(f"[WARN] Could not load conversation history: {e}")

    def export_chat(self):
        """Export chat to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Voice Assistant Chat Export\n")
                    f.write("=" * 50 + "\n\n")

                    for msg in self.conversation_history:
                        timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{timestamp}] {msg['sender']}: {msg['message']}\n")

                messagebox.showinfo("Export Complete", f"Chat exported to {filename}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export chat: {e}")

    def clear_chat(self):
        """Clear chat display"""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.conversation_history.clear()

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Voice Assistant",
            "Voice Assistant GUI\n\n"
            "A modern interface for voice-controlled AI assistant\n"
            "Features:\n"
            "- Voice and text chat\n"
            "- Settings management\n"
            "- Conversation history\n"
            "- Multiple AI integrations"
        )

    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

# Main entry point
if __name__ == "__main__":
    try:
        gui = VoiceAssistantGUI()
        gui.run()
    except Exception as e:
        print(f"[ERROR] GUI failed to start: {e}")
        # Fallback to command line interface
        print("[INFO] Falling back to command line interface...")
        import main
        main.main()