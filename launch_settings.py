#!/usr/bin/env python3
"""
Settings GUI Launcher
Separate launcher for the voice assistant settings GUI
"""

def launch_settings():
    """Launch the settings GUI"""
    try:
        from settings_gui import SettingsWindow
        print("[INFO] Launching Voice Assistant Settings GUI...")
        app = SettingsWindow()
        app.window.mainloop()
    except ImportError as e:
        print(f"[ERROR] Settings GUI not available: {e}")
        print("Make sure all required packages are installed.")
    except Exception as e:
        print(f"[ERROR] Failed to launch settings GUI: {e}")
        print("Try running the main voice assistant with: python main.py")

if __name__ == "__main__":
    launch_settings()