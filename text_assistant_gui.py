#!/usr/bin/env python3
"""
Text-based GUI interface for the Enhanced Assistant
Provides a simple windowed interface to interact with the assistant through text
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import queue
from datetime import datetime
from enhanced_memory import EnhancedMemory
from llm_interface import LLMInterface
from intent_parser import IntentParser
from commands import *
from config_manager import config

class TextAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{config.get('assistant.name', 'Assistant')} v{config.get('assistant.version', '1.0.0')} - Text Interface")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize assistant components
        self.memory = EnhancedMemory()
        self.llm = LLMInterface(memory=self.memory)
        self.intent_parser = IntentParser()
        
        # Queue for thread-safe GUI updates
        self.response_queue = queue.Queue()
        
        # Session tracking
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        self.setup_ui()
        self.setup_styling()
        
        # Start checking for responses from background threads
        self.check_response_queue()
        
        print(f"[INFO] Text GUI initialized for {config.get('assistant.name', 'Assistant')}")
    
    def setup_ui(self):
        """Setup the user interface components"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text=f"{config.get('assistant.name', 'Assistant')} Text Interface",
            font=('Arial', 16, 'bold'),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 10))
        
        # Chat history area
        self.chat_frame = tk.Frame(main_frame, bg='#2b2b2b')
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff',
            selectbackground='#404040',
            state=tk.DISABLED,
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input field
        self.input_field = tk.Entry(
            input_frame,
            font=('Arial', 12),
            bg='#404040',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief=tk.FLAT,
            bd=5
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_field.bind('<Return>', self.send_message)
        self.input_field.focus()
        
        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            font=('Arial', 12, 'bold'),
            bg='#0078d4',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            cursor='hand2'
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg='#2b2b2b')
        status_frame.pack(fill=tk.X)
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=('Arial', 9),
            bg='#2b2b2b',
            fg='#888888'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Memory stats button
        self.memory_button = tk.Button(
            status_frame,
            text="Memory Stats",
            command=self.show_memory_stats,
            font=('Arial', 9),
            bg='#404040',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        self.memory_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Clear chat button
        self.clear_button = tk.Button(
            status_frame,
            text="Clear Chat",
            command=self.clear_chat,
            font=('Arial', 9),
            bg='#404040',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2'
        )
        self.clear_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add welcome message
        self.add_message("Assistant", f"Hello! I'm {config.get('assistant.name', 'Assistant')} running in text mode. How can I help you today?", "assistant")
    
    def setup_styling(self):
        """Setup additional styling and theming"""
        # Configure text tags for different message types
        self.chat_display.tag_configure("user", foreground="#87CEEB", font=('Arial', 10, 'bold'))
        self.chat_display.tag_configure("assistant", foreground="#90EE90", font=('Arial', 10))
        self.chat_display.tag_configure("system", foreground="#FFA500", font=('Arial', 9, 'italic'))
        self.chat_display.tag_configure("timestamp", foreground="#888888", font=('Arial', 8))
    
    def add_message(self, sender, message, msg_type="user"):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add sender and message
        if msg_type == "user":
            self.chat_display.insert(tk.END, f"You: {message}\n", "user")
        elif msg_type == "assistant":
            self.chat_display.insert(tk.END, f"{sender}: {message}\n", "assistant")
        else:
            self.chat_display.insert(tk.END, f"{sender}: {message}\n", "system")
        
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        """Send a message to the assistant"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        # Clear input field
        self.input_field.delete(0, tk.END)
        
        # Add user message to chat
        self.add_message("You", message, "user")
        
        # Update status
        self.status_label.config(text="Processing...")
        self.send_button.config(state=tk.DISABLED)
        
        # Process message in background thread
        threading.Thread(
            target=self.process_message,
            args=(message,),
            daemon=True
        ).start()
    
    def process_message(self, message):
        """Process the user message and generate response"""
        # Create thread-local memory instance to avoid SQLite threading issues
        thread_memory = None
        try:
            self.interaction_count += 1
            
            # Create a new memory instance for this thread
            thread_memory = EnhancedMemory()
            
            # Parse intent
            intent = self.intent_parser.parse_intent(message)
            print(f"[DEBUG] Detected intent: {intent}")
            
            response = None
            context_type = "general"
            
            # Handle different intents
            if intent == "memory_recall" or self.intent_parser.is_memory_related(message):
                context_type = "memory_query"
                # Create a temporary LLM interface with thread-local memory
                thread_llm = LLMInterface(memory=thread_memory)
                response = thread_llm.get_response_with_memory_search(message)
            
            elif intent == "timer":
                context_type = "timer"
                duration = IntentParser.extract_timer_duration(message)
                if duration:
                    response = start_timer(duration)
                else:
                    response = "Sorry, I couldn't understand the timer duration."
            
            elif intent == "get_weather":
                context_type = "weather"
                default_location = config.get('weather.default_location', 'Guildford')
                
                # Extract location using LLM
                location_prompt = f"""Extract the location from this weather request. If no location is mentioned, respond with '{default_location}' as a one word answer.
                
User request: "{message}"

Location:"""
                
                extracted_location = self.llm._call_llm(location_prompt).strip()
                location = extracted_location if extracted_location and extracted_location.lower() != default_location.lower() else default_location
                
                # Extract time
                target_time = self.extract_datetime(message)
                response = get_weather(location, target_time)
            
            elif intent == "time":
                context_type = "time"
                response = get_time()
            
            elif intent == "joke":
                context_type = "joke"
                response = tell_joke()
            
            elif intent == "play_music":
                context_type = "music_play"
                music_query = IntentParser.extract_music_query(message)
                if music_query:
                    response = play_music(music_query)
                else:
                    response = "Sorry, I couldn't understand what music you want to play."
            
            elif intent == "search_web":
                context_type = "web_search"
                query = message.replace("search for", "").replace("look up", "").strip()
                response = search_web_with_context(query, self.llm)
            
            elif intent in ["memory_stats", "show_memory"]:
                context_type = "memory_stats"
                response = get_memory_stats()
            
            elif intent == "save_memory":
                context_type = "save_memory"
                # Extract title and content for saving
                response = "I can help you save information to memory. What would you like me to remember?"
            
            else:
                # General conversation - use LLM with context
                context_type = "conversation"
                # Create a temporary LLM interface with thread-local memory
                thread_llm = LLMInterface(memory=thread_memory)
                response = thread_llm.get_response(message)
            
            # Save interaction to thread-local memory
            thread_memory.save_interaction(message, response, context_type)
            
            # Queue response for GUI update
            self.response_queue.put(("response", response))
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(f"[ERROR] Processing message failed: {e}")
            self.response_queue.put(("response", error_msg))
        finally:
            # Always close the thread-local memory instance
            if thread_memory:
                try:
                    thread_memory.close()
                except Exception as e:
                    print(f"[WARNING] Failed to close thread memory: {e}")
    
    def extract_datetime(self, command):
        """Extract datetime from command"""
        import dateparser
        parsed = dateparser.parse(
            command,
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": datetime.now(),
                "PARSERS": ["relative-time", "absolute-time", "timestamp"],
            }
        )
        return parsed
    
    def check_response_queue(self):
        """Check for responses from background threads and update GUI"""
        try:
            while True:
                msg_type, content = self.response_queue.get_nowait()
                if msg_type == "response":
                    self.add_message("Assistant", content, "assistant")
                    self.status_label.config(text="Ready")
                    self.send_button.config(state=tk.NORMAL)
                    self.input_field.focus()
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_response_queue)
    
    def show_memory_stats(self):
        """Show memory statistics in a popup"""
        try:
            # Create a temporary memory instance for stats (this runs in main thread)
            temp_memory = EnhancedMemory()
            try:
                stats_text = get_memory_stats(temp_memory)
                messagebox.showinfo("Memory Statistics", stats_text)
            finally:
                temp_memory.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get memory stats: {str(e)}")
    
    def clear_chat(self):
        """Clear the chat display"""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.add_message("Assistant", "Chat cleared. How can I help you?", "assistant")
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit the assistant?"):
            try:
                self.memory.close()
            except:
                pass
            self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add some helpful keybindings
        self.root.bind('<Control-l>', lambda e: self.clear_chat())
        self.root.bind('<Control-m>', lambda e: self.show_memory_stats())
        
        print("[INFO] Starting Text Assistant GUI...")
        print("[INFO] Keyboard shortcuts:")
        print("  - Enter: Send message")
        print("  - Ctrl+L: Clear chat")
        print("  - Ctrl+M: Show memory stats")
        
        self.root.mainloop()

def main():
    """Main entry point for the text GUI"""
    try:
        app = TextAssistantGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n[INFO] Text Assistant GUI interrupted by user")
    except Exception as e:
        print(f"[ERROR] Failed to start Text Assistant GUI: {e}")
        messagebox.showerror("Startup Error", f"Failed to start assistant: {str(e)}")

if __name__ == "__main__":
    main()
