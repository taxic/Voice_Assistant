# intent_parser.py

import re
import json
import subprocess
from datetime import datetime

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
    def __init__(self, llm_model="mistral"):
        self.llm_model = llm_model
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
            "interrupt": ["stop", "pause", "wait", "interrupt", "hold on", "quiet", "shut up", "enough", "cancel"]
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
                ["ollama", "run", self.llm_model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
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
