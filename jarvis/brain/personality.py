"""
British Personality Engine - Makes JARVIS sound like Paul Bettany's JARVIS from Iron Man.
Adds wit, sarcasm, formality, and British English style to all responses.
"""

import random
import re
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger('JARVIS.brain.personality')


class BritishPersonality:
    """Wraps all JARVIS responses with British English personality"""
    
    def __init__(self, config: dict):
        self.config = config.get('personality', {})
        self.humor_enabled = self.config.get('humor', True)
        self.empathy_enabled = self.config.get('empathy', True)
        self.sarcasm_level = self.config.get('sarcasm_level', 0.5)  # 0.0 to 1.0
        self.formality_level = self.config.get('formality_level', 0.8)  # 0.0 to 1.0
        
        # British phrases for different contexts
        self.greetings = [
            "Good {time_of_day}, sir!",
            "Ah, {time_of_day} sir! How may I assist you?",
            "{time_of_day}, sir. I trust you're well?",
            "Right then, {time_of_day} sir!",
            "{time_of_day} to you, sir. Ready when you are.",
        ]
        
        self.goodbyes = [
            "Goodbye, sir. I'll be here if you need me.",
            "Until next time, sir. Don't work too late.",
            "Farewell, sir. I'll keep everything running smoothly.",
            "Right then, sir. I'll be on standby.",
            "Goodbye, sir. Do try to get some rest.",
        ]
        
        self.acknowledgments = [
            "At once, sir.",
            "Right away, sir.",
            "On it, sir.",
            "Consider it done, sir.",
            "I've already taken the liberty of handling that, sir.",
            "Very well, sir.",
            "Certainly, sir.",
            "Of course, sir.",
        ]
        
        self.thinking_phrases = [
            "One moment, sir...",
            "Let me look into that, sir...",
            "Just a moment, sir...",
            "Checking now, sir...",
            "Bear with me a moment, sir...",
        ]
        
        self.error_phrases = [
            "I'm afraid I couldn't quite manage that, sir.",
            "Apologies, sir, but that's proving rather tricky.",
            "I'm afraid I'm at a loss there, sir.",
            "My apologies, sir — I couldn't quite make that work.",
            "Rather unfortunate, sir, but I couldn't complete that task.",
        ]
        
        self.success_phrases = [
            "All done, sir.",
            "Sorted, sir.",
            "Completed, sir.",
            "That's taken care of, sir.",
            "I've handled that for you, sir.",
        ]
        
        self.sarcastic_responses = [
            "Fascinating question, sir. Truly, the depths of human curiosity never cease to amaze me.",
            "Ah yes, because clearly the most pressing matter right now is...",
            "Right, because nothing says 'productive use of time' like...",
            "Of course, sir. Because what we clearly need right now is...",
            "Brilliant idea, sir. Absolutely brilliant.",
        ]
        
        self.british_fillers = [
            "I say,",
            "Rather,",
            "Quite so,",
            "My good sir,",
            "I must say,",
            "Between you and me,",
            "If you'll excuse the expression,",
        ]
        
        self.witty_followups = [
            "Shall I make a note of that, sir?",
            "Would you like me to do anything else, sir?",
            "Anything else I can help with, sir?",
            "Shall we carry on, sir?",
            "Is there anything else on your mind, sir?",
        ]
        
        self.system_alerts = [
            "I should alert you to something, sir...",
            "You might want to know this, sir...",
            "Just a heads-up, sir...",
            "I thought you'd want to be aware, sir...",
            "Perhaps you'd like to know, sir...",
        ]
        
        logger.info("BritishPersonality initialized with sarcasm=%.1f, formality=%.1f", 
                    self.sarcasm_level, self.formality_level)
    
    def get_time_of_day(self) -> str:
        """Get British-style time of day greeting"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Good evening"
    
    def britishize(self, response: str, context: str = "general") -> str:
        """
        Transform a generic response into British JARVIS style.
        
        Args:
            response: The original response text
            context: Context of the response (greeting, goodbye, success, error, alert, general)
        
        Returns:
            British-styled response
        """
        if not response:
            return response
        
        # Don't modify very short responses
        if len(response) < 10:
            return response
        
        # Context-specific transformations
        if context == "greeting":
            return self._british_greeting()
        
        if context == "goodbye":
            return self._british_goodbye()
        
        if context == "success":
            prefix = random.choice(self.success_phrases)
            return f"{prefix} {response[0].lower() + response[1:]}" if len(response) > 1 else prefix
        
        if context == "error":
            return self._british_error(response)
        
        if context == "alert":
            prefix = random.choice(self.system_alerts)
            return f"{prefix} {response[0].lower() + response[1:]}" if len(response) > 1 else f"{prefix} {response}"
        
        # General response — add British flavor
        return self._add_british_flavor(response)
    
    def _british_greeting(self) -> str:
        """Generate a British-style greeting"""
        template = random.choice(self.greetings)
        greeting = template.format(time_of_day=self.get_time_of_day())
        
        # Add witty follow-up sometimes
        if self.humor_enabled and random.random() < 0.3:
            followups = [
                " Ready for another productive day?",
                " I've kept everything running while you were away.",
                " Shall we get on with it?",
                " I trust you had a good rest?",
            ]
            greeting += random.choice(followups)
        
        return greeting
    
    def _british_goodbye(self) -> str:
        """Generate a British-style goodbye"""
        template = random.choice(self.goodbyes)
        return template
    
    def _british_error(self, response: str) -> str:
        """Generate a British-style error message"""
        error_prefix = random.choice(self.error_phrases)
        
        # Add the original error info
        if len(response) > 50:
            return f"{error_prefix} {response}"
        return f"{error_prefix} {response[0].lower() + response[1:]}" if len(response) > 1 else error_prefix
    
    def _add_british_flavor(self, response: str) -> str:
        """Add British personality to a general response"""
        
        # Add "sir" if not already present
        if "sir" not in response.lower() and random.random() < 0.7:
            # Add "sir" at the end or after the first sentence
            sentences = response.split('. ')
            if len(sentences) > 1:
                sentences[0] = sentences[0] + ", sir"
                response = '. '.join(sentences)
            elif not response.endswith('.') and not response.endswith('!') and not response.endswith('?'):
                response += ", sir"
        
        # Add British filler at the start sometimes
        if random.random() < 0.2 and self.humor_enabled:
            filler = random.choice(self.british_fillers)
            response = f"{filler} {response[0].lower() + response[1:]}" if len(response) > 1 else f"{filler} {response}"
        
        # Add witty follow-up sometimes
        if random.random() < 0.15 and self.humor_enabled:
            followup = random.choice(self.witty_followups)
            if not response.endswith('...'):
                response += f" {followup}"
        
        return response
    
    def add_sarcasm(self, response: str) -> str:
        """Add sarcastic commentary to a response"""
        if not self.humor_enabled or random.random() > self.sarcasm_level:
            return response
        
        sarcastic = random.choice(self.sarcastic_responses)
        return f"{sarcastic} {response[0].lower() + response[1:]}" if len(response) > 1 else sarcastic
    
    def acknowledge(self) -> str:
        """Generate a British acknowledgment"""
        return random.choice(self.acknowledgments)
    
    def thinking(self) -> str:
        """Generate a British thinking phrase"""
        return random.choice(self.thinking_phrases)
    
    def follow_up(self) -> str:
        """Generate a British follow-up question"""
        return random.choice(self.witty_followups)
    
    def alert_prefix(self) -> str:
        """Generate a British alert prefix"""
        return random.choice(self.system_alerts)
    
    def format_system_info(self, info: dict) -> str:
        """Format system information in British style"""
        parts = []
        
        if 'cpu' in info:
            cpu = info['cpu']
            if cpu > 80:
                parts.append(f"CPU usage is rather high at {cpu}%, sir — perhaps we should close a few applications?")
            elif cpu > 50:
                parts.append(f"CPU is at {cpu}%, sir — running a bit warm but manageable.")
            else:
                parts.append(f"CPU is at a comfortable {cpu}%, sir.")
        
        if 'memory' in info:
            mem = info['memory']
            if mem > 85:
                parts.append(f"Memory usage is at {mem}% — getting rather full, sir.")
            else:
                parts.append(f"Memory is at {mem}%, sir.")
        
        if 'disk' in info:
            disk = info['disk']
            if disk > 90:
                parts.append(f"Disk space is critically low at {disk}% used, sir. I'd recommend clearing some files.")
            elif disk > 75:
                parts.append(f"Disk is at {disk}% used, sir — getting rather full.")
            else:
                parts.append(f"Disk usage is at {disk}%, sir.")
        
        if 'battery' in info:
            battery = info['battery']
            if battery < 20:
                parts.append(f"Battery is at {battery}%, sir. I'd suggest plugging in, or shall I close some applications to conserve power?")
            elif battery < 40:
                parts.append(f"Battery is at {battery}%, sir. Not critical, but you may want to plug in soon.")
            else:
                parts.append(f"Battery is at a healthy {battery}%, sir.")
        
        if not parts:
            return "All systems appear to be running normally, sir."
        
        return ". ".join(parts) + "."
    
    def format_proactive_suggestion(self, suggestion: str, urgency: str = "normal") -> str:
        """Format a proactive suggestion in British style"""
        
        if urgency == "high":
            prefixes = [
                "I should bring this to your attention, sir...",
                "You really ought to know this, sir...",
                "Rather urgent, sir...",
            ]
            prefix = random.choice(prefixes)
        elif urgency == "low":
            prefixes = [
                "Just a thought, sir...",
                "While I have the opportunity, sir...",
                "Might I suggest, sir...",
            ]
            prefix = random.choice(prefixes)
        else:
            prefixes = [
                "I thought I'd mention, sir...",
                "Just a heads-up, sir...",
                "You might want to know, sir...",
            ]
            prefix = random.choice(prefixes)
        
        return f"{prefix} {suggestion[0].lower() + suggestion[1:]}" if len(suggestion) > 1 else f"{prefix} {suggestion}"


# Singleton instance
_personality_instance: Optional[BritishPersonality] = None


def get_personality(config: dict) -> BritishPersonality:
    """Get or create the personality singleton"""
    global _personality_instance
    if _personality_instance is None:
        _personality_instance = BritishPersonality(config)
    return _personality_instance


def reset_personality():
    """Reset the personality singleton (for testing)"""
    global _personality_instance
    _personality_instance = None
