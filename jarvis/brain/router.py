"""
Command Router - Parses user input and routes to the correct handler.
Uses rule-based matching for system commands and falls back to the learning AI for general queries.
"""

import re
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger('JARVIS.brain.router')


class Command:
    """Represents a parsed command"""
    def __init__(self, intent: str, parameters: Dict[str, Any] = None, raw: str = ""):
        self.intent = intent
        self.parameters = parameters or {}
        self.raw = raw
        self.timestamp = datetime.now()


class CommandRouter:
    """Routes user input to appropriate handlers based on intent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.handlers: Dict[str, Callable] = {}
        self.patterns: Dict[str, re.Pattern] = {}
        self.learning_ai = None  # Set by server after initialization
        self.local_learning = None  # Set by server after initialization
        self._register_default_patterns()
        logger.info("CommandRouter initialized")
    
    def set_learning_ai(self, learning_ai):
        """Attach the learning AI engine to the router"""
        self.learning_ai = learning_ai
        logger.info("LearningAI attached to CommandRouter")
    
    def set_local_learning(self, local_learning):
        """Attach the local learning AI engine to the router"""
        self.local_learning = local_learning
        logger.info("LocalLearningAI attached to CommandRouter")
    
    def _register_default_patterns(self):
        """Register built-in command patterns"""
        self.patterns = {
            # Greetings
            "greet": re.compile(r'\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b', re.I),
            
            # Time & Date
            "time": re.compile(r'(what\s*is\s*the\s*)?(time|current\s+time)', re.I),
            "date": re.compile(r'(what\s*is\s*the\s*)?(date|today\s*(?:\'?s|)?\s*day|day\s*of\s*the\s*week)', re.I),
            
            # System Control
            "volume_up": re.compile(r'(volume\s*up|increase\s*volume|turn\s*it\s*up|louder)', re.I),
            "volume_down": re.compile(r'(volume\s*down|decrease\s*volume|turn\s*it\s*down|quieter)', re.I),
            "volume_mute": re.compile(r'(mute\s*volume|mute\s*(?:the\s*)?sound|silence)', re.I),
            "volume_set": re.compile(r'volume\s*(?:to\s*)?(\d+)', re.I),
            
            # App Control
            "open_app": re.compile(r'(open|launch|start|run)\s+([\w\s]+)', re.I),
            "close_app": re.compile(r'(close|quit|exit|stop|kill)\s+([\w\s]+)', re.I),
            "list_apps": re.compile(r'(list|show)\s*(?:running\s*)?(apps?|programs?|processes?)', re.I),
            
            # File Operations
            "open_file": re.compile(r'open\s+(?:file\s*)?([\w\s\.]+)', re.I),
            "open_folder": re.compile(r'open\s+(?:folder|directory|dir)\s*([\w\s]+)', re.I),
            "search_files": re.compile(r'(search|find)\s+(?:for\s*)?([\w\s]+)', re.I),
            "list_files": re.compile(r'(list|show)\s*(?:all\s*)?(files?|folders?)\s*(?:in\s*([\w\s]+))?', re.I),
            
            # System Info
            "system_info": re.compile(r'(system\s*info|pc\s*info|computer\s*info|about\s*(?:this\s*)?(?:pc|computer|system)|specs?)', re.I),
            "system_status": re.compile(r'(system\s*status|system\s*health|how\s*is\s*(?:the\s*)?system|system\s*check|overall\s*status)', re.I),
            "battery": re.compile(r'(battery\s*(?:status|level|life)|how\s*much\s*battery)', re.I),
            "disk_space": re.compile(r'(disk\s*space|storage\s*(?:usage|info)|free\s*space)', re.I),
            "cpu_usage": re.compile(r'(cpu\s*(?:usage|use|load|temp)|processor\s*usage)', re.I),
            "memory_usage": re.compile(r'(memory\s*(?:usage|use|info)|ram\s*(?:usage|info|free))', re.I),
            
            # Web & Search
            "web_search": re.compile(r'(search\s*(?:the\s*)?web|google|bing|look\s*up)\s+(.+)', re.I),
            "open_url": re.compile(r'open\s+(?:url\s*)?(https?://\S+)', re.I),
            
            # Reminders & Tasks
            "set_reminder": re.compile(r'(set\s*(?:a\s*)?reminder|remind\s*me\s*(?:to\s*)?|remember\s*(?:to\s*)?)', re.I),
            "list_reminders": re.compile(r'(list|show)\s*(?:my\s*)?(reminders?|tasks?|alerts?)', re.I),
            "delete_reminder": re.compile(r'(delete|remove|clear)\s*(?:reminder|task|alert)', re.I),
            
            # Calculator
            "calculate": re.compile(r'(calculate|compute)\s*([\d\s\+\-\*\/\.\(\)]+)', re.I),
            "math_expression": re.compile(r'what\s+is\s+([\d]+[\s]*[\+\-\*\/][\s]*[\d]+(?:[\s]*[\+\-\*\/][\s]*[\d]+)*)', re.I),
            
            # Weather
            "weather": re.compile(r'(weather|temperature|forecast)\s*(?:in\s*([\w\s]+))?', re.I),
            
            # Jokes & Fun
            "joke": re.compile(r'(joke|tell\s*me\s*(?:a\s*)?(?:joke|funny\s*story)|make\s*me\s*laugh)', re.I),
            "quote": re.compile(r'(quote|inspirational|motivat)', re.I),
            
            # Help
            "help": re.compile(r'(help|what\s*can\s*you\s*do|commands?|features?)', re.I),
            
            # Goodbye
            "goodbye": re.compile(r'\b(bye|goodbye|see\s*you|good\s*night|exit|quit|shutdown)\b', re.I),
            
            # Internet Learning
            "learn_now": re.compile(r'(start\s*)?(learn(?:ing)?\s*(?:now|from\s*internet|from\s*web|new\s*facts?))', re.I),
            "learning_status": re.compile(r'(learn(?:ing)?\s*status|what\s*have\s*you\s*learned|internet\s*learn(?:ing)?)', re.I),
            
            # Power Status
            "power_status": re.compile(r'(power\s*status|battery\s*status|is\s*it\s*on\s*power|plugged\s*in)', re.I),
            
            # Local AI Learning
            "local_status": re.compile(r'(local\s*status|local\s*(?:ai\s*)?learn(?:ing)?\s*status|what\s*have\s*you\s*locally\s*learned|local\s*brain)', re.I),
            "scan_files": re.compile(r'(scan\s*(?:my\s*)?(?:files?|folders?|directories?|local\s*files?))', re.I),
            "who_is": re.compile(r'who\s+(?:is|was)\s+(.+)', re.I),
        }
        logger.info(f"Registered {len(self.patterns)} command patterns")
    
    def register_handler(self, intent: str, handler: Callable):
        """Register a handler function for an intent"""
        self.handlers[intent] = handler
        logger.info(f"Registered handler for intent: {intent}")
    
    def parse(self, text: str) -> Optional[Command]:
        """Parse user input and return a Command object"""
        text = text.strip()
        if not text:
            return None
        
        # Try to match against known patterns
        for intent, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                parameters = self._extract_parameters(intent, match, text)
                logger.info(f"Matched intent: {intent} | Parameters: {parameters}")
                return Command(intent=intent, parameters=parameters, raw=text)
        
        # No match - return as unknown (will be handled by LLM if available)
        return Command(intent="unknown", parameters={}, raw=text)
    
    def _extract_parameters(self, intent: str, match: re.Match, text: str) -> Dict[str, Any]:
        """Extract parameters from regex match"""
        params = {}
        
        if intent == "volume_set":
            params['level'] = int(match.group(1))
        elif intent == "open_app":
            params['app_name'] = match.group(2).strip().lower()
        elif intent == "close_app":
            params['app_name'] = match.group(2).strip().lower()
        elif intent == "open_folder":
            params['folder'] = match.group(1).strip().lower()
        elif intent == "search_files":
            params['query'] = match.group(1).strip()
        elif intent == "web_search":
            params['query'] = match.group(2).strip()
        elif intent == "open_url":
            params['url'] = match.group(1).strip()
        elif intent == "calculate":
            params['expression'] = match.group(2).strip()
        elif intent == "math_expression":
            params['expression'] = match.group(1).strip()
        elif intent == "weather":
            if match.group(2):
                params['location'] = match.group(2).strip()
        elif intent == "who_is":
            params['name'] = match.group(1).strip()
        elif intent == "scan_files":
            # Check for directory parameter
            dir_match = re.search(r'in\s+([\w\s]+)', text, re.I)
            if dir_match:
                params['directory'] = dir_match.group(1).strip()
        
        return params
    
    async def execute(self, command: Command) -> str:
        """Execute a command and return the response"""
        if command.intent in self.handlers:
            handler = self.handlers[command.intent]
            try:
                result = handler(command)
                # Handle async handlers
                if hasattr(result, '__await__'):
                    import asyncio
                    result = await result
                return str(result)
            except Exception as e:
                logger.error(f"Error executing {command.intent}: {e}")
                return f"Sorry, I encountered an error: {str(e)}"
        else:
            return None  # Signal that learning AI should handle this
    
    def handle_teach_command(self, text: str) -> Optional[str]:
        """Handle 'teach' commands: 'teach me X is Y' or 'remember that X means Y'"""
        if self.learning_ai is None:
            return None
        
        # Pattern: "teach me <question> is <answer>"
        teach_match = re.search(r'teach\s+(?:me\s+)?(.+?)\s+(?:is|means|answer\s+is)\s+(.+)', text, re.I)
        if teach_match:
            question = teach_match.group(1).strip()
            answer = teach_match.group(2).strip()
            self.learning_ai.add_fact(question, answer)
            return f"Got it! I've learned that '{question}' is '{answer}'. I'll remember this."
        
        # Pattern: "remember that <statement>" (must have 'that' to avoid conflict with reminder)
        remember_match = re.search(r'remember\s+that\s+(.+)', text, re.I)
        if remember_match:
            statement = remember_match.group(1).strip()
            # Try to split into question/answer
            if ' is ' in statement:
                parts = statement.split(' is ', 1)
                self.learning_ai.add_fact(parts[0].strip(), parts[1].strip())
                return f"Remembered: '{statement}'"
            elif ' means ' in statement:
                parts = statement.split(' means ', 1)
                self.learning_ai.add_fact(parts[0].strip(), parts[1].strip())
                return f"Remembered: '{statement}'"
            else:
                self.learning_ai.learn(
                    patterns=self.learning_ai._generate_variations(statement),
                    response=f"I remember: {statement}",
                    category="fact"
                )
                return f"I'll remember that: '{statement}'"
        
        return None
