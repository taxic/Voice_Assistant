# response_variations.py

import random
from datetime import datetime

class ResponseVariations:
    def __init__(self):
        """Initialize response variations with different categories"""
        
        # Wake word activation responses
        self.wake_responses = [
            # Standard responses
            "Yes? I'm listening.",
            "How can I help you?",
            "I'm here, what do you need?",
            "What can I do for you?",
            "Yes? What's on your mind?",
            
            # Friendly responses
            "Hi there! What's up?",
            "Hey! I'm all ears.",
            "Ready when you are!",
            "At your service!",
            "What's happening?",
            
            # Time-based responses
            "Good morning! How can I assist?",  # Will be filtered by time
            "Good afternoon! What do you need?",
            "Good evening! I'm here to help.",
            "Hope you're having a great day! What's up?",
            
            # Casual responses
            "Yep, I'm here!",
            "What's going on?",
            "I'm ready, what do you need?",
            "Hit me with it!",
            "What can I help you with today?",
            
            # Enthusiastic responses
            "Absolutely! What can I do?",
            "You bet! How can I help?",
            "Right here! What's the plan?",
            "Let's do this! What do you need?",
        ]
        
        # Error/clarification responses
        self.clarification_responses = [
            "I didn't catch that.",
            "Sorry, could you repeat that?",
            "I missed what you said, try again?",
            "Come again?",
            "Didn't quite get that.",
            "Can you say that once more?",
            "I'm not sure I heard you correctly.",
            "Could you try that again?",
            "Sorry, what was that?",
            "One more time, please?"
        ]
        
        # Interruption acknowledgment responses
        self.interrupt_responses = [
            "Okay, I'll stop talking.",
            "Got it, I'll be quiet.",
            "No problem, I'll pause.",
            "Sure thing, stopping now.",
            "Alright, I'll hold off.",
            "Understood, I'll stop.",
            "Of course, pausing now.",
            "Right, I'll quiet down.",
            "Okay, going silent.",
            "Will do, stopping."
        ]
        
        # Acknowledgment responses
        self.acknowledgment_responses = [
            "Got it!",
            "Understood!",
            "Roger that!",
            "Copy that!",
            "Makes sense!",
            "Alright!",
            "Perfect!",
            "I see!",
            "Gotcha!",
            "Right!"
        ]
        
        # Error handling responses
        self.error_responses = [
            "I encountered an error processing your request.",
            "Oops, something went wrong there.",
            "Sorry, I hit a snag with that one.",
            "I ran into an issue there.",
            "That didn't work as expected.",
            "Something's not right there.",
            "I'm having trouble with that.",
            "That's not working for some reason.",
            "There seems to be a problem.",
            "I'm getting an error with that."
        ]
        
        # Success responses
        self.success_responses = [
            "Done!",
            "All set!",
            "There you go!",
            "Perfect!",
            "Completed!",
            "That's taken care of!",
            "Mission accomplished!",
            "Good to go!",
            "All done!",
            "Sorted!"
        ]
        
        # Last used responses to avoid immediate repetition
        self._last_responses = {}
        self._response_history = []
        self._max_history = 10
        
    def get_wake_response(self):
        """Get a varied wake word activation response"""
        current_hour = datetime.now().hour
        
        # Filter time-specific responses
        available_responses = []
        for response in self.wake_responses:
            if "Good morning" in response and 5 <= current_hour < 12:
                available_responses.append(response)
            elif "Good afternoon" in response and 12 <= current_hour < 17:
                available_responses.append(response)
            elif "Good evening" in response and (current_hour >= 17 or current_hour < 5):
                available_responses.append(response)
            elif "Good" not in response:  # Non-time-specific responses
                available_responses.append(response)
        
        return self._get_varied_response("wake", available_responses)
    
    def get_clarification_response(self):
        """Get a varied clarification response"""
        return self._get_varied_response("clarification", self.clarification_responses)
    
    def get_interrupt_response(self):
        """Get a varied interruption acknowledgment response"""
        return self._get_varied_response("interrupt", self.interrupt_responses)
    
    def get_acknowledgment_response(self):
        """Get a varied acknowledgment response"""
        return self._get_varied_response("acknowledgment", self.acknowledgment_responses)
    
    def get_error_response(self):
        """Get a varied error response"""
        return self._get_varied_response("error", self.error_responses)
    
    def get_success_response(self):
        """Get a varied success response"""
        return self._get_varied_response("success", self.success_responses)
    
    def _get_varied_response(self, category, responses):
        """Get a response with variation logic to avoid repetition"""
        # Filter out recently used responses
        available_responses = [r for r in responses if r not in self._response_history[-3:]]
        
        # If we've used all responses recently, reset and use all
        if not available_responses:
            available_responses = responses
        
        # Get last used response for this category
        last_response = self._last_responses.get(category, None)
        
        # If we have more than one option, avoid the last one used
        if len(available_responses) > 1 and last_response in available_responses:
            available_responses.remove(last_response)
        
        # Choose a random response
        response = random.choice(available_responses)
        
        # Update tracking
        self._last_responses[category] = response
        self._response_history.append(response)
        
        # Maintain history size
        if len(self._response_history) > self._max_history:
            self._response_history.pop(0)
        
        return response


# Global instance
response_variations = ResponseVariations()
