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

        # Start status updates
        self.start_status_updates()

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
        self.setup_iot_tab()
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

    def setup_iot_tab(self):
        """Setup the IoT/Tapo devices settings tab"""
        frame = self.create_tab_frame(self.notebook, "IoT Devices")

        # IoT Status
        status_frame = tk.Frame(frame, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, pady=10)

        tk.Label(status_frame, text="IoT System Status:", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='#ffffff').pack(anchor='w')

        self.iot_status_label = tk.Label(status_frame, text="Checking...",
                                       font=('Arial', 10), bg='#2b2b2b', fg='#ffa500')
        self.iot_status_label.pack(anchor='w', pady=(5, 0))

        # Tapo Device Scanning
        scan_frame = tk.Frame(frame, bg='#2b2b2b')
        scan_frame.pack(fill=tk.X, pady=10)

        tk.Label(scan_frame, text="Tapo Device Discovery:", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='#ffffff').pack(anchor='w')

        scan_button = tk.Button(
            scan_frame,
            text="Scan Network for Tapo Devices",
            command=self.scan_tapo_devices,
            font=('Arial', 10),
            bg='#0078d4',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        scan_button.pack(anchor='w', pady=(5, 0))

        self.scan_status_label = tk.Label(scan_frame, text="",
                                        font=('Arial', 9), bg='#2b2b2b', fg='#888888')
        self.scan_status_label.pack(anchor='w', pady=(5, 0))

        # Tapo Devices List
        devices_frame = tk.Frame(frame, bg='#2b2b2b')
        devices_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(devices_frame, text="Tapo Devices:", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='#ffffff').pack(anchor='w', pady=(0, 10))

        # Create a frame for the devices list with scrollbar
        devices_list_frame = tk.Frame(devices_frame, bg='#2b2b2b')
        devices_list_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas and scrollbar for scrollable device list
        self.devices_canvas = tk.Canvas(devices_list_frame, bg='#2b2b2b', highlightthickness=0)
        devices_scrollbar = ttk.Scrollbar(devices_list_frame, orient="vertical", command=self.devices_canvas.yview)
        self.devices_scrollable_frame = tk.Frame(self.devices_canvas, bg='#2b2b2b')

        self.devices_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.devices_canvas.configure(scrollregion=self.devices_canvas.bbox("all"))
        )

        self.devices_canvas.create_window((0, 0), window=self.devices_scrollable_frame, anchor="nw")
        self.devices_canvas.configure(yscrollcommand=devices_scrollbar.set)

        self.devices_canvas.pack(side="left", fill="both", expand=True)
        devices_scrollbar.pack(side="right", fill="y")

        # Store reference for updating device list
        self.tapo_devices_frame = self.devices_scrollable_frame

        # Refresh devices button
        refresh_frame = tk.Frame(frame, bg='#2b2b2b')
        refresh_frame.pack(fill=tk.X, pady=10)

        refresh_button = tk.Button(
            refresh_frame,
            text="Refresh Device Status",
            command=self.refresh_tapo_devices,
            font=('Arial', 10),
            bg='#28a745',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        refresh_button.pack(anchor='w')

        # IoT Instructions
        instructions_frame = tk.Frame(frame, bg='#1e1e1e', relief=tk.FLAT, bd=1)
        instructions_frame.pack(fill=tk.X, pady=20, padx=5)

        instructions_title = tk.Label(instructions_frame, text="Tapo Setup Instructions:",
                                    font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#87CEEB')
        instructions_title.pack(anchor='w', padx=10, pady=(10, 5))

        instructions_text = """1. Ensure your Tapo devices are powered on and connected to WiFi
2. Click "Scan Network for Tapo Devices" to discover devices
3. Configure discovered devices with your Tapo credentials
4. Use the device controls to test functionality
5. Save your configuration to config.json"""

        instructions_label = tk.Label(instructions_frame, text=instructions_text,
                                    font=('Arial', 9), bg='#1e1e1e', fg='#ffffff',
                                    justify=tk.LEFT, wraplength=500)
        instructions_label.pack(anchor='w', padx=10, pady=(0, 10))

        # Manual Configuration Section
        manual_frame = tk.Frame(frame, bg='#2b2b2b')
        manual_frame.pack(fill=tk.X, pady=10)

        tk.Label(manual_frame, text="Manual Device Configuration:", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='#ffffff').pack(anchor='w')

        manual_button = tk.Button(
            manual_frame,
            text="Add Tapo Device Manually",
            command=self.show_manual_device_config,
            font=('Arial', 10),
            bg='#6f42c1',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        manual_button.pack(anchor='w', pady=(5, 0))

        self.manual_config_frame = tk.Frame(frame, bg='#2b2b2b')
        # Don't pack yet, will be shown when needed

    def show_manual_config_option(self):
        """Show manual configuration option when scan fails"""
        try:
            # Clear existing devices
            for widget in self.tapo_devices_frame.winfo_children():
                widget.destroy()

            # Show manual configuration message
            manual_message = tk.Label(
                self.tapo_devices_frame,
                text="Automatic discovery couldn't find your devices.\nYou can add them manually using the button below.",
                font=('Arial', 10),
                bg='#2b2b2b',
                fg='#ffa500',
                justify=tk.CENTER
            )
            manual_message.pack(pady=10)

            manual_button = tk.Button(
                self.tapo_devices_frame,
                text="Add Tapo Device Manually",
                command=self.show_manual_device_config,
                font=('Arial', 12, 'bold'),
                bg='#6f42c1',
                fg='#ffffff',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2',
                padx=20,
                pady=10
            )
            manual_button.pack(pady=(10, 20))

        except Exception as e:
            print(f"Error showing manual config option: {e}")

    def show_manual_device_config(self):
        """Show manual device configuration form"""
        try:
            # Hide the manual config frame if it's already visible
            try:
                self.manual_config_frame.pack_forget()
            except:
                pass

            # Clear existing devices
            for widget in self.tapo_devices_frame.winfo_children():
                widget.destroy()

            # Create manual configuration form
            config_frame = tk.Frame(self.tapo_devices_frame, bg='#404040', relief=tk.FLAT, bd=1)
            config_frame.pack(fill=tk.X, pady=10, padx=5)

            # Title
            title_label = tk.Label(
                config_frame,
                text="Add Tapo Device Manually",
                font=('Arial', 12, 'bold'),
                bg='#404040',
                fg='#ffffff'
            )
            title_label.pack(anchor='w', padx=10, pady=10)

            # Configuration fields
            fields_frame = tk.Frame(config_frame, bg='#404040')
            fields_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            # Device Name
            name_frame = tk.Frame(fields_frame, bg='#404040')
            name_frame.pack(fill=tk.X, pady=5)

            tk.Label(name_frame, text="Device Name:", font=('Arial', 10),
                    bg='#404040', fg='#ffffff', width=15, anchor='w').pack(side=tk.LEFT)

            name_var = tk.StringVar()
            name_entry = tk.Entry(name_frame, textvariable=name_var, font=('Arial', 10),
                                bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1)
            name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # IP Address
            ip_frame = tk.Frame(fields_frame, bg='#404040')
            ip_frame.pack(fill=tk.X, pady=5)

            tk.Label(ip_frame, text="IP Address:", font=('Arial', 10),
                    bg='#404040', fg='#ffffff', width=15, anchor='w').pack(side=tk.LEFT)

            ip_var = tk.StringVar()
            ip_entry = tk.Entry(ip_frame, textvariable=ip_var, font=('Arial', 10),
                              bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1)
            ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # Username
            user_frame = tk.Frame(fields_frame, bg='#404040')
            user_frame.pack(fill=tk.X, pady=5)

            tk.Label(user_frame, text="Username:", font=('Arial', 10),
                    bg='#404040', fg='#ffffff', width=15, anchor='w').pack(side=tk.LEFT)

            user_var = tk.StringVar()
            user_entry = tk.Entry(user_frame, textvariable=user_var, font=('Arial', 10),
                                bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1)
            user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # Password
            pass_frame = tk.Frame(fields_frame, bg='#404040')
            pass_frame.pack(fill=tk.X, pady=5)

            tk.Label(pass_frame, text="Password:", font=('Arial', 10),
                    bg='#404040', fg='#ffffff', width=15, anchor='w').pack(side=tk.LEFT)

            pass_var = tk.StringVar()
            pass_entry = tk.Entry(pass_frame, textvariable=pass_var, font=('Arial', 10),
                                bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1, show="*")
            pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # Model
            model_frame = tk.Frame(fields_frame, bg='#404040')
            model_frame.pack(fill=tk.X, pady=5)

            tk.Label(model_frame, text="Model:", font=('Arial', 10),
                    bg='#404040', fg='#ffffff', width=15, anchor='w').pack(side=tk.LEFT)

            model_var = tk.StringVar(value="L530B")
            model_combo = ttk.Combobox(model_frame, textvariable=model_var,
                                     values=["L530B", "L530", "L510", "L900", "L610", "L630"], state="readonly",
                                     font=('Arial', 10), width=10)
            model_combo.pack(side=tk.LEFT, padx=(5, 0))

            # Buttons
            button_frame = tk.Frame(config_frame, bg='#404040')
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            def test_manual_device():
                if not name_var.get() or not ip_var.get() or not user_var.get() or not pass_var.get():
                    messagebox.showwarning("Warning", "Please fill in all fields")
                    return

                self.test_tapo_device(ip_var.get(), name_var.get(), user_var.get(),
                                    pass_var.get(), model_var.get())

            def add_manual_device():
                if not name_var.get() or not ip_var.get() or not user_var.get() or not pass_var.get():
                    messagebox.showwarning("Warning", "Please fill in all fields")
                    return

                self.add_tapo_to_config(ip_var.get(), name_var.get(), user_var.get(),
                                      pass_var.get(), model_var.get())

            test_button = tk.Button(
                button_frame,
                text="Test Connection",
                command=test_manual_device,
                font=('Arial', 10),
                bg='#ffc107',
                fg='#000000',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2'
            )
            test_button.pack(side=tk.LEFT, padx=(0, 5))

            add_button = tk.Button(
                button_frame,
                text="Add Device",
                command=add_manual_device,
                font=('Arial', 10),
                bg='#28a745',
                fg='#ffffff',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2'
            )
            add_button.pack(side=tk.LEFT)

            back_button = tk.Button(
                button_frame,
                text="Back to Scan",
                command=self.back_to_scan,
                font=('Arial', 10),
                bg='#6c757d',
                fg='#ffffff',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2'
            )
            back_button.pack(side=tk.RIGHT)

            # Store variables for access
            config_frame.vars = {
                'name': name_var,
                'ip': ip_var,
                'username': user_var,
                'password': pass_var,
                'model': model_var
            }

        except Exception as e:
            print(f"Error showing manual config: {e}")

    def back_to_scan(self):
        """Go back to the scan results/devices list"""
        try:
            # Hide manual config frame
            self.manual_config_frame.pack_forget()

            # Refresh the device list
            self.refresh_tapo_devices()

        except Exception as e:
            print(f"Error going back to scan: {e}")

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
            self.check_iot_status()
            
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

        # Check IoT status
        self.check_iot_status()
    
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

    def check_iot_status(self):
        """Check IoT system status"""
        try:
            from iot_manager import iot_manager
            devices = iot_manager.list_devices()

            # Count different device types
            tapo_devices = [d for d in devices if d.protocol == 'tapo']
            other_devices = [d for d in devices if d.protocol != 'tapo']

            if devices:
                status_parts = []
                if tapo_devices:
                    status_parts.append(f"{len(tapo_devices)} Tapo")
                if other_devices:
                    status_parts.append(f"{len(other_devices)} other")

                device_summary = " + ".join(status_parts) if len(status_parts) > 1 else f"{len(devices)} total"
                self.iot_status_label.config(text=f"✓ Connected - {device_summary} devices configured", fg='#28a745')
            else:
                self.iot_status_label.config(text="⚠ No devices configured", fg='#ffa500')

        except ImportError as e:
            self.iot_status_label.config(text=f"⚠ IoT not available: {str(e)}", fg='#ffa500')
        except Exception as e:
            # Handle specific errors more gracefully
            error_msg = str(e)
            if "TapoLight" in error_msg:
                # Check if tapo package is actually available
                try:
                    import tapo
                    self.iot_status_label.config(text="✓ IoT connected with Tapo support", fg='#28a745')
                except ImportError:
                    self.iot_status_label.config(text="✓ IoT connected (Tapo package not installed)", fg='#28a745')
            else:
                self.iot_status_label.config(text=f"✗ IoT Error: {error_msg}", fg='#dc3545')

    def scan_tapo_devices(self):
        """Scan network for Tapo devices (runs in separate thread)"""
        try:
            self.scan_status_label.config(text="Scanning network for Tapo devices...", fg='#ffa500')
            self.window.update()

            # Run scan in separate thread to avoid freezing GUI
            import threading
            scan_thread = threading.Thread(target=self._run_network_scan, daemon=True)
            scan_thread.start()

        except Exception as e:
            error_msg = f"Failed to start scan: {str(e)}"
            self.scan_status_label.config(text=error_msg, fg='#dc3545')
            print(f"Scan start error: {e}")

    def _run_network_scan(self):
        """Run the actual network scan (called from thread)"""
        try:
            # Update GUI to show scanning status
            def update_gui_text(text, color='#ffa500'):
                try:
                    self.scan_status_label.config(text=text, fg=color)
                    self.window.update()
                except:
                    pass  # GUI might be destroyed

            update_gui_text("Scanning network for Tapo devices...")

            import socket
            import ipaddress
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def get_network_interfaces():
                """Get all local network interfaces and their ranges"""
                interfaces = []
                try:
                    # Get all network interfaces
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)

                    # Get network interfaces
                    import netifaces
                    for interface in netifaces.interfaces():
                        try:
                            addresses = netifaces.ifaddresses(interface)
                            if netifaces.AF_INET in addresses:
                                for addr in addresses[netifaces.AF_INET]:
                                    ip = addr['addr']
                                    if not ip.startswith('127.'):
                                        # Calculate network range
                                        netmask = addr.get('netmask', '255.255.255.0')
                                        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                                        interfaces.append((ip, network))
                        except:
                            continue
                except ImportError:
                    # Fallback if netifaces not available
                    local_ip = socket.gethostbyname(socket.gethostname())
                    network_prefix = '.'.join(local_ip.split('.')[:-1])
                    network = ipaddress.IPv4Network(f"{network_prefix}.0/24", strict=False)
                    interfaces.append((local_ip, network))

                return interfaces

            def scan_ip_ports(ip, ports=[9999, 80, 443, 554, 8888]):
                """Scan a single IP for multiple ports used by Tapo devices"""
                for port in ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)  # Increased timeout

                        result = sock.connect_ex((str(ip), port))
                        sock.close()

                        if result == 0:
                            return str(ip), port
                    except socket.error as e:
                        # Log specific socket errors for debugging
                        print(f"Socket error scanning {ip}:{port} - {e}")
                        continue
                    except Exception as e:
                        print(f"Unexpected error scanning {ip}:{port} - {e}")
                        continue
                return None, None

            def scan_network_range(network):
                """Scan a network range for Tapo devices"""
                found_devices = []

                # Use more conservative worker count to avoid overwhelming network
                max_workers = min(30, network.num_addresses - 2)  # Reserve network and broadcast

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_ip = {executor.submit(scan_ip_ports, ip): ip for ip in network.hosts()}

                    for future in as_completed(future_to_ip, timeout=60):  # 60 second overall timeout
                        try:
                            result = future.result(timeout=5)
                            if result[0]:
                                found_devices.append(result[0])
                        except Exception:
                            continue  # Skip failed scans

                return found_devices

            # Get all network interfaces
            interfaces = get_network_interfaces()
            all_found_devices = []

            for local_ip, network in interfaces:
                update_gui_text(f"Scanning {network}...")

                try:
                    devices_in_network = scan_network_range(network)
                    all_found_devices.extend(devices_in_network)
                except Exception as e:
                    print(f"Error scanning network {network}: {e}")

            # Remove duplicates
            unique_devices = list(set(all_found_devices))

            if unique_devices:
                update_gui_text(f"Found {len(unique_devices)} potential Tapo devices", '#28a745')
                # Use after method to safely update GUI from thread
                self.window.after(0, lambda: self.display_found_devices(unique_devices))
            else:
                update_gui_text("No Tapo devices found. Try manual configuration.", '#dc3545')
                # Use after method to safely update GUI from thread
                self.window.after(0, self.show_manual_config_option)

        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            print(f"Tapo scan error: {e}")  # Debug output
            # Use after method to safely update GUI from thread
            self.window.after(0, lambda: self.show_manual_config_option())

    def display_found_devices(self, devices):
        """Display found Tapo devices in the GUI"""
        # Clear existing devices
        for widget in self.tapo_devices_frame.winfo_children():
            widget.destroy()

        if not devices:
            no_devices_label = tk.Label(
                self.tapo_devices_frame,
                text="No devices found",
                font=('Arial', 10),
                bg='#2b2b2b',
                fg='#888888'
            )
            no_devices_label.pack(pady=10)
            return

        # Display each found device
        for i, ip in enumerate(devices):
            device_frame = tk.Frame(self.tapo_devices_frame, bg='#404040', relief=tk.FLAT, bd=1)
            device_frame.pack(fill=tk.X, pady=2, padx=5)

            # Device info
            info_label = tk.Label(
                device_frame,
                text=f"Tapo Device {i+1} - IP: {ip}",
                font=('Arial', 10, 'bold'),
                bg='#404040',
                fg='#ffffff'
            )
            info_label.pack(anchor='w', padx=10, pady=5)

            # Configuration frame
            config_frame = tk.Frame(device_frame, bg='#404040')
            config_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            # Device name
            name_frame = tk.Frame(config_frame, bg='#404040')
            name_frame.pack(fill=tk.X, pady=2)

            tk.Label(name_frame, text="Device Name:", font=('Arial', 9),
                    bg='#404040', fg='#cccccc', width=12, anchor='w').pack(side=tk.LEFT)

            name_var = tk.StringVar(value=f"Device {i+1}")
            name_entry = tk.Entry(name_frame, textvariable=name_var, font=('Arial', 9),
                                bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1)
            name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # Username
            user_frame = tk.Frame(config_frame, bg='#404040')
            user_frame.pack(fill=tk.X, pady=2)

            tk.Label(user_frame, text="Username:", font=('Arial', 9),
                    bg='#404040', fg='#cccccc', width=12, anchor='w').pack(side=tk.LEFT)

            user_var = tk.StringVar()
            user_entry = tk.Entry(user_frame, textvariable=user_var, font=('Arial', 9),
                                bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1)
            user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # Password
            pass_frame = tk.Frame(config_frame, bg='#404040')
            pass_frame.pack(fill=tk.X, pady=2)

            tk.Label(pass_frame, text="Password:", font=('Arial', 9),
                    bg='#404040', fg='#cccccc', width=12, anchor='w').pack(side=tk.LEFT)

            pass_var = tk.StringVar()
            pass_entry = tk.Entry(pass_frame, textvariable=pass_var, font=('Arial', 9),
                                bg='#2b2b2b', fg='#ffffff', relief=tk.FLAT, bd=1, show="*")
            pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            # Model selection
            model_frame = tk.Frame(config_frame, bg='#404040')
            model_frame.pack(fill=tk.X, pady=2)

            tk.Label(model_frame, text="Model:", font=('Arial', 9),
                    bg='#404040', fg='#cccccc', width=12, anchor='w').pack(side=tk.LEFT)

            model_var = tk.StringVar(value="L530")
            model_combo = ttk.Combobox(model_frame, textvariable=model_var,
                                     values=["L530", "L530B", "L510", "L900", "L610", "L630"], state="readonly",
                                     font=('Arial', 9), width=10)
            model_combo.pack(side=tk.LEFT, padx=(5, 0))

            # Control buttons frame
            control_frame = tk.Frame(device_frame, bg='#404040')
            control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            # Test connection button
            test_button = tk.Button(
                control_frame,
                text="Test",
                command=lambda ip=ip, name=name_var, user=user_var, pw=pass_var, model=model_var:
                    self.test_tapo_device(ip, name.get(), user.get(), pw.get(), model.get()),
                font=('Arial', 9),
                bg='#ffc107',
                fg='#000000',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2'
            )
            test_button.pack(side=tk.LEFT, padx=(0, 5))

            # Add to config button
            add_button = tk.Button(
                control_frame,
                text="Add to Config",
                command=lambda ip=ip, name=name_var, user=user_var, pw=pass_var, model=model_var:
                    self.add_tapo_to_config(ip, name.get(), user.get(), pw.get(), model.get()),
                font=('Arial', 9),
                bg='#28a745',
                fg='#ffffff',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2'
            )
            add_button.pack(side=tk.LEFT)

            # Store variables for access
            device_frame.vars = {
                'name': name_var,
                'username': user_var,
                'password': pass_var,
                'model': model_var,
                'ip': ip
            }

    def test_tapo_device(self, ip, name, username, password, model):
        """Test connection to a Tapo device"""
        try:
            from tapo_light_wrapper import TapoLight

            if not username or not password:
                messagebox.showwarning("Warning", "Please enter username and password")
                return

            if not ip:
                messagebox.showwarning("Warning", "Please enter IP address")
                return

            # Validate IP address format
            try:
                import ipaddress
                ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError:
                messagebox.showwarning("Warning", "Please enter a valid IP address")
                return

            def update_test_status(text, color='#ffa500'):
                try:
                    self.scan_status_label.config(text=text, fg=color)
                    self.window.update()
                except:
                    pass

            # Use after method for thread-safe GUI update
            self.window.after(0, lambda: update_test_status(f"Testing connection to {name}...", '#ffa500'))

            # Create test device
            device = TapoLight(
                device_id=f"test_{ip.replace('.', '_')}",
                name=name,
                username=username,
                password=password,
                ip=ip,
                model=model
            )

            # Test connection by trying to get device info
            import asyncio

            async def test_connection():
                try:
                    await device._ensure_connection()
                    info = await device.get_device_info()
                    return True, info
                except Exception as e:
                    error_msg = str(e)
                    # Provide specific troubleshooting for common errors
                    if "timeout" in error_msg.lower():
                        error_msg += "\n\nTroubleshooting: Check if device is powered on and IP address is correct."
                    elif "authentication" in error_msg.lower() or "password" in error_msg.lower():
                        error_msg += "\n\nTroubleshooting: Verify your Tapo app email and password are correct."
                    elif "network" in error_msg.lower() or "unreachable" in error_msg.lower():
                        error_msg += "\n\nTroubleshooting: Check network connectivity and firewall settings."
                    return False, error_msg

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, result = loop.run_until_complete(test_connection())
            loop.close()

            if success:
                # Use after method for thread-safe GUI update
                self.window.after(0, lambda: update_test_status(f"Successfully connected to {name}", '#28a745'))
                messagebox.showinfo("Success", f"Successfully connected to {name}!\n\nDevice Info: {result}")
            else:
                # Use after method for thread-safe GUI update
                self.window.after(0, lambda: update_test_status(f"Connection failed for {name}", '#dc3545'))
                messagebox.showerror("Connection Failed", f"Failed to connect to {name}:\n\n{result}")

        except ImportError:
            messagebox.showerror("Error", "Tapo package not installed. Please install with: pip install tapo")
        except Exception as e:
            error_msg = f"Test failed: {str(e)}"
            # Use after method for thread-safe GUI update
            self.window.after(0, lambda: update_test_status("Test failed", '#dc3545'))
            messagebox.showerror("Error", error_msg)
            print(f"Tapo device test error: {e}")  # Debug output

    def add_tapo_to_config(self, ip, name, username, password, model):
        """Add Tapo device to configuration"""
        try:
            if not username or not password:
                messagebox.showwarning("Warning", "Please enter username and password")
                return

            # Load current config
            try:
                with open('config.json', 'r') as f:
                    config_data = json.load(f)
            except FileNotFoundError:
                config_data = {"iot": {"devices": []}}

            # Ensure IoT section exists
            if 'iot' not in config_data:
                config_data['iot'] = {'devices': []}

            if 'devices' not in config_data['iot']:
                config_data['iot']['devices'] = []

            # Create device config
            device_config = {
                "id": f"tapo_{ip.replace('.', '_')}",
                "name": name,
                "type": "light",
                "protocol": "tapo",
                "username": username,
                "password": password,
                "ip": ip,
                "model": model,
                "config": {
                    "description": f"Tapo {model} at {ip}"
                }
            }

            # Add to config
            config_data['iot']['devices'].append(device_config)

            # Save config
            with open('config.json', 'w') as f:
                json.dump(config_data, f, indent=2)

            messagebox.showinfo("Success", f"Added {name} to configuration!\n\nPlease restart the application for changes to take effect.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add device to config: {str(e)}")

    def refresh_tapo_devices(self):
        """Refresh status of configured Tapo devices"""
        try:
            from iot_manager import iot_manager

            # Clear existing devices
            for widget in self.tapo_devices_frame.winfo_children():
                widget.destroy()

            # Get configured Tapo devices
            tapo_devices = []
            for device in iot_manager.list_devices():
                if device.protocol == 'tapo':
                    tapo_devices.append(device)

            if not tapo_devices:
                no_devices_label = tk.Label(
                    self.tapo_devices_frame,
                    text="No Tapo devices configured",
                    font=('Arial', 10),
                    bg='#2b2b2b',
                    fg='#888888'
                )
                no_devices_label.pack(pady=10)
                return

            # Display configured devices with controls
            for device in tapo_devices:
                self.create_device_control_widget(device)

        except Exception as e:
            error_label = tk.Label(
                self.tapo_devices_frame,
                text=f"Error refreshing devices: {str(e)}",
                font=('Arial', 9),
                bg='#2b2b2b',
                fg='#dc3545'
            )
            error_label.pack(pady=10)

    def create_device_control_widget(self, device):
        """Create control widget for a Tapo device"""
        device_frame = tk.Frame(self.tapo_devices_frame, bg='#404040', relief=tk.FLAT, bd=1)
        device_frame.pack(fill=tk.X, pady=2, padx=5)

        # Device header
        header_frame = tk.Frame(device_frame, bg='#404040')
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(header_frame, text=device.name.title(),
                font=('Arial', 11, 'bold'), bg='#404040', fg='#ffffff').pack(side=tk.LEFT)

        # Status indicator
        status_label = tk.Label(header_frame, text="●", font=('Arial', 10),
                              bg='#404040', fg='#ffa500')
        status_label.pack(side=tk.RIGHT)
        device_frame.status_indicator = status_label

        # Controls frame
        controls_frame = tk.Frame(device_frame, bg='#404040')
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # On/Off buttons
        button_frame = tk.Frame(controls_frame, bg='#404040')
        button_frame.pack(side=tk.LEFT, pady=5)

        on_button = tk.Button(
            button_frame,
            text="ON",
            command=lambda d=device: self.control_tapo_device(d, 'on'),
            font=('Arial', 9, 'bold'),
            bg='#28a745',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            width=6
        )
        on_button.pack(side=tk.LEFT, padx=(0, 5))

        off_button = tk.Button(
            button_frame,
            text="OFF",
            command=lambda d=device: self.control_tapo_device(d, 'off'),
            font=('Arial', 9, 'bold'),
            bg='#dc3545',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            width=6
        )
        off_button.pack(side=tk.LEFT)

        # Brightness control
        brightness_frame = tk.Frame(controls_frame, bg='#404040')
        brightness_frame.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(brightness_frame, text="Brightness:", font=('Arial', 9),
                bg='#404040', fg='#cccccc').pack(side=tk.LEFT)

        brightness_var = tk.StringVar(value="50")
        brightness_spin = tk.Spinbox(
            brightness_frame,
            from_=0,
            to=100,
            textvariable=brightness_var,
            width=5,
            font=('Arial', 9),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=1
        )
        brightness_spin.pack(side=tk.LEFT, padx=(5, 0))

        set_brightness_button = tk.Button(
            brightness_frame,
            text="Set",
            command=lambda d=device, b=brightness_var: self.control_tapo_device(d, 'brightness', b.get()),
            font=('Arial', 9),
            bg='#0078d4',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        set_brightness_button.pack(side=tk.LEFT, padx=(5, 0))

        # Color temperature control
        temp_frame = tk.Frame(controls_frame, bg='#404040')
        temp_frame.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(temp_frame, text="Temp (K):", font=('Arial', 9),
                bg='#404040', fg='#cccccc').pack(side=tk.LEFT)

        temp_var = tk.StringVar(value="4000")
        temp_spin = tk.Spinbox(
            temp_frame,
            from_=2200,
            to=6500,
            textvariable=temp_var,
            width=6,
            font=('Arial', 9),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=1
        )
        temp_spin.pack(side=tk.LEFT, padx=(5, 0))

        set_temp_button = tk.Button(
            temp_frame,
            text="Set",
            command=lambda d=device, t=temp_var: self.control_tapo_device(d, 'temperature', t.get()),
            font=('Arial', 9),
            bg='#0078d4',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        set_temp_button.pack(side=tk.LEFT, padx=(5, 0))

        # Preset buttons
        preset_frame = tk.Frame(device_frame, bg='#404040')
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        presets = [
            ("Reading", "#28a745", lambda d=device: self.set_tapo_preset(d, 'reading')),
            ("Relax", "#ffc107", lambda d=device: self.set_tapo_preset(d, 'relax')),
            ("Movie", "#17a2b8", lambda d=device: self.set_tapo_preset(d, 'movie'))
        ]

        for preset_name, color, command in presets:
            preset_button = tk.Button(
                preset_frame,
                text=preset_name,
                command=command,
                font=('Arial', 8),
                bg=color,
                fg='#ffffff',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2'
            )
            preset_button.pack(side=tk.LEFT, padx=(0, 5))

        # Store references for updates
        device_frame.vars = {
            'brightness': brightness_var,
            'temperature': temp_var
        }

        # Update status indicator
        self.update_device_status(device, device_frame)

    def control_tapo_device(self, device, action, value=None):
        """Control a Tapo device"""
        try:
            if action == 'on':
                from iot_manager import iot_manager
                result = iot_manager.turn_on_light(device.name)
                if "turned on" in result.lower():
                    messagebox.showinfo("Success", result)
                else:
                    messagebox.showerror("Error", result)

            elif action == 'off':
                from iot_manager import iot_manager
                result = iot_manager.turn_off_light(device.name)
                if "turned off" in result.lower():
                    messagebox.showinfo("Success", result)
                else:
                    messagebox.showerror("Error", result)

            elif action == 'brightness':
                from iot_manager import iot_manager
                result = iot_manager.set_brightness(device.name, int(value))
                if "brightness" in result.lower():
                    messagebox.showinfo("Success", result)
                else:
                    messagebox.showerror("Error", result)

            elif action == 'temperature':
                from tapo_light_wrapper import set_tapo_color_temperature
                result = set_tapo_color_temperature(device.name, int(value))
                if "color temperature" in result.lower():
                    messagebox.showinfo("Success", result)
                else:
                    messagebox.showerror("Error", result)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to control device: {str(e)}")

    def set_tapo_preset(self, device, preset):
        """Set Tapo device to a preset scene"""
        try:
            if preset == 'reading':
                # 80% brightness, 4000K
                self.control_tapo_device(device, 'brightness', '80')
                self.control_tapo_device(device, 'temperature', '4000')
                messagebox.showinfo("Success", f"Set {device.name} to reading mode")
            elif preset == 'relax':
                # 30% brightness, 2200K
                self.control_tapo_device(device, 'brightness', '30')
                self.control_tapo_device(device, 'temperature', '2200')
                messagebox.showinfo("Success", f"Set {device.name} to relax mode")
            elif preset == 'movie':
                # 40% brightness, 3000K
                self.control_tapo_device(device, 'brightness', '40')
                self.control_tapo_device(device, 'temperature', '3000')
                messagebox.showinfo("Success", f"Set {device.name} to movie mode")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to set preset: {str(e)}")

    def update_device_status(self, device, device_frame):
        """Update the status indicator for a device"""
        try:
            import asyncio

            async def check_device():
                try:
                    await device._ensure_connection()
                    info = await device.get_device_info()

                    # Update status indicator based on device state
                    if info.get('device_on', False):
                        device_frame.status_indicator.config(fg='#28a745')  # Green for on
                    else:
                        device_frame.status_indicator.config(fg='#dc3545')  # Red for off

                    return True
                except Exception:
                    device_frame.status_indicator.config(fg='#808080')  # Gray for error
                    return False

            # Run async check
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(check_device())
            loop.close()

        except Exception:
            device_frame.status_indicator.config(fg='#808080')  # Gray for error

    def start_status_updates(self):
        """Start periodic status updates for devices"""
        try:
            # Update IoT status every 30 seconds
            self.window.after(30000, self.check_iot_status)

            # Update device statuses every 10 seconds
            self.window.after(10000, self.update_all_device_statuses)

        except Exception as e:
            print(f"Error starting status updates: {e}")

    def update_all_device_statuses(self):
        """Update status for all displayed Tapo devices"""
        try:
            # Find all device frames and update their status
            for widget in self.tapo_devices_frame.winfo_children():
                if hasattr(widget, 'status_indicator'):
                    # This is a device frame, find the associated device
                    # For now, just update the indicator color
                    widget.status_indicator.config(fg='#ffa500')  # Orange for updating

            # Schedule next update
            self.window.after(10000, self.update_all_device_statuses)

        except Exception as e:
            print(f"Error updating device statuses: {e}")

def main():
    """Main entry point for testing the settings window"""
    app = SettingsWindow()
    app.window.mainloop()

if __name__ == "__main__":
    main()
