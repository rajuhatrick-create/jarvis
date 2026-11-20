"""
Deep Memory System - Cross-session memory for user preferences, habits, and conversation history.
Like movie JARVIS, remembers everything about the user across sessions.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger('JARVIS.brain.deep_memory')


class UserProfile:
    """Stores user profile information"""
    
    def __init__(self):
        self.name = ""
        self.preferred_greeting = ""
        self.work_hours_start = 9
        self.work_hours_end = 18
        self.timezone = ""
        self.language = "en"
        self.preferences: Dict[str, str] = {}
        self.habits: Dict[str, str] = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "preferred_greeting": self.preferred_greeting,
            "work_hours_start": self.work_hours_start,
            "work_hours_end": self.work_hours_end,
            "timezone": self.timezone,
            "language": self.language,
            "preferences": self.preferences,
            "habits": self.habits,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        profile = cls()
        profile.name = data.get("name", "")
        profile.preferred_greeting = data.get("preferred_greeting", "")
        profile.work_hours_start = data.get("work_hours_start", 9)
        profile.work_hours_end = data.get("work_hours_end", 18)
        profile.timezone = data.get("timezone", "")
        profile.language = data.get("language", "en")
        profile.preferences = data.get("preferences", {})
        profile.habits = data.get("habits", {})
        profile.created_at = data.get("created_at", datetime.now().isoformat())
        profile.updated_at = data.get("updated_at", datetime.now().isoformat())
        return profile


class ConversationMemory:
    """Stores conversation history with context"""
    
    def __init__(self, user_input: str, response: str, context: str = "", 
                 topics: List[str] = None, timestamp: datetime = None):
        self.user_input = user_input
        self.response = response
        self.context = context
        self.topics = topics or []
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "user_input": self.user_input,
            "response": self.response,
            "context": self.context,
            "topics": self.topics,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMemory':
        memory = cls(
            user_input=data.get("user_input", ""),
            response=data.get("response", ""),
            context=data.get("context", ""),
            topics=data.get("topics", []),
        )
        memory.timestamp = datetime.fromisoformat(data["timestamp"])
        return memory


class DeepMemory:
    """Cross-session memory system for user preferences, habits, and conversation history"""
    
    def __init__(self, config: dict, sqlite_db=None):
        self.config = config.get('deep_memory', {})
        self.enabled = self.config.get('enabled', True)
        self.max_conversation_history = self.config.get('max_conversation_history', 100)
        self.max_preferences = self.config.get('max_preferences', 50)
        self.max_habits = self.config.get('max_habits', 30)
        self.sqlite_db = sqlite_db
        
        # In-memory storage
        self.user_profile = UserProfile()
        self.conversation_history: List[ConversationMemory] = []
        self.topic_frequency = defaultdict(int)  # topic -> count
        self.frequently_asked = defaultdict(int)  # question -> count
        
        # Load from database if available
        if self.sqlite_db:
            self._load_from_database()
        
        logger.info("DeepMemory initialized with %d conversation memories", len(self.conversation_history))
    
    def _load_from_database(self):
        """Load memory from SQLite database"""
        if not self.sqlite_db:
            return
        
        try:
            # Load user profile
            profile_data = self.sqlite_db.get_meta("user_profile")
            if profile_data:
                self.user_profile = UserProfile.from_dict(json.loads(profile_data))
            
            # Load conversation history
            conversations = self.sqlite_db.get_meta("conversation_history")
            if conversations:
                conv_list = json.loads(conversations)
                self.conversation_history = [ConversationMemory.from_dict(c) for c in conv_list]
            
            # Load topic frequency
            topics = self.sqlite_db.get_meta("topic_frequency")
            if topics:
                self.topic_frequency = defaultdict(int, json.loads(topics))
            
            # Load frequently asked
            freq_asked = self.sqlite_db.get_meta("frequently_asked")
            if freq_asked:
                self.frequently_asked = defaultdict(int, json.loads(freq_asked))
            
            logger.info("DeepMemory loaded from database: profile=%s, conversations=%d", 
                       bool(profile_data), len(self.conversation_history))
        except Exception as e:
            logger.error("Error loading DeepMemory from database: %s", e)
    
    def _save_to_database(self):
        """Save memory to SQLite database"""
        if not self.sqlite_db:
            return
        
        try:
            # Save user profile
            self.sqlite_db.set_meta("user_profile", json.dumps(self.user_profile.to_dict()))
            
            # Save conversation history (last N)
            recent = self.conversation_history[-self.max_conversation_history:]
            self.sqlite_db.set_meta("conversation_history", 
                                   json.dumps([c.to_dict() for c in recent]))
            
            # Save topic frequency
            self.sqlite_db.set_meta("topic_frequency", json.dumps(dict(self.topic_frequency)))
            
            # Save frequently asked
            self.sqlite_db.set_meta("frequently_asked", json.dumps(dict(self.frequently_asked)))
            
        except Exception as e:
            logger.error("Error saving DeepMemory to database: %s", e)
    
    def remember_preference(self, key: str, value: str):
        """Remember a user preference"""
        self.user_profile.preferences[key] = value
        self.user_profile.updated_at = datetime.now().isoformat()
        self._save_to_database()
        logger.info("Remembered preference: %s = %s", key, value)
    
    def remember_habit(self, habit: str, value: str):
        """Remember a user habit"""
        self.user_profile.habits[habit] = value
        self.user_profile.updated_at = datetime.now().isoformat()
        self._save_to_database()
        logger.info("Remembered habit: %s = %s", habit, value)
    
    def set_user_name(self, name: str):
        """Set the user's name"""
        self.user_profile.name = name
        self.user_profile.updated_at = datetime.now().isoformat()
        self._save_to_database()
        logger.info("Set user name: %s", name)
    
    def record_conversation(self, user_input: str, response: str, context: str = "", 
                           topics: List[str] = None):
        """Record a conversation exchange"""
        memory = ConversationMemory(user_input, response, context, topics)
        self.conversation_history.append(memory)
        
        # Update topic frequency
        if topics:
            for topic in topics:
                self.topic_frequency[topic] += 1
        
        # Track frequently asked questions
        if user_input.strip().endswith('?'):
            self.frequently_asked[user_input.strip()] += 1
        
        # Trim history
        if len(self.conversation_history) > self.max_conversation_history:
            self.conversation_history = self.conversation_history[-self.max_conversation_history:]
        
        self._save_to_database()
    
    def recall_context(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Recall relevant past conversations based on query.
        Returns most relevant past conversations.
        """
        if not self.conversation_history:
            return []
        
        query_words = set(query.lower().split())
        scored = []
        
        for memory in self.conversation_history:
            input_words = set(memory.user_input.lower().split())
            topic_words = set(word for topic in memory.topics for word in topic.lower().split())
            all_words = input_words | topic_words
            
            # Calculate similarity
            overlap = len(query_words & all_words)
            if overlap > 0:
                score = overlap / len(query_words)
                scored.append((score, memory))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        return [memory.to_dict() for _, memory in scored[:limit]]
    
    def get_user_profile(self) -> Dict:
        """Get the current user profile"""
        return self.user_profile.to_dict()
    
    def get_preference(self, key: str, default: str = "") -> str:
        """Get a specific preference"""
        return self.user_profile.preferences.get(key, default)
    
    def get_habit(self, key: str, default: str = "") -> str:
        """Get a specific habit"""
        return self.user_profile.habits.get(key, default)
    
    def get_frequently_asked(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently asked questions"""
        sorted_questions = sorted(self.frequently_asked.items(), 
                                 key=lambda x: x[1], reverse=True)
        return sorted_questions[:top_n]
    
    def get_popular_topics(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most popular conversation topics"""
        sorted_topics = sorted(self.topic_frequency.items(), 
                             key=lambda x: x[1], reverse=True)
        return sorted_topics[:top_n]
    
    def get_conversation_summary(self) -> Dict:
        """Get a summary of conversation history"""
        if not self.conversation_history:
            return {
                "total_conversations": 0,
                "popular_topics": [],
                "frequently_asked": [],
            }
        
        # Get time range
        oldest = self.conversation_history[0].timestamp
        newest = self.conversation_history[-1].timestamp
        
        return {
            "total_conversations": len(self.conversation_history),
            "time_range": {
                "oldest": oldest.isoformat(),
                "newest": newest.isoformat(),
            },
            "popular_topics": self.get_popular_topics(),
            "frequently_asked": self.get_frequently_asked(),
        }
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        recent = self.conversation_history[-limit:]
        return [conv.to_dict() for conv in reversed(recent)]
    
    def what_did_we_discuss(self, time_frame: str = "recently") -> str:
        """Generate a natural language summary of past conversations"""
        if not self.conversation_history:
            return "We haven't had any conversations yet, sir."
        
        # Filter by time frame
        now = datetime.now()
        filtered = self.conversation_history
        
        if time_frame == "yesterday":
            yesterday = now - timedelta(days=1)
            filtered = [c for c in self.conversation_history 
                       if yesterday <= c.timestamp < now.replace(hour=0, minute=0, second=0)]
        elif time_frame == "this week":
            week_ago = now - timedelta(weeks=1)
            filtered = [c for c in self.conversation_history if c.timestamp > week_ago]
        
        if not filtered:
            return f"I don't recall any conversations from {time_frame}, sir."
        
        # Extract topics
        topics = defaultdict(int)
        for conv in filtered:
            for topic in conv.topics:
                topics[topic] += 1
        
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_topics:
            topic_list = ", ".join([topic for topic, _ in top_topics])
            return (f"We discussed {topic_list} and a few other things. "
                   f"Would you like me to go into more detail on any of these, sir?")
        
        return f"We had {len(filtered)} conversations {time_frame}. Anything specific you'd like to recall, sir?"
    
    def extract_preference_from_input(self, user_input: str) -> Optional[Tuple[str, str]]:
        """
        Extract preferences from user input.
        Returns (key, value) if a preference is detected.
        """
        input_lower = user_input.lower()
        
        # Pattern: "I prefer X"
        if "i prefer" in input_lower:
            parts = input_lower.split("i prefer", 1)
            if len(parts) > 1:
                value = parts[1].strip().rstrip('.')
                key = f"preference_{value.replace(' ', '_')}"
                return (key, value)
        
        # Pattern: "I like X"
        if "i like" in input_lower:
            parts = input_lower.split("i like", 1)
            if len(parts) > 1:
                value = parts[1].strip().rstrip('.')
                key = f"likes_{value.replace(' ', '_')}"
                return (key, value)
        
        # Pattern: "My name is X"
        if "my name is" in input_lower:
            parts = input_lower.split("my name is", 1)
            if len(parts) > 1:
                name = parts[1].strip().rstrip('.')
                return ("name", name)
        
        # Pattern: "Call me X"
        if "call me" in input_lower:
            parts = input_lower.split("call me", 1)
            if len(parts) > 1:
                name = parts[1].strip().rstrip('.')
                return ("name", name)
        
        # Pattern: "I work from X to Y"
        if "i work from" in input_lower:
            import re
            match = re.search(r'i work from\s+(\d+)(?:\s*to\s*(\d+))?', input_lower)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else 18
                self.user_profile.work_hours_start = start
                self.user_profile.work_hours_end = end
                return ("work_hours", f"{start}:00 to {end}:00")
        
        return None
    
    def extract_topics_from_input(self, user_input: str) -> List[str]:
        """Extract topics from user input"""
        topics = []
        input_lower = user_input.lower()
        
        # Common topic keywords
        topic_keywords = {
            "coding": ["code", "programming", "python", "javascript", "software"],
            "music": ["music", "song", "album", "band", "playlist"],
            "movies": ["movie", "film", "cinema", "watch"],
            "food": ["food", "eat", "cook", "recipe", "restaurant"],
            "work": ["work", "job", "project", "task", "deadline"],
            "health": ["health", "exercise", "gym", "fitness", "diet"],
            "travel": ["travel", "trip", "vacation", "flight", "hotel"],
            "gaming": ["game", "gaming", "play"],
            "reading": ["read", "book", "novel", "article"],
            "learning": ["learn", "study", "course", "tutorial"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_status(self) -> Dict:
        """Get current deep memory status"""
        return {
            "enabled": self.enabled,
            "user_profile": self.get_user_profile(),
            "conversation_count": len(self.conversation_history),
            "topic_count": len(self.topic_frequency),
            "preference_count": len(self.user_profile.preferences),
            "habit_count": len(self.user_profile.habits),
            "popular_topics": self.get_popular_topics(5),
            "frequently_asked": self.get_frequently_asked(5),
        }
