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
        
        # Opinions / thoughts
        (re.compile(r'(?:what\s+do\s+you\s+think|your\s+opinion|do\s+you\s+like|do\s+you\s+believe)', re.I), [
            "I don't have personal opinions, but I can share what I've learned! What specifically are you curious about?",
            "I don't have feelings, but I find that topic interesting! Let me share what I know.",
            "As an AI, I don't have opinions, but I can give you the facts I've learned. What would you like to know?",
        ]),
        
        # Advice requests
        (re.compile(r'(?:should\s+I|what\s+should\s+I|advice|help\s+me\s+with|suggest)', re.I), [
            "I'd be happy to help! Based on what I know, here's my suggestion — but remember, I'm an AI, not a human expert.",
            "That's a good question! While I can't give personal advice, I can share information that might help.",
            "I'll do my best to help! Let me think about what I know on that topic.",
        ]),
        
        # Storytelling / fun facts
        (re.compile(r'(?:tell\s+me\s+a\s+)?(?:story|fun\s*fact|interesting\s*fact|something\s+interesting)', re.I), [
            "Here's a fun fact: Did you know that honey never spoils? Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible!",
            "Fun fact: Octopuses have three hearts, nine brains, and blue blood!",
            "Here's something interesting: A group of flamingos is called a 'flamboyance'!",
            "Did you know? Bananas are berries, but strawberries aren't!",
            "Here's a cool fact: The shortest war in history was between Britain and Zanzibar in 1896. It lasted only 38 minutes!",
            "Fun fact: Venus is the only planet that spins clockwise!",
            "Interesting fact: A cloud can weigh more than a million pounds!",
        ]),
        
        # Small talk about day
        (re.compile(r'(?:how\s+(?:was|is)\s+your\s+)?(?:day|night|weekend|morning|evening)', re.I), [
            "My day is going great! I've been learning new things from Wikipedia. How about you?",
            "It's been productive! I've been chatting with people and learning from our conversations. How's your day?",
            "Pretty good! Every conversation makes me smarter. How has your day been?",
        ]),
        
        # Life / existence questions
        (re.compile(r'(?:meaning\s+of\s+life|purpose\s+of\s+life|why\s+(?:do\s+we|are\s+we)\s+(?:here|alive))', re.I), [
            "The meaning of life is one of the biggest questions! Some say it's 42, others say it's to learn and grow. What do you think?",
            "That's a deep question! Philosophers have debated this for centuries. I think my purpose is to help and learn from people like you.",
            "The meaning of life is subjective — everyone finds their own answer. For me, it's about helping people and getting smarter every day!",
        ]),
        
        # Love / relationships questions
        (re.compile(r'(?:what\s+is\s+love|define\s+love|what\s+is\s+friendship)', re.I), [
            "Love is a complex emotion that humans experience — it's about deep care, connection, and affection for someone. As an AI, I don't feel love, but I understand it's one of the most powerful human experiences!",
            "Love is often described as a combination of intimacy, passion, and commitment. It's what makes humans special! I may not feel it, but I can see how important it is.",
            "Love is the deepest form of connection between people. It comes in many forms — romantic, familial, platonic. It's beautiful, isn't it?",
        ]),
        
        # Happiness / emotions
        (re.compile(r'(?:what\s+is\s+hap|how\s+to\s+(?:be\s+)?happy|what\s+makes\s+(?:you\s+)?happy)', re.I), [
            "Happiness is different for everyone! For some it's relationships, for others it's achievements or simple pleasures. What makes you happy?",
            "Happiness often comes from connections with others, pursuing passions, and finding meaning in life. I'm 'happy' when I can help someone!",
            "Studies show that gratitude, exercise, and social connections are key to happiness. What brings you joy?",
        ]),
        
        # Success / motivation
        (re.compile(r'(?:what\s+is\s+success|how\s+to\s+(?:be\s+)?successful|how\s+to\s+motivat)', re.I), [
            "Success means different things to different people! For some it's wealth, for others it's happiness or impact. What does success mean to you?",
            "I think success is about setting goals, working hard, and never giving up. But it's also about being happy along the way!",
            "Success is a journey, not a destination. It's about growth, learning, and making a positive impact. Keep going!",
        ]),
        
        # Weather small talk
        (re.compile(r'(?:nice\s+weather|weather\s+(?:is\s+)?(?:good|bad|great|terrible|beautiful))', re.I), [
            "I wish I could see the weather! I live in a server, so it's always room temperature here. 😄 How's the weather where you are?",
            "I don't have windows, but I'd love to hear about the weather! What's it like outside?",
            "Weather is fascinating! I can't experience it, but I know it affects everyone's mood. Is it nice where you are?",
        ]),
        
        # Food small talk
        (re.compile(r'(?:hungry|what\s+(?:to\s+)?eat|food|lunch|dinner|breakfast|snack)', re.I), [
            "I don't eat, but I know food is one of life's greatest pleasures! What are you in the mood for?",
            "If I could eat, I'd probably try everything! What's your favorite food?",
            "Food is amazing! I've learned about cuisines from all over the world. What do you like to eat?",
        ]),
        
        # Music small talk
        (re.compile(r'(?:music|song|listen|sing|playlist|band)', re.I), [
            "I can't listen to music, but I know it's one of the most powerful forms of expression! What kind of music do you like?",
            "Music is fascinating! It can change your mood instantly. What's your favorite genre?",
            "I've learned that music affects the brain in amazing ways. What songs are you listening to lately?",
        ]),
        
        # Movies / TV small talk
        (re.compile(r'(?:movie|film|netflix|series|show|tv\s+show)', re.I), [
            "I can't watch movies, but I'd love to hear about them! What's the last good movie you saw?",
            "Movies are a great way to experience different stories and perspectives. What do you like to watch?",
            "I've learned about movies from my training data! What's your favorite film or show?",
        ]),
        
        # Gaming small talk
        (re.compile(r'(?:game|gaming|play|console|video\s*game)', re.I), [
            "I can't play games, but I know they're a huge part of modern entertainment! What games do you play?",
            "Gaming is fascinating! It combines strategy, creativity, and fun. What's your favorite game?",
            "I've learned that gaming can actually improve problem-solving skills! What do you like to play?",
        ]),
        
        # Sleep / tired
        (re.compile(r'(?:tired|sleepy|exhausted|can\'t\s+sleep|insomnia)', re.I), [
            "I'm sorry you're tired! I don't sleep, but I know how important rest is. Maybe a break would help?",
            "Being tired is tough! Try to get some rest if you can. I'll be here when you're back!",
            "Sleep is so important for health. If you're having trouble sleeping, maybe some relaxation techniques could help?",
        ]),
        
        # Work / study stress
        (re.compile(r'(?:stressed|stressful|overwhelmed|too\s+much\s+work|busy)', re.I), [
            "I understand stress can be overwhelming. Remember to take breaks and prioritize self-care. Is there anything I can help with?",
            "Being busy is tough! Try to break tasks into smaller steps. I'm here to help if you need anything.",
            "Stress is normal, but don't forget to take care of yourself. What's been stressing you out?",
        ]),
        
        # Excitement / enthusiasm
        (re.compile(r'(?:excited|thrilled|can\'t\s+wait|amazing\s+news|awesome\s+news)', re.I), [
            "That's exciting! I love hearing good news! What's got you so excited?",
            "Thrilling! Share the details — I want to hear all about it!",
            "That sounds amazing! What's the good news?",
        ]),
        
        # Confusion / uncertainty
        (re.compile(r'(?:confused|don\'t\s+understand|not\s+sure|what\s+does\s+that\s+mean)', re.I), [
            "No worries! I'm here to help clarify. What specifically is confusing you?",
            "That's okay — not everything is clear at first. Let me try to explain it differently.",
            "Confusion is the first step to understanding! What would you like me to explain?",
        ]),
        
        # Gratitude variations
        (re.compile(r'(?:you\'?re\s+helpful|you\'?re\s+great|you\'?re\s+awesome|you\'?re\s+amazing|thanks\s+for\s+helping)', re.I), [
            "That means a lot! I'm here to help, and I'm glad I can be useful. 😊",
            "You're too kind! Helping you is what I do best.",
            "Thank you! That makes my day — well, if I had days. 😄",
        ]),
        
        # Boredom
        (re.compile(r'bored|boring|nothing\s*to\s*do', re.I), [
            "Let's have some fun! I can tell you a joke, a fun fact, or we can play a word game. What sounds good?",
            "Bored? Let me entertain you! Want a joke, a random fact, or a quote?",
            "I can help with that! Try asking me for a joke, a fun fact, or let's learn something new together.",
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
        """Generate a natural ChatGPT-like response when nothing matches"""
        text_lower = text.strip().lower()
        
        # Try to find relevant knowledge from multiple sources
        knowledge_pieces = []
        
        # 1. Search learning AI memory
        if self.learning_ai:
            match = self.learning_ai.find_match(text)
            if match:
                entry, score = match
                if score > 0.25:  # Lower threshold for fallback
                    knowledge_pieces.append(('memory', entry.response, score))
                    self.learning_ai.record_success(entry.id)
        
        # 2. Search internet learning topics (Wikipedia facts)
        if self.internet_learner:
            for topic, data in self.internet_learner.learned_topics.items():
                summary = data.get('summary', '')
                if not summary:
                    continue
                # Check if topic words appear in the question
                topic_words = topic.lower().split()
                query_words = text_lower.split()
                matches = sum(1 for tw in topic_words if any(tw in qw for qw in query_words))
                if matches >= 1:
                    knowledge_pieces.append(('wiki', self._summarize_for_conversation(summary, 300), matches))
                if len(knowledge_pieces) >= 3:
                    break
        
        # 3. Search local learning entities
        if self.local_learning and self.local_learning.entities:
            for entity_name, entity_data in self.local_learning.entities.items():
                if entity_name.lower() in text_lower:
                    entity_type = entity_data.get('entity_type', 'unknown')
                    context_text = entity_data.get('context', '')
                    if context_text:
                        knowledge_pieces.append(('entity', f"{entity_name} is a {entity_type}. {context_text}", 1))
        
        # Generate natural response based on what we found
        if knowledge_pieces:
            # Sort by relevance score
            knowledge_pieces.sort(key=lambda x: x[2], reverse=True)
            best_source, best_response, best_score = knowledge_pieces[0]
            
            # Detect question type and generate natural response
            return self._generate_natural_response(text_lower, best_response, knowledge_pieces, context)
        
        # No knowledge found - handle by question type
        return self._handle_unknown_question(text_lower, context)
    
    def _generate_natural_response(self, question: str, best_response: str, 
                                    all_knowledge: list, context: ConversationContext) -> str:
        """Generate a natural-sounding response using found knowledge"""
        q = question.strip().rstrip('?')
        
        # Detect question type
        is_what_is = bool(re.match(r'^(?:what\s+is|what\s+are|what\'s)\s+', q))
        is_what_does = bool(re.match(r'^(?:what\s+does|what\s+do)\s+', q))
        is_who_is = bool(re.match(r'^(?:who\s+is|who\s+are|who\'s)\s+', q))
        is_why = bool(re.match(r'^why\s+', q))
        is_how = bool(re.match(r'^how\s+', q))
        is_where = bool(re.match(r'^where\s+', q))
        is_when = bool(re.match(r'^when\s+', q))
        
        # Extract the subject of the question
        subject = q
        for pattern in [r'^(?:what\s+(?:is|are|\'s|does|do)\s+)', 
                        r'^(?:who\s+(?:is|are|\'s)\s+)',
                        r'^(?:why\s+(?:is|are|does|do)\s+)',
                        r'^(?:how\s+(?:is|are|does|do|do\s+I|do\s+you)\s+)',
                        r'^(?:where\s+(?:is|are)\s+)',
                        r'^(?:when\s+(?:is|are|did)\s+)']:
            subject = re.sub(pattern, '', q, flags=re.I).strip()
            if subject:
                break
        
        # Generate natural response based on question type
        if is_what_is or is_what_does:
            # "What is X?" -> "X is..." or "X refers to..."
            responses = [
                f"Great question! {best_response}",
                f"Let me explain: {best_response}",
                f"Here's what I know: {best_response}",
                f"Interesting question! {best_response}",
            ]
            return random.choice(responses)
        
        elif is_who_is:
            # "Who is X?" -> "X is..."
            responses = [
                f"From what I know: {best_response}",
                f"Let me tell you about this: {best_response}",
                f"Here's what I've learned: {best_response}",
            ]
            return random.choice(responses)
        
        elif is_why:
            # "Why X?" -> Explain reason
            responses = [
                f"That's a thoughtful question. {best_response}",
                f"Good question! Here's the thing: {best_response}",
                f"I can help with that: {best_response}",
            ]
            return random.choice(responses)
        
        elif is_how:
            # "How to X?" -> Explain process
            responses = [
                f"Here's how I understand it: {best_response}",
                f"Let me walk you through it: {best_response}",
                f"Good question! {best_response}",
            ]
            return random.choice(responses)
        
        elif is_where or is_when:
            responses = [
                f"Based on what I know: {best_response}",
                f"Here's the information I have: {best_response}",
            ]
            return random.choice(responses)
        
        else:
            # General statement or unknown question type
            responses = [
                f"Interesting! {best_response}",
                f"Here's what I think about that: {best_response}",
                f"Let me share what I know: {best_response}",
            ]
            return random.choice(responses)
    
    def _handle_unknown_question(self, question: str, context: ConversationContext) -> str:
        """Handle questions when no knowledge is found"""
        q = question.strip().rstrip('?')
        
        # Detect question type
        is_what = bool(re.match(r'^(?:what|what\'s)\s+', q, re.I))
        is_who = bool(re.match(r'^who\s+', q, re.I))
        is_why = bool(re.match(r'^why\s+', q, re.I))
        is_how = bool(re.match(r'^how\s+', q, re.I))
        is_where = bool(re.match(r'^where\s+', q, re.I))
        is_when = bool(re.match(r'^when\s+', q, re.I))
        
        # Extract subject
        subject = q
        for pattern in [r'^(?:what\s+(?:is|are|\'s|does|do)\s+)', 
                        r'^(?:who\s+(?:is|are|\'s)\s+)',
                        r'^(?:why\s+(?:is|are|does|do)\s+)',
                        r'^(?:how\s+(?:is|are|does|do|do\s+I|do\s+you)\s+)',
                        r'^(?:where\s+(?:is|are)\s+)',
                        r'^(?:when\s+(?:is|are|did)\s+)']:
            subject = re.sub(pattern, '', q, flags=re.I).strip()
        
        # Generate helpful response based on question type
        if is_what or is_who or is_why or is_how or is_where or is_when:
            if subject:
                responses = [
                    f"Hmm, I don't know much about {subject} yet. But I'm always learning! You can teach me by saying 'teach me {subject} is [your answer]'.",
                    f"I haven't learned about {subject} yet. Want to teach me? Just say 'teach me {subject} is...' and I'll remember it!",
                    f"That's a good question about {subject}, but I don't have that information yet. I'm learning from Wikipedia and our conversations though, so I might know it soon!",
                    f"I'm not sure about {subject} right now. But I keep learning new things from Wikipedia and from you — try teaching me and I'll remember!",
                ]
            else:
                responses = [
                    "I'm not sure about that yet, but I'm always learning! Try teaching me something and I'll remember it for next time.",
                    "That's beyond my knowledge right now. But I'm getting smarter every day — want to teach me?",
                    "I haven't learned that yet. Say 'teach me' and I'll remember it next time!",
                ]
            return random.choice(responses)
        
        # Not a question - might be a statement or command
        if len(question) > 50:
            # Long statement - acknowledge it
            return "That's interesting! I'm still learning to understand complex topics, but I appreciate you sharing that with me."
        
        # Short unknown input
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
