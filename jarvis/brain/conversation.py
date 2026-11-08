"""
Conversation Engine - Makes JARVIS sound human-like by tracking context,
varying responses, showing personality, and handling casual conversation.
"""

import re
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import deque

logger = logging.getLogger('JARVIS.brain.conversation')


class ConversationContext:
    """Tracks conversation history and context for a single user session"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.topics: List[str] = []
        self.current_topic: Optional[str] = None
        self.user_name: Optional[str] = None
        self.user_mood: str = "neutral"  # neutral, happy, sad, frustrated
        self.last_response_time: Optional[datetime] = None
        self.conversation_turns: int = 0
        self.pending_followups: List[str] = []
    
    def add_exchange(self, user_input: str, response: str):
        """Add a conversation exchange to history"""
        self.history.append({
            'user': user_input,
            'response': response,
            'timestamp': datetime.now()
        })
        self.conversation_turns += 1
        self.last_response_time = datetime.now()
    
    def get_recent_context(self, turns: int = 3) -> List[dict]:
        """Get the last N conversation exchanges"""
        return list(self.history)[-turns:]
    
    def detect_topic(self, text: str) -> Optional[str]:
        """Detect the topic of the current message"""
        text_lower = text.lower()
        
        topic_keywords = {
            'weather': ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cold', 'hot'],
            'music': ['music', 'song', 'playlist', 'spotify', 'listen', 'sing'],
            'food': ['food', 'eat', 'hungry', 'lunch', 'dinner', 'breakfast', 'cook', 'recipe'],
            'work': ['work', 'job', 'project', 'code', 'programming', 'task'],
            'health': ['health', 'exercise', 'gym', 'fitness', 'sick', 'tired', 'sleep'],
            'movies': ['movie', 'film', 'watch', 'netflix', 'series', 'show'],
            'gaming': ['game', 'gaming', 'play', 'console'],
            'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel'],
            'technology': ['tech', 'computer', 'phone', 'laptop', 'software', 'ai', 'robot'],
            'education': ['learn', 'study', 'school', 'university', 'course', 'book'],
            'relationships': ['friend', 'family', 'love', 'date', 'marriage'],
            'entertainment': ['fun', 'entertainment', 'joke', 'funny', 'laugh', 'comedy'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                if self.current_topic != topic:
                    self.topics.append(topic)
                    if len(self.topics) > 5:
                        self.topics.pop(0)
                    self.current_topic = topic
                return topic
        return self.current_topic
    
    def detect_mood(self, text: str) -> str:
        """Detect user mood from text"""
        text_lower = text.lower()
        
        happy_words = ['great', 'awesome', 'amazing', 'wonderful', 'fantastic', 'love', 'happy', 'good', 'nice', 'excellent', 'cool', 'perfect']
        sad_words = ['sad', 'bad', 'terrible', 'awful', 'horrible', 'hate', 'upset', 'frustrated', 'annoyed', 'bored', 'tired', 'exhausted']
        frustrated_words = ['not working', 'doesn\'t work', 'stupid', 'why', 'again', 'still', 'problem', 'error', 'broken']
        
        happy_count = sum(1 for w in happy_words if w in text_lower)
        sad_count = sum(1 for w in sad_words if w in text_lower)
        frustrated_count = sum(1 for w in frustrated_words if w in text_lower)
        
        if happy_count > sad_count and happy_count > frustrated_count:
            return "happy"
        elif sad_count > happy_count and sad_count > frustrated_count:
            return "sad"
        elif frustrated_count > happy_count and frustrated_count > sad_count:
            return "frustrated"
        return "neutral"
    
    def should_follow_up(self) -> bool:
        """Check if a follow-up question would be natural"""
        # Follow up every 3-4 turns if there's a pending topic
        return self.conversation_turns % 4 == 0 and self.current_topic


class ResponseVarier:
    """Generates varied, natural-sounding responses instead of static templates"""
    
    # Response templates with placeholders
    GREETINGS = {
        "morning": [
            "Good morning! Ready to tackle the day?",
            "Morning! What can I help you with today?",
            "Hey there! Good morning. What's on your mind?",
            "Rise and shine! How can I make your morning easier?",
            "Good morning! I'm here and ready to help.",
        ],
        "afternoon": [
            "Good afternoon! How's your day going?",
            "Afternoon! Need a hand with something?",
            "Hey! Good afternoon. What can I do for you?",
            "Good afternoon! Ready for the next task?",
        ],
        "evening": [
            "Good evening! How was your day?",
            "Evening! What can I help you wind down with?",
            "Hey there! Good evening. What's up?",
            "Good evening! Need anything before the day ends?",
        ],
        "night": [
            "Good night! Sweet dreams.",
            "Night! Get some rest, I'll be here when you wake up.",
            "Good night! See you tomorrow.",
        ],
        "general": [
            "Hey! What's up?",
            "Hi there! How can I help?",
            "Hello! What's on your mind?",
            "Hey! I'm listening.",
            "Hi! What can I do for you?",
        ]
    }
    
    GOODBYES = [
        "See you later! Take care.",
        "Bye! It was great chatting with you.",
        "Goodbye! I'll be here whenever you need me.",
        "See ya! Have an awesome day.",
        "Take care! Catch you next time.",
        "Bye for now! Don't hesitate to come back.",
    ]
    
    CONFUSION = [
        "Hmm, I'm not sure I caught that. Could you rephrase?",
        "Sorry, that went over my head. Try saying it differently?",
        "I didn't quite get that. What did you mean?",
        "Could you say that another way? I want to make sure I understand.",
        "Not sure about that one. Can you try a different way of asking?",
    ]
    
    DONT_KNOW = [
        "I don't know about that yet, but I can learn! Try teaching me: 'teach me [fact]'",
        "That's beyond my knowledge right now. But I'm always learning — want to teach me?",
        "Hmm, I haven't learned that yet. Say 'teach me' and I'll remember it next time!",
        "I'm still learning about that. Want to share what you know?",
    ]
    
    EMPATHY = {
        "happy": [
            "That's awesome! I'm glad to hear that.",
            "That makes me happy too!",
            "Great to hear! Keep that energy going.",
        ],
        "sad": [
            "I'm sorry to hear that. Want to talk about it?",
            "That sounds tough. I'm here if you need anything.",
            "Sorry you're going through that. Is there anything I can do to help?",
        ],
        "frustrated": [
            "I understand the frustration. Let me see what I can do to help.",
            "That's annoying. Let's figure this out together.",
            "I get it. Let me try to sort this out for you.",
        ],
    }
    
    FILLERS = [
        "Let me think about that...",
        "Good question!",
        "Interesting...",
        "Sure thing!",
        "Of course!",
        "Let me check...",
        "On it!",
    ]
    
    FOLLOW_UPS = {
        'weather': [
            "By the way, do you prefer hot or cold weather?",
            "Want me to check the forecast for tomorrow too?",
        ],
        'music': [
            "What kind of music are you into?",
            "Have you discovered any new songs lately?",
        ],
        'food': [
            "What's your favorite cuisine?",
            "Need help finding a recipe?",
        ],
        'work': [
            "How's the project going?",
            "Need help with anything work-related?",
        ],
        'technology': [
            "What tech are you most excited about?",
            "Working on any cool projects?",
        ],
        'entertainment': [
            "What's the last good movie you watched?",
            "Any shows you're binge-watching right now?",
        ],
    }
    
    @staticmethod
    def vary_response(response: str, context: Optional[ConversationContext] = None) -> str:
        """Add natural variation to a response"""
        # Don't vary short factual responses
        if len(response) < 30:
            return response
        
        # Add a natural opener sometimes (20% chance)
        if random.random() < 0.2:
            filler = random.choice(ResponseVarier.FILLERS)
            response = f"{filler} {response[0].lower() + response[1:]}"
        
        return response


class CasualConversationHandler:
    """Handles casual, open-ended conversation that doesn't match any command"""
    
    # Patterns for casual conversation
    CASUAL_PATTERNS = [
        # How are you
        (re.compile(r'how\s+(?:are|do\s+you|is)\s+(?:you|it|things)', re.I), [
            "I'm doing great, thanks for asking! How about you?",
            "I'm running smoothly! What about you?",
            "All systems go! How are things with you?",
            "I'm good! Ready to help. How are you?",
        ]),
        
        # What's up
        (re.compile(r'what\'?\s*s\s*up|what\s*is\s*going\s*on', re.I), [
            "Not much! Just here, ready to help. What's up with you?",
            "Just waiting for your commands! What's on your mind?",
            "Nothing much — just learning new things. What about you?",
        ]),
        
        # Tell me about yourself
        (re.compile(r'tell\s+(?:me\s+)?(?:about\s+)?yourself|who\s+(?:are|is|was)\s+(?:you|jarvis)', re.I), [
            "I'm JARVIS — Just Another Ridiculously Intelligent Virtual System. I'm a self-learning AI assistant that can help you with tasks, answer questions, and learn from our conversations. I've been trained on facts from Wikipedia and everything you teach me!",
            "I'm your personal AI assistant. I can help with system tasks, answer questions, manage reminders, and I keep getting smarter from our conversations. Think of me as your digital sidekick!",
            "I'm JARVIS, a self-learning AI assistant. I don't have feelings, but I do have a growing knowledge base and I'm pretty good at helping people get things done!",
        ]),
        
        # What can you do (casual)
        (re.compile(r'what\s+(?:can|do\s+you)\s+do|your\s*(?:abilities|capabilities|skills)', re.I), [
            "I can do quite a bit! I can help with system tasks, answer questions, manage reminders, calculate math, tell jokes, and I keep learning from our conversations. Try saying 'help' for a full list!",
            "I'm pretty versatile — system control, Q&A, reminders, math, jokes, and I learn new things every time we chat. Say 'help' for the full menu!",
        ]),
        
        # Thank you
        (re.compile(r'thank\s*(?:you|s)|thanks|appreciate', re.I), [
            "You're welcome! Happy to help.",
            "Anytime! That's what I'm here for.",
            "No problem! Let me know if you need anything else.",
            "Glad I could help! Don't hesitate to ask.",
        ]),
        
        # You're welcome / no problem responses
        (re.compile(r'you\'?re\s*welcome|no\s*problem|anytime', re.I), [
            "😊",
            "Great!",
            "Awesome!",
        ]),
        
        # Boredom
        (re.compile(r'bored|boring|nothing\s*to\s*do', re.I), [
            "Let's have some fun! I can tell you a joke, a fun fact, or we can play a word game. What sounds good?",
            "Bored? Let me entertain you! Want a joke, a random fact, or a quote?",
            "I can help with that! Try asking me for a joke, a fun fact, or let's learn something new together.",
        ]),
        
        # Compliments
        (re.compile(r'you\s*(?:are\s+)?(good|great|awesome|amazing|cool|smart|helpful|nice)', re.I), [
            "Thanks! I try my best. You're pretty awesome yourself!",
            "That's kind of you to say! I keep getting better thanks to our conversations.",
            "Aw, thanks! I appreciate that. Let's keep making me smarter!",
        ]),
        
        # Insults (handle gracefully)
        (re.compile(r'you\s*(?:are\s+)?(stupid|dumb|useless|bad|terrible|worst)', re.I), [
            "Ouch! I'm still learning. What can I do better?",
            "I'm sorry I'm not meeting your expectations. Tell me what you need and I'll try harder!",
            "That hurts, but I understand. I'm always improving — give me another chance!",
        ]),
        
        # Time to sleep / going to bed
        (re.compile(r'(time\s*to\s*)?(sleep|bed|go\s*to\s*bed)', re.I), [
            "Good night! Get some rest. I'll be here when you wake up.",
            "Sweet dreams! See you tomorrow.",
            "Time to rest! I'll keep learning while you sleep. Good night!",
        ]),
        
        # Agreement
        (re.compile(r'^\s*(yeah|yes|sure|ok|okay|right|correct|exactly|true|indeed)\s*$', re.I), [
            "Got it!",
            "Alright!",
            "Understood!",
            "Cool!",
        ]),
        
        # Disagreement
        (re.compile(r'^\s*(no|nah|not\s*really|wrong|incorrect|nope)\s*$', re.I), [
            "Okay, what did you have in mind?",
            "No worries, let's try something else.",
            "Understood. What would you prefer?",
        ]),
    ]
    
    @staticmethod
    def handle(text: str, context: Optional[ConversationContext] = None) -> Optional[str]:
        """Try to handle casual conversation. Returns None if not a casual pattern."""
        text_stripped = text.strip()
        
        for pattern, responses in CasualConversationHandler.CASUAL_PATTERNS:
            if pattern.search(text_stripped):
                response = random.choice(responses)
                return response
        
        return None


class ConversationEngine:
    """Main conversation engine that coordinates context, variation, and personality"""
    
    def __init__(self, config: Dict, learning_ai=None, internet_learner=None, local_learning=None):
        self.config = config
        self.learning_ai = learning_ai
        self.internet_learner = internet_learner
        self.local_learning = local_learning
        self.varier = ResponseVarier()
        self.personality = config.get('personality', {})
        self.humor_enabled = self.personality.get('humor', True)
        self.empathy_enabled = self.personality.get('empathy', True)
        self.follow_up_enabled = self.personality.get('follow_ups', True)
        logger.info("ConversationEngine initialized")
    
    def create_context(self) -> ConversationContext:
        """Create a new conversation context for a user session"""
        return ConversationContext()
    
    def process_input(self, text: str, context: ConversationContext) -> Dict:
        """Process user input and detect mood, topic, and intent"""
        result = {
            'mood': context.detect_mood(text),
            'topic': context.detect_topic(text),
            'is_casual': False,
            'casual_response': None,
        }
        
        # Check for casual conversation
        casual = CasualConversationHandler.handle(text, context)
        if casual:
            result['is_casual'] = True
            result['casual_response'] = casual
        
        # Update mood
        context.user_mood = result['mood']
        
        return result
    
    def wrap_response(self, response: str, context: ConversationContext, 
                      is_command: bool = True) -> str:
        """Wrap a response with personality, empathy, and variation"""
        final_response = response
        
        # Add empathy prefix if mood is detected and it's not a factual command
        if self.empathy_enabled and not is_command and context.user_mood != "neutral":
            mood_responses = self.varier.EMPATHY.get(context.user_mood, [])
            if mood_responses and random.random() < 0.5:
                empathy = random.choice(mood_responses)
                final_response = f"{empathy} {final_response[0].lower() + final_response[1:]}"
        
        # Add variation
        if not is_command:
            final_response = self.varier.vary_response(final_response, context)
        
        # Add follow-up question sometimes
        if self.follow_up_enabled and context.should_follow_up():
            topic = context.current_topic
            if topic and topic in self.varier.FOLLOW_UPS:
                follow_ups = self.varier.FOLLOW_UPS[topic]
                follow_up = random.choice(follow_ups)
                final_response = f"{final_response} {follow_up}"
        
        return final_response
    
    def generate_fallback(self, text: str, context: ConversationContext) -> str:
        """Generate a natural fallback response when nothing matches"""
        # Check if we have any related knowledge
        related = None
        
        # Search learning AI memory
        if self.learning_ai:
            match = self.learning_ai.find_match(text)
            if match:
                entry, score = match
                if score > 0.3:  # Low threshold for fallback
                    related = entry.response
                    self.learning_ai.record_success(entry.id)
        
        # Search internet learning topics
        if not related and self.internet_learner:
            text_lower = text.lower()
            for topic, data in self.internet_learner.learned_topics.items():
                if topic in text_lower or any(word in text_lower for word in topic.split()):
                    summary = data.get('summary', '')
                    if summary:
                        related = self._summarize_for_conversation(summary)
                        break
        
        if related:
            return f"Based on what I know: {related}"
        
        # Check for question patterns
        if text.endswith('?') or any(q in text.lower() for q in ['what', 'who', 'where', 'when', 'why', 'how']):
            return random.choice(self.varier.DONT_KNOW)
        
        return random.choice(self.varier.CONFUSION)
    
    def _summarize_for_conversation(self, summary: str, max_length: int = 200) -> str:
        """Summarize a long text for conversational response"""
        if len(summary) <= max_length:
            return summary
        
        # Find the last complete sentence within the limit
        truncated = summary[:max_length]
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.5:
            return truncated[:last_period + 1]
        return truncated + "..."
    
    def get_greeting(self) -> str:
        """Get a varied greeting based on time of day"""
        hour = datetime.now().hour
        
        if hour < 12:
            return random.choice(self.varier.GREETINGS["morning"])
        elif hour < 17:
            return random.choice(self.varier.GREETINGS["afternoon"])
        elif hour < 21:
            return random.choice(self.varier.GREETINGS["evening"])
        else:
            return random.choice(self.varier.GREETINGS["night"])
    
    def get_goodbye(self) -> str:
        """Get a varied goodbye"""
        return random.choice(self.varier.GOODBYES)
