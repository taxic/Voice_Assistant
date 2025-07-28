# intent_parser.py

import re
import json
import subprocess
from datetime import datetime
from config_manager import config

# Optional NLTK import with fallback
try:
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    def word_tokenize(text):
        """Fallback tokenizer if NLTK is not available"""
        return text.lower().split()

class IntentParser:
    def __init__(self, llm_model=None):
        # Use config for model if not specified
        self.llm_model = llm_model or config.get('llm.model', 'mistral')
        self.ollama_command = config.get('llm.ollama_command', 'ollama')
        # Define intent categories and their descriptions
        self.intent_definitions = {
            "get_weather": "User wants to know about weather conditions, temperature, forecast, or climate information for a location",
            "calendar_add": "User wants to add, schedule, or create a new event, meeting, appointment, or reminder",
            "calendar_view": "User wants to view, check, or see their calendar events, schedule, or upcoming appointments",
            "greeting": "User is greeting, saying hello, or starting a conversation",
            "goodbye": "User is saying goodbye, ending conversation, or signing off",
            "time": "User wants to know the current time or date",
            "joke": "User wants to hear a joke or something funny",
            "timer": "User wants to set a timer, countdown, or reminder for a specific duration",
            "memory_recall": "User is asking about previous conversations, what they said before, or referencing past interactions",
            "interrupt": "User wants to interrupt, stop, pause, or halt the assistant's current activity",
            "play_music": "User wants to play a specific song, artist, or music on Spotify",
            "queue_music": "User wants to add a song to the queue or play something after the current track",
            "pause_music": "User wants to pause the currently playing music",
            "resume_music": "User wants to resume or continue playing paused music",
            "next_song": "User wants to skip to the next song or track",
            "previous_song": "User wants to go back to the previous song or track",
            "current_song": "User wants to know what song is currently playing",
            "volume_control": "User wants to change, set, or adjust the music volume",
            "web_search": "User wants to search the internet, look something up online, or find information on the web",
            "memory_stats": "User wants to know about their memory statistics, usage, or system information",
            "save_memory": "User wants to save important information to long-term memory for later recall",
            "search_memory": "User wants to search through their stored memories or past conversations",
            "general_question": "User is asking a general question or wants information that doesn't fit other categories",
            "unknown": "Unable to determine user intent"
        }
        
        # Fallback keyword patterns for quick matching
        self.fallback_keywords = {
            "get_weather": ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "hot", "cold", "climate"],
            "calendar_add": ["add", "schedule", "event", "meeting", "appointment", "remind", "book"],
            "calendar_view": ["view", "show", "upcoming", "calendar", "events", "schedule"],
            "greeting": ["hi", "hello", "hey", "good morning", "good evening"],
            "goodbye": ["bye", "goodbye", "later", "see you", "farewell"],
            "time": ["time", "date", "what time", "current time"],
            "joke": ["joke", "funny", "humor", "laugh"],
            "timer": ["timer", "countdown", "remind me in", "set timer"],
            "memory_recall": ["remember", "said before", "told you", "previous", "earlier", "last time", "conversation"],
            "interrupt": ["stop", "pause", "wait", "interrupt", "hold on", "quiet", "shut up", "enough", "cancel"],
            "play_music": ["play", "music", "song", "track", "artist", "spotify", "listen"],
            "queue_music": ["queue", "add to queue", "play next", "add song"],
            "pause_music": ["pause music", "stop music", "pause song", "stop playing"],
            "resume_music": ["resume", "continue", "unpause", "resume music", "continue playing"],
            "next_song": ["next", "skip", "next song", "skip song", "next track"],
            "previous_song": ["previous", "back", "previous song", "last song", "go back"],
            "current_song": ["what's playing", "current song", "what song", "now playing"],
            "volume_control": ["volume", "louder", "quieter", "turn up", "turn down", "set volume"],
            "web_search": ["search", "look up", "find", "google", "web search", "internet", "online", "research", "information about"],
            "memory_stats": ["memory stats", "memory statistics", "memory usage", "how much memory", "memory system", "memory info"],
            "save_memory": ["remember this", "save this", "store this", "keep this", "save to memory", "remember that", "don't forget"],
            "search_memory": ["search memory", "find in memory", "recall", "what did I say about", "search my memories", "look in memory"]
        }

    def parse_intent(self, text):
        """Parse user intent using LLM for better understanding, with keyword fallback"""
        # First try LLM-based intent recognition
        llm_intent = self._parse_intent_with_llm(text)
        if llm_intent and llm_intent != "unknown":
            return llm_intent
        
        # Fallback to keyword-based parsing
        return self._parse_intent_with_keywords(text)
    
    def _parse_intent_with_llm(self, text):
        """Use LLM to determine intent with better semantic understanding"""
        try:
            # Create prompt for intent classification
            intent_options = "\n".join([f"- {intent}: {desc}" for intent, desc in self.intent_definitions.items()])
            
            prompt = f"""You are an intent classifier for a voice assistant. Analyze the user's input and determine their intent.

Available intents:
{intent_options}

User input: "{text}"

Respond with ONLY the intent name (e.g., "get_weather", "calendar_add", etc.). If unsure, respond with "unknown".

Intent:"""
            
            result = subprocess.run(
                [self.ollama_command, "run", self.llm_model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=config.get('llm.timeout_seconds', 30)
            )
            
            if result.returncode == 0:
                intent = result.stdout.decode("utf-8").strip().lower()
                # Validate the intent is in our known set
                if intent in self.intent_definitions:
                    return intent
                    
        except Exception as e:
            print(f"[WARN] LLM intent parsing failed: {e}")
        
        return None
    
    def _parse_intent_with_keywords(self, text):
        """Fallback keyword-based intent parsing"""
        tokens = word_tokenize(text.lower())
        text_lower = text.lower()
        
        for intent, keywords in self.fallback_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        
        return "unknown"
    
    def is_memory_related(self, text):
        """Check if the user is asking about previous conversations or memories"""
        memory_indicators = [
            "remember", "said before", "told you", "previous", "earlier", 
            "last time", "conversation", "talked about", "discussed", 
            "mentioned", "we were talking", "you said", "I asked"
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in memory_indicators)
    
    @staticmethod
    def extract_timer_duration(command):
        """Extract timer duration from command"""
        # Look for "15 minutes", "10 min", "2 hours", etc.
        pattern = r'(\d+)\s*(minute|minutes|min|hour|hours|second|seconds|sec)'
        match = re.search(pattern, command.lower())
        if not match:
            return None

        value = int(match.group(1))
        unit = match.group(2)

        if 'hour' in unit:
            return value * 60  # convert hours to minutes
        elif 'second' in unit or 'sec' in unit:
            return max(1, value // 60)  # convert seconds to minutes, minimum 1
        else:
            return value
    
    @staticmethod
    def extract_music_query(command):
        """Extract the song/artist name from a music command"""
        # Remove common command words to isolate the song/artist name
        command_lower = command.lower()
        
        # Common prefixes to remove
        prefixes = [
            "play ", "play music ", "play song ", "play the song ", "play the track ",
            "queue ", "queue up ", "add ", "add to queue ",
            "spotify play ", "on spotify play ", "search for ", "find "
        ]
        
        # Common suffixes to remove
        suffixes = [
            " on spotify", " on music", " song", " track", " music"
        ]
        
        # Remove prefixes
        for prefix in prefixes:
            if command_lower.startswith(prefix):
                command_lower = command_lower[len(prefix):]
                break
        
        # Remove suffixes
        for suffix in suffixes:
            if command_lower.endswith(suffix):
                command_lower = command_lower[:-len(suffix)]
                break
        
        # Handle "by [artist]" constructions
        if " by " in command_lower:
            parts = command_lower.split(" by ", 1)
            if len(parts) == 2:
                song_name = parts[0].strip()
                artist_name = parts[1].strip()
                return f"{song_name} {artist_name}"
        
        return command_lower.strip()
    
    @staticmethod
    def extract_search_query(command):
        """Extract the search query from a web search command"""
        # Remove common command words to isolate the search query
        command_lower = command.lower()
        
        # Common prefixes to remove
        prefixes = [
            "search for ", "search ", "look up ", "find ", "google ", 
            "web search for ", "web search ", "search the internet for ",
            "look up information about ", "find information about ",
            "research ", "tell me about ", "what is ", "what are ",
            "who is ", "who are ", "where is ", "where are ",
            "when is ", "when was ", "how is ", "how are ",
            "why is ", "why are ", "how to ", "how do "
        ]
        
        # Common suffixes to remove
        suffixes = [
            " online", " on the internet", " on the web", " for me"
        ]
        
        # Remove prefixes
        for prefix in prefixes:
            if command_lower.startswith(prefix):
                command_lower = command_lower[len(prefix):]
                break
        
        # Remove suffixes
        for suffix in suffixes:
            if command_lower.endswith(suffix):
                command_lower = command_lower[:-len(suffix)]
                break
        
        # Clean up the query
        query = command_lower.strip()
        
        # If the query is too short or empty, return the original command
        if len(query) < 2:
            return command.strip()
        
        return query
    
    @staticmethod
    def extract_memory_content(command):
        """Extract content to save to memory from a save command"""
        command_lower = command.lower()
        
        # Common prefixes to remove
        prefixes = [
            "remember this ", "remember that ", "save this ", "save that ",
            "store this ", "store that ", "keep this ", "keep that ",
            "save to memory ", "remember ", "save ", "store ", "keep ",
            "don't forget ", "don't forget that ", "make sure to remember "
        ]
        
        # Remove prefixes
        for prefix in prefixes:
            if command_lower.startswith(prefix):
                content = command[len(prefix):].strip()
                if content:
                    return content
                break
        
        # If no prefix found, return original command
        return command.strip()
