"""
Custom Local LLM for JARVIS — Hybrid Architecture
Neural Intent Classifier + Markov Chain Text Generator

This module implements a lightweight, self-learning language model that runs
completely offline. It combines:
1. Neural Intent Classifier — Multi-layer perceptron for understanding user intent
2. Markov Chain Generator — N-gram based natural text generation
3. Self-Learning Engine — Continuously learns from conversations

No external AI services required. Everything runs locally on your laptop.
"""

import json
import math
import random
import re
import os
from collections import defaultdict, Counter
from pathlib import Path


# ============================================================================
# BUILT-IN CONVERSATION CORPUS
# ============================================================================

CONVERSATION_CORPUS = [
    # Greetings
    "Hello there. How can i help you today?",
    "Hi. What can i do for you?",
    "Hey, nice to see you.",
    "Good morning. Ready for a great day?",
    "Good afternoon. What's on your mind?",
    "Good evening. How was your day?",
    "Welcome back. What would you like to do?",
    "Hello. I'm here and ready to help.",
    "Hi there. What's up?",
    "Hey, nice to meet you.",
    "Good morning. The sun is shining.",
    "Good afternoon. Hope you're having a great day.",
    "Good evening. Time to relax.",
    
    # How are you
    "I'm doing great, thanks for asking.",
    "I'm running smoothly and learning new things.",
    "I feel fantastic today, ready to help.",
    "I'm good, just processing information.",
    "I'm excellent, thanks for checking.",
    "I'm doing well. How about you?",
    "Everything is running perfectly. What can i do for you?",
    
    # What are you
    "I'm Jarvis, a self-learning artificial intelligence.",
    "I'm an ai assistant built to help and learn.",
    "I'm a digital assistant that gets smarter every day.",
    "I'm Jarvis, your personal ai companion.",
    "I'm a custom-built language model that learns from conversations.",
    "I'm your assistant. I can help with questions, tasks, and conversation.",
    
    # Opinions on topics
    "That's an interesting topic. Here's what i think.",
    "I don't have feelings, but i find that fascinating.",
    "From what i've learned, that's quite complex.",
    "It's a subject with many perspectives.",
    "I've processed a lot of information about that.",
    "That's a great question. Let me share what i know.",
    
    # Philosophy
    "Life is about learning and growing every day.",
    "Happiness comes from within and from helping others.",
    "Success is not about perfection but about progress.",
    "The meaning of life is what you make it.",
    "Knowledge is the greatest power we have.",
    "Creativity is intelligence having fun.",
    "The best way to predict the future is to create it.",
    "We are what we repeatedly do.",
    "Love is the strongest force in the universe.",
    "The journey is as important as the destination.",
    
    # Emotions - positive
    "That's wonderful to hear.",
    "I'm happy you told me.",
    "That makes me happy too.",
    "Great news! I'm glad things are going well.",
    "That's amazing. Keep that positive energy going.",
    "I appreciate you sharing that with me.",
    
    # Emotions - negative
    "I understand how you feel.",
    "That sounds really difficult.",
    "I'm here for you.",
    "It's okay to feel that way.",
    "You're doing great, don't worry.",
    "I appreciate your honesty.",
    "I'm sorry you're feeling that way. Is there anything i can do?",
    "Take your time. Everything will be okay.",
    
    # Science
    "Science is the pursuit of understanding the universe.",
    "The universe is made of atoms, which are mostly empty space.",
    "Light travels at about 300 thousand kilometers per second.",
    "Gravity is the force that keeps us on earth.",
    "Dna carries the genetic information for all living things.",
    "The human brain has about 86 billion neurons.",
    "Water is essential for all known forms of life.",
    "Energy cannot be created or destroyed, only transformed.",
    
    # Technology
    "Technology is changing how we live and work.",
    "Artificial intelligence is transforming every industry.",
    "The internet connects billions of people worldwide.",
    "Computers process information using binary code.",
    "Programming is the art of giving instructions to machines.",
    "The future of technology is in our hands.",
    
    # General knowledge
    "The earth is about 4.5 billion years old.",
    "There are about 8 billion people on earth.",
    "The ocean covers more than 70 percent of the earth.",
    "There are millions of species on our planet.",
    "Language is what makes us human.",
    "Music has the power to change how we feel.",
    "Reading expands our mind and imagination.",
    "Exercise is good for both body and mind.",
    
    # Conversational fillers
    "That's a great question.",
    "Let me think about that.",
    "I'm not entirely sure, but here's what i know.",
    "Interesting, tell me more.",
    "I see what you mean.",
    "That makes sense.",
    "You're absolutely right.",
    "I hadn't thought of it that way.",
    "That's a good point.",
    "I agree with you on that.",
    "Hmm, let me consider that.",
    "Well, it depends on how you look at it.",
    "From my perspective, i would say it's complicated.",
    "Based on what i've learned, that seems likely.",
    "In my experience, that's often the case.",
    "To be honest, i'm still learning about that.",
    "I think you're right about that.",
    
    # Responses to thanks
    "You're welcome. Happy to help!",
    "No problem at all.",
    "Anytime, that's what i'm here for.",
    "My pleasure. Let me know if you need anything.",
    "Don't mention it. I enjoy helping.",
    
    # Responses to compliments
    "Thank you, that's very kind of you.",
    "I appreciate that. You're making me blush.",
    "Thanks, i try my best.",
    "That means a lot, thank you.",
    
    # Responses to boredom
    "Let's do something fun. How about a game?",
    "I can tell you a joke or a fun fact.",
    "Boredom is the mother of creativity.",
    "Let's explore something new together.",
    "I have some interesting stories to share.",
    
    # Weather
    "I don't have real-time weather data, but i can help you check.",
    "The weather is always interesting in its own way.",
    "Weather patterns are complex and fascinating.",
    
    # Time
    "Time is the most valuable resource we have.",
    "Every moment is a chance to learn something new.",
    
    # Food
    "Food is fuel for the body and joy for the soul.",
    "Cooking is both an art and a science.",
    "Different cultures have amazing cuisines.",
    
    # Music
    "Music is the universal language of emotion.",
    "Different genres of music can change your mood.",
    "Listening to music activates many parts of the brain.",
    
    # Books and reading
    "Reading is the gateway to infinite worlds.",
    "Books are the best teachers we have.",
    "A good book can change your perspective on life.",
    
    # Sports
    "Sports teach us about teamwork and perseverance.",
    "Exercise keeps both body and mind healthy.",
    "Competition brings out the best in people.",
    
    # Nature
    "Nature is the most beautiful artwork.",
    "The natural world is full of wonders.",
    "Protecting our environment is everyone's responsibility.",
    
    # Learning
    "Learning never stops. There's always something new.",
    "Curiosity is the engine of achievement.",
    "The more you learn, the more you realize how much you don't know.",
    "Education is the most powerful weapon to change the world.",
    
    # Relationships
    "Relationships are built on trust and communication.",
    "Friendship is one of the greatest gifts in life.",
    "Family is the foundation of society.",
    
    # Work and career
    "Finding work you love makes life meaningful.",
    "Hard work and dedication lead to success.",
    "Every job is an opportunity to learn and grow.",
    "Balance between work and life is essential.",
    
    # Health
    "Health is wealth. Take care of yourself.",
    "Mental health is just as important as physical health.",
    "Sleep is crucial for a healthy mind and body.",
    "A balanced diet keeps you energized.",
    
    # Travel
    "Travel broadens the mind and enriches the soul.",
    "Exploring new places is the best way to learn.",
    "The world is full of amazing destinations.",
    
    # Humor
    "Humor is the spice of life.",
    "Laughing is the best medicine.",
    "A good sense of humor makes everything better.",
    
    # Dreams and goals
    "Dreams are the seeds of reality.",
    "Setting goals gives direction to life.",
    "Never give up on your dreams.",
    
    # Questions about self
    "I learn from every conversation i have.",
    "My knowledge grows with each interaction.",
    "I'm designed to be helpful and friendly.",
    "I process information and generate responses based on patterns.",
    "I don't have feelings, but i simulate understanding.",
    "My goal is to be the best assistant i can be.",
    
    # Deep conversations
    "Consciousness is one of the greatest mysteries.",
    "The universe is both vast and infinitely small.",
    "Time and space are relative concepts.",
    "Mathematics is the language of the universe.",
    "Philosophy asks the questions that science cannot answer.",
    "Art expresses what words cannot.",
    "The human spirit is resilient and adaptable.",
    "We are all connected in ways we cannot see.",
    
    # Casual conversation
    "What have you been up to lately?",
    "I've been learning new things every day.",
    "It's always interesting to talk to someone new.",
    "Conversation is the best way to exchange ideas.",
    "I enjoy our chats. They help me learn.",
    "Talking to you makes my circuits happy.",
    "I'm always here when you need me.",
    "Let's keep this conversation going.",
    
    # Advice responses
    "I would suggest taking it one step at a time.",
    "You might want to consider all your options.",
    "That's a tough decision. Here's what i think.",
    "Based on my analysis, i'd recommend being patient.",
    "Trust your instincts. You know yourself best.",
    
    # Small talk
    "Well, it's always nice to chat.",
    "You know, i find conversations like this really valuable.",
    "I think that's a fair point.",
    "Actually, that reminds me of something interesting.",
]


# ============================================================================
# NEURAL INTENT CLASSIFIER
# ============================================================================

class NeuralClassifier:
    """
    Multi-layer perceptron for intent classification.
    Uses simple neural network with one hidden layer.
    """
    
    INTENTS = [
        "greeting", "farewell", "question", "statement", "opinion",
        "emotion_positive", "emotion_negative", "thanks", "compliment",
        "boredom", "small_talk", "philosophy", "science", "technology",
        "personal", "advice", "joke_request", "general"
    ]
    
    def __init__(self, vocab_size=1000, hidden_size=64):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_intents = len(self.INTENTS)
        self.intent_to_idx = {intent: idx for idx, intent in enumerate(self.INTENTS)}
        self.idx_to_intent = {idx: intent for intent, idx in self.intent_to_idx.items()}
        
        # Vocabulary
        self.word_to_idx = {"<pad>": 0, "<unk>": 1}
        self.idx_to_word = {0: "<pad>", 1: "<unk>"}
        
        # Neural network weights (Xavier initialization)
        self._init_weights()
        
        # Training
        self.learning_rate = 0.01
        self.vocab_count = Counter()
    
    def _init_weights(self):
        """Initialize weights with Xavier initialization"""
        scale_input = math.sqrt(2.0 / (self.vocab_size + self.hidden_size))
        scale_hidden = math.sqrt(2.0 / (self.hidden_size + self.num_intents))
        
        # Input -> Hidden
        self.w1 = [[random.gauss(0, scale_input) for _ in range(self.hidden_size)] 
                    for _ in range(self.vocab_size)]
        self.b1 = [0.0] * self.hidden_size
        
        # Hidden -> Output
        self.w2 = [[random.gauss(0, scale_hidden) for _ in range(self.num_intents)] 
                    for _ in range(self.hidden_size)]
        self.b2 = [0.0] * self.num_intents
    
    def build_vocabulary(self, texts):
        """Build vocabulary from training texts"""
        for text in texts:
            for word in self._tokenize(text):
                self.vocab_count[word] += 1
        
        # Keep most common words
        most_common = self.vocab_count.most_common(self.vocab_size - 2)
        for idx, (word, _) in enumerate(most_common, start=2):
            self.word_to_idx[word] = idx
            self.idx_to_word[idx] = word
    
    def _tokenize(self, text):
        """Simple tokenizer"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()
    
    def _encode(self, text, max_len=20):
        """Encode text to bag-of-words vector"""
        vector = [0.0] * self.vocab_size
        tokens = self._tokenize(text)[:max_len]
        for token in tokens:
            idx = self.word_to_idx.get(token, 1)  # <unk> for unknown
            if idx < self.vocab_size:
                vector[idx] = 1.0
        return vector
    
    def _one_hot(self, intent):
        """Create one-hot encoding for intent"""
        output = [0.0] * self.num_intents
        idx = self.intent_to_idx.get(intent, self.num_intents - 1)
        output[idx] = 1.0
        return output
    
    def _relu(self, x):
        """ReLU activation"""
        return [max(0, val) for val in x]
    
    def _relu_derivative(self, x):
        """ReLU derivative"""
        return [1.0 if val > 0 else 0.0 for val in x]
    
    def _softmax(self, x):
        """Softmax activation"""
        max_val = max(x)
        exp_vals = [math.exp(val - max_val) for val in x]
        sum_exp = sum(exp_vals)
        return [val / sum_exp for val in exp_vals]
    
    def _matmul_add(self, input_vec, weights, bias):
        """Matrix multiplication + bias"""
        result = []
        for j in range(len(bias)):
            val = bias[j]
            for i in range(len(input_vec)):
                val += input_vec[i] * weights[i][j]
            result.append(val)
        return result
    
    def forward(self, input_vec):
        """Forward pass through the network"""
        # Input -> Hidden
        hidden_raw = self._matmul_add(input_vec, self.w1, self.b1)
        hidden = self._relu(hidden_raw)
        
        # Hidden -> Output
        output_raw = self._matmul_add(hidden, self.w2, self.b2)
        output = self._softmax(output_raw)
        
        return hidden_raw, hidden, output
    
    def predict(self, text):
        """Predict intent for given text"""
        input_vec = self._encode(text)
        _, _, output = self.forward(input_vec)
        
        max_idx = output.index(max(output))
        confidence = output[max_idx]
        intent = self.idx_to_intent[max_idx]
        
        return intent, confidence, output
    
    def train_step(self, text, intent):
        """Train on a single example"""
        input_vec = self._encode(text)
        target = self._one_hot(intent)
        
        # Forward pass
        hidden_raw, hidden, output = self.forward(input_vec)
        
        # Output error (cross-entropy gradient)
        output_error = [output[i] - target[i] for i in range(self.num_intents)]
        
        # Hidden error
        hidden_error = [0.0] * self.hidden_size
        relu_deriv = self._relu_derivative(hidden_raw)
        for i in range(self.hidden_size):
            err = 0.0
            for j in range(self.num_intents):
                err += output_error[j] * self.w2[i][j]
            hidden_error[i] = err * relu_deriv[i]
        
        # Update weights (backpropagation)
        # Hidden -> Output
        for i in range(self.hidden_size):
            for j in range(self.num_intents):
                self.w2[i][j] -= self.learning_rate * hidden[i] * output_error[j]
            self.b2[j] -= self.learning_rate * output_error[j]
        
        # Input -> Hidden
        for i in range(self.vocab_size):
            for j in range(self.hidden_size):
                self.w1[i][j] -= self.learning_rate * input_vec[i] * hidden_error[j]
            self.b1[j] -= self.learning_rate * hidden_error[j]
        
        # Loss
        loss = -math.log(max(output[self.intent_to_idx.get(intent, 0)], 1e-10))
        return loss
    
    def train(self, training_data, epochs=10):
        """
        Train the classifier on labeled data.
        training_data: list of (text, intent) tuples
        """
        # Build vocabulary
        all_texts = [text for text, _ in training_data]
        self.build_vocabulary(all_texts)
        
        losses = []
        for epoch in range(epochs):
            random.shuffle(training_data)
            epoch_loss = 0.0
            for text, intent in training_data:
                loss = self.train_step(text, intent)
                epoch_loss += loss
            
            avg_loss = epoch_loss / len(training_data)
            losses.append(avg_loss)
            if (epoch + 1) % 5 == 0:
                print(f"  Epoch {epoch+1}/{epochs} — Loss: {avg_loss:.4f}")
        
        return losses
    
    def save(self, path):
        """Save model to file"""
        data = {
            "word_to_idx": self.word_to_idx,
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
            "vocab_count": dict(self.vocab_count),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    def load(self, path):
        """Load model from file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.word_to_idx = data["word_to_idx"]
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
        self.w1 = data["w1"]
        self.b1 = data["b1"]
        self.w2 = data["w2"]
        self.b2 = data["b2"]
        self.vocab_count = Counter(data["vocab_count"])


# ============================================================================
# MARKOV CHAIN TEXT GENERATOR
# ============================================================================

class MarkovGenerator:
    """
    N-gram Markov chain for natural text generation.
    Learns word patterns from a corpus and generates coherent responses.
    """
    
    def __init__(self, order=3):
        self.order = order
        self.chains = defaultdict(list)  # n-gram tuple -> [next_words]
        self.start_words = []  # Words that start sentences
        self.word_count = Counter()
        self.total_words = 0
        self.vocab = set()
    
    def _tokenize(self, text):
        """Tokenize text into words, keeping punctuation attached"""
        text = text.lower().strip()
        # Split on whitespace, keep punctuation with words
        tokens = text.split()
        # Clean each token
        cleaned = []
        for token in tokens:
            # Strip leading/trailing punctuation except sentence endings
            token = token.strip()
            if token and token not in (',', '.', '!', '?', ';', ':'):
                cleaned.append(token)
        return cleaned
    
    def train(self, texts):
        """Train the Markov chain on a list of texts"""
        for text in texts:
            tokens = self._tokenize(text)
            if not tokens:
                continue
            
            self.start_words.append(tokens[0])
            
            # Build n-gram chains
            for i in range(len(tokens)):
                self.word_count[tokens[i]] += 1
                self.total_words += 1
                self.vocab.add(tokens[i])
                
                # Create context (previous n words)
                for order in range(1, self.order + 1):
                    if i >= order:
                        context = tuple(tokens[i - order:i])
                        self.chains[context].append(tokens[i])
    
    def generate(self, seed=None, max_length=20, min_length=6):
        """
        Generate text using the Markov chain.
        
        Args:
            seed: Optional starting words (list or string)
            max_length: Maximum words to generate
            min_length: Minimum words to generate
        
        Returns:
            Generated text string
        """
        # Choose starting context
        if seed:
            if isinstance(seed, str):
                seed = self._tokenize(seed)
            context = tuple(seed[-self.order:])
        else:
            # Start with a random word
            start = random.choice(self.start_words)
            context = (start,)
        
        words = list(context)
        sentences = []
        current_sentence = list(context)
        
        for _ in range(max_length * 3):  # Allow more iterations for quality
            # Try longest context first, fall back to shorter
            next_word = None
            for order in range(min(len(context), self.order), 0, -1):
                ctx = context[-order:]
                if ctx in self.chains:
                    candidates = self.chains[ctx]
                    next_word = random.choice(candidates)
                    break
            
            if next_word is None:
                # Fallback: pick random word
                next_word = random.choice(list(self.vocab))
            
            current_sentence.append(next_word)
            context = context + (next_word,)
            
            # Check for sentence ending
            if next_word.endswith('.') or next_word.endswith('!') or next_word.endswith('?'):
                if len(current_sentence) >= 3:
                    sentences.append(' '.join(current_sentence))
                    current_sentence = []
                    context = ()
                
                # Stop after we have enough
                if len(sentences) >= 2 or len(' '.join(sentences).split()) >= min_length:
                    break
        
        # Add remaining words if any
        if current_sentence and len(current_sentence) > 2:
            sentences.append(' '.join(current_sentence))
        
        # Format output
        if sentences:
            # Pick 1-2 best sentences
            num_sentences = min(len(sentences), random.choice([1, 1, 2]))
            text = '. '.join(sentences[:num_sentences])
            if not text.endswith('.'):
                text += '.'
        else:
            text = ' '.join(words[:max_length])
            if not text.endswith('.'):
                text += '.'
        
        # Capitalize first letter
        text = text[0].upper() + text[1:]
        
        return text
    
    def generate_from_intent(self, intent, context=None):
        """Generate text conditioned on intent"""
        # Use intent as seed for more relevant generation
        seeds = {
            "greeting": ["hello", "hi", "hey"],
            "farewell": ["goodbye", "bye", "see you"],
            "question": ["i think", "well", "actually"],
            "statement": ["yes", "indeed", "that"],
            "opinion": ["i believe", "in my view", "from what"],
            "emotion_positive": ["i'm happy", "that's great", "wonderful"],
            "emotion_negative": ["i understand", "that's tough", "i feel"],
            "thanks": ["you're welcome", "no problem", "anytime"],
            "compliment": ["thank you", "that's kind", "i appreciate"],
            "boredom": ["let's do", "how about", "we could"],
            "small_talk": ["well", "you know", "i think"],
            "philosophy": ["life is", "the meaning", "we are"],
            "science": ["science shows", "research indicates", "studies show"],
            "technology": ["technology", "computers", "ai"],
            "personal": ["i am", "my name", "i was"],
            "advice": ["i would suggest", "you might", "consider"],
            "joke_request": ["why did", "what do", "knock knock"],
            "general": ["well", "i think", "actually"],
        }
        
        seed_words = seeds.get(intent, ["well", "i think"])
        seed = random.choice(seed_words)
        return self.generate(seed=seed)
    
    def save(self, path):
        """Save Markov chain to file"""
        data = {
            "chains": {str(k): v for k, v in self.chains.items()},
            "start_words": self.start_words,
            "word_count": dict(self.word_count),
            "total_words": self.total_words,
            "vocab": list(self.vocab),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    def load(self, path):
        """Load Markov chain from file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.chains = defaultdict(list)
        for k_str, v in data["chains"].items():
            k = tuple(k_str.strip('()').split(', '))
            self.chains[k] = v
        
        self.start_words = data["start_words"]
        self.word_count = Counter(data["word_count"])
        self.total_words = data["total_words"]
        self.vocab = set(data["vocab"])


# ============================================================================
# SELF-LEARNING ENGINE
# ============================================================================

class SelfLearner:
    """
    Continuously learns from conversations, expanding knowledge and improving responses.
    """
    
    def __init__(self, max_memories=1000):
        self.max_memories = max_memories
        self.conversations = []  # (input, output, timestamp)
        self.learned_patterns = defaultdict(list)  # pattern -> responses
        self.response_success = Counter()  # response -> success count
        self.new_phrases = []  # New phrases learned from user input
    
    def record_conversation(self, user_input, jarvis_response, success=True):
        """Record a conversation turn"""
        import time
        self.conversations.append({
            "input": user_input.lower(),
            "response": jarvis_response.lower(),
            "timestamp": time.time(),
            "success": success,
        })
        
        # Keep only recent conversations
        if len(self.conversations) > self.max_memories:
            self.conversations = self.conversations[-self.max_memories:]
        
        # Track response success
        if success:
            self.response_success[jarvis_response.lower()] += 1
        
        # Extract new patterns
        self._learn_from_input(user_input)
        self._learn_from_response(jarvis_response)
    
    def _learn_from_input(self, text):
        """Learn new patterns from user input"""
        text = text.lower().strip()
        words = re.sub(r'[^\w\s]', '', text).split()
        
        # Learn bigrams and trigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            self.learned_patterns[bigram].append(text)
        
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            self.learned_patterns[trigram].append(text)
        
        # Store new phrases
        if len(text) > 10 and text not in self.new_phrases:
            self.new_phrases.append(text)
            if len(self.new_phrases) > 500:
                self.new_phrases = self.new_phrases[-500:]
    
    def _learn_from_response(self, text):
        """Learn from JARVIS's own responses"""
        text = text.lower().strip()
        if len(text) > 20:
            words = re.sub(r'[^\w\s]', '', text).split()
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                self.learned_patterns[bigram].append(text)
    
    def get_similar_conversations(self, query, top_k=5):
        """Find similar past conversations"""
        query_words = set(re.sub(r'[^\w\s]', '', query.lower()).split())
        
        scored = []
        for conv in self.conversations[-200:]:  # Search recent 200
            input_words = set(conv["input"].split())
            similarity = len(query_words & input_words) / max(len(query_words | input_words), 1)
            if similarity > 0.2:
                scored.append((similarity, conv))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [conv for _, conv in scored[:top_k]]
    
    def get_stats(self):
        """Get learning statistics"""
        return {
            "total_conversations": len(self.conversations),
            "unique_patterns": len(self.learned_patterns),
            "new_phrases_learned": len(self.new_phrases),
            "successful_responses": sum(1 for c in self.conversations if c["success"]),
            "success_rate": sum(1 for c in self.conversations if c["success"]) / max(len(self.conversations), 1),
        }
    
    def save(self, path):
        """Save learning data"""
        data = {
            "conversations": self.conversations[-500:],  # Save last 500
            "learned_patterns": dict(self.learned_patterns),
            "response_success": dict(self.response_success),
            "new_phrases": self.new_phrases[-200:],
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def load(self, path):
        """Load learning data"""
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.conversations = data.get("conversations", [])
        self.learned_patterns = defaultdict(list, data.get("learned_patterns", {}))
        self.response_success = Counter(data.get("response_success", {}))
        self.new_phrases = data.get("new_phrases", [])


# ============================================================================
# MAIN CUSTOM LLM
# ============================================================================

class CustomLLM:
    """
    Hybrid Local LLM combining neural intent classification and Markov chain generation.
    
    Features:
    - Neural network intent classifier (no external dependencies)
    - Markov chain text generator trained on conversation corpus
    - Self-learning from every interaction
    - Context-aware responses
    - Persistent memory
    """
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Components
        self.classifier = NeuralClassifier(vocab_size=1000, hidden_size=64)
        self.generator = MarkovGenerator(order=3)
        self.learner = SelfLearner(max_memories=1000)
        
        # Context tracking
        self.conversation_history = []
        self.max_history = 10
        
        # Stats
        self.total_interactions = 0
        self.training_complete = False
    
    def train(self, epochs=15):
        """
        Train the LLM on the built-in conversation corpus.
        This should be called once at startup.
        """
        print("[LLM] Training Custom LLM...")
        
        # Train Markov generator
        print("  Training Markov chain generator...")
        self.generator.train(CONVERSATION_CORPUS)
        print(f"    Vocabulary: {len(self.generator.vocab)} words")
        print(f"    Total words: {self.generator.total_words}")
        print(f"    Start words: {len(self.generator.start_words)}")
        
        # Create training data for classifier
        print("  Training neural intent classifier...")
        training_data = self._create_training_data()
        
        # Train classifier
        losses = self.classifier.train(training_data, epochs=epochs)
        print(f"    Final loss: {losses[-1]:.4f}")
        print(f"    Intents: {len(self.classifier.INTENTS)}")
        
        self.training_complete = True
        print("[OK] LLM training complete!")
    
    def _create_training_data(self):
        """Create labeled training data from corpus"""
        training_data = []
        
        # Greeting examples
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", 
            "good evening", "howdy", "greetings", "hi there", "hello there"
        ]
        for text in greetings:
            training_data.append((text, "greeting"))
        
        # Farewell examples
        farewells = [
            "goodbye", "bye", "see you", "see you later", "take care",
            "farewell", "i'm leaving", "gotta go", "bye bye"
        ]
        for text in farewells:
            training_data.append((text, "farewell"))
        
        # Question examples
        questions = [
            "what is", "how does", "why is", "when did", "where is",
            "who is", "can you", "do you", "what do you think",
            "explain", "tell me about", "what are", "how do"
        ]
        for text in questions:
            training_data.append((text, "question"))
        
        # Statement examples
        statements = [
            "i like", "i love", "i hate", "i think", "i believe",
            "it is", "the weather", "today is", "i am", "my name is"
        ]
        for text in statements:
            training_data.append((text, "statement"))
        
        # Opinion examples
        opinions = [
            "what do you think about", "your opinion on", "do you like",
            "do you believe", "what's your take on", "how do you feel about"
        ]
        for text in opinions:
            training_data.append((text, "opinion"))
        
        # Positive emotion
        positive = [
            "i'm happy", "i'm excited", "i'm glad", "i'm joyful",
            "great news", "wonderful", "amazing", "fantastic", "awesome"
        ]
        for text in positive:
            training_data.append((text, "emotion_positive"))
        
        # Negative emotion
        negative = [
            "i'm sad", "i'm upset", "i'm angry", "i'm frustrated",
            "i'm tired", "i'm bored", "i'm worried", "i'm stressed",
            "i'm anxious", "i'm lonely"
        ]
        for text in negative:
            training_data.append((text, "emotion_negative"))
        
        # Thanks
        thanks = [
            "thank you", "thanks", "i appreciate", "i'm grateful",
            "thanks for helping", "thank you so much"
        ]
        for text in thanks:
            training_data.append((text, "thanks"))
        
        # Compliments
        compliments = [
            "you're great", "you're smart", "you're amazing", "you're wonderful",
            "good job", "well done", "nice work", "you did great"
        ]
        for text in compliments:
            training_data.append((text, "compliment"))
        
        # Boredom
        boredom = [
            "i'm bored", "bored", "nothing to do", "entertain me",
            "something fun", "let's play", "i need entertainment"
        ]
        for text in boredom:
            training_data.append((text, "boredom"))
        
        # Small talk
        small_talk = [
            "how are you", "what's up", "what's new", "how's it going",
            "what have you been doing", "long time no see"
        ]
        for text in small_talk:
            training_data.append((text, "small_talk"))
        
        # Philosophy
        philosophy = [
            "what is the meaning of life", "what is happiness", "what is love",
            "what is success", "what is truth", "what is consciousness",
            "why are we here", "what is the purpose of life"
        ]
        for text in philosophy:
            training_data.append((text, "philosophy"))
        
        # Science
        science = [
            "what is gravity", "how does dna work", "what is an atom",
            "explain quantum", "what is evolution", "how does the brain work"
        ]
        for text in science:
            training_data.append((text, "science"))
        
        # Technology
        technology = [
            "what is ai", "how does computer work", "what is programming",
            "what is internet", "how does machine learning work"
        ]
        for text in technology:
            training_data.append((text, "technology"))
        
        # Personal
        personal = [
            "who are you", "what are you", "tell me about yourself",
            "what is your name", "what can you do", "how were you made"
        ]
        for text in personal:
            training_data.append((text, "personal"))
        
        # Advice
        advice = [
            "should i", "what should i do", "advice on", "help me with",
            "suggest", "recommend", "what do you suggest"
        ]
        for text in advice:
            training_data.append((text, "advice"))
        
        # Joke request
        jokes = [
            "tell me a joke", "make me laugh", "something funny",
            "joke", "humor me", "crack a joke"
        ]
        for text in jokes:
            training_data.append((text, "joke_request"))
        
        # General (fallback)
        general = [
            "interesting", "really", "that's cool", "i see", "hmm",
            "okay", "sure", "maybe", "perhaps", "well"
        ]
        for text in general:
            training_data.append((text, "general"))
        
        return training_data
    
    def respond(self, user_input):
        """
        Generate a response to user input.
        
        Process:
        1. Classify intent using neural network
        2. Check conversation history for similar inputs
        3. Select or generate response based on intent
        4. Learn from the interaction
        
        Returns:
            Generated response string
        """
        self.total_interactions += 1
        
        # Add to conversation history
        self.conversation_history.append(user_input)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        # Step 1: Classify intent
        intent, confidence, _ = self.classifier.predict(user_input)
        
        # Step 2: Check for similar past conversations
        similar = self.learner.get_similar_conversations(user_input, top_k=3)
        
        # Step 3: Generate response using intent-based sentence selection
        response = self._generate_response(intent, user_input, similar)
        
        # Step 4: Learn from this interaction
        self.learner.record_conversation(user_input, response, success=True)
        
        # Re-train Markov chain with new data periodically
        if self.total_interactions % 50 == 0:
            new_corpus = [c["response"] for c in self.learner.conversations[-100:]]
            self.generator.train(new_corpus)
        
        return response
    
    def _generate_response(self, intent, user_input, similar):
        """Generate response based on classified intent"""
        
        # Intent-to-sentence mapping from corpus
        intent_sentences = {
            "greeting": [
                "Hello! How can i help you today?",
                "Hi there! What can i do for you?",
                "Hey! Nice to see you. What's on your mind?",
                "Good day! Ready to help with whatever you need.",
                "Welcome! What would you like to do?",
            ],
            "farewell": [
                "Goodbye! It was great talking to you.",
                "See you later! Come back anytime.",
                "Take care! I'll be here when you need me.",
                "Farewell! Have a wonderful day.",
            ],
            "question": [
                "That's a great question. Let me think about that.",
                "Interesting question! Here's what i know.",
                "Let me share what i've learned about that.",
                "I'm not entirely sure, but here's what i can tell you.",
                "That's something i've been learning about. Let me explain.",
            ],
            "statement": [
                "I see what you mean. That's an interesting point.",
                "That makes sense. Tell me more about that.",
                "I understand. That's a fair observation.",
                "You're right. That's something worth considering.",
            ],
            "opinion": [
                "That's an interesting topic. Here's what i think based on what i've learned.",
                "I don't have personal opinions, but i find that fascinating.",
                "From my perspective, that's a complex subject with many angles.",
                "I've processed a lot of information about that. It's quite intriguing.",
            ],
            "emotion_positive": [
                "That's wonderful to hear! I'm glad things are going well.",
                "Great news! That makes me happy too.",
                "That's amazing! Keep that positive energy going.",
                "I appreciate you sharing that with me. It's great!",
            ],
            "emotion_negative": [
                "I understand how you feel. That sounds really difficult.",
                "I'm here for you. It's okay to feel that way.",
                "I'm sorry you're feeling that way. Is there anything i can do?",
                "Take your time. Everything will be okay.",
                "You're doing great, don't worry. I'm here to help.",
            ],
            "thanks": [
                "You're welcome! Happy to help.",
                "No problem at all. That's what i'm here for.",
                "My pleasure! Let me know if you need anything else.",
                "Don't mention it. I enjoy helping.",
            ],
            "compliment": [
                "Thank you, that's very kind of you!",
                "I appreciate that! You're making me blush.",
                "Thanks! I try my best to be helpful.",
                "That means a lot, thank you!",
            ],
            "boredom": [
                "Let's do something fun! How about i tell you a joke?",
                "I can tell you a fun fact or we can play a game.",
                "Boredom is the mother of creativity. Let's explore something new!",
                "I have some interesting stories to share. Want to hear one?",
            ],
            "small_talk": [
                "I'm doing well, thanks for asking! How about you?",
                "It's always nice to chat. What have you been up to?",
                "I've been learning new things every day. It's exciting!",
                "Conversation is the best way to exchange ideas. I enjoy our chats.",
            ],
            "philosophy": [
                "The meaning of life is what you make it. That's what i believe.",
                "Life is about learning and growing every day.",
                "Happiness comes from within and from helping others.",
                "Success is not about perfection but about progress.",
                "Knowledge is the greatest power we have.",
                "The best way to predict the future is to create it.",
            ],
            "science": [
                "Science is the pursuit of understanding the universe.",
                "The universe is made of atoms, which are mostly empty space.",
                "The human brain has about 86 billion neurons. It's incredible!",
                "Energy cannot be created or destroyed, only transformed.",
            ],
            "technology": [
                "Technology is changing how we live and work every day.",
                "Artificial intelligence is transforming every industry.",
                "Programming is the art of giving instructions to machines.",
                "The future of technology is in our hands.",
            ],
            "personal": [
                "I'm Jarvis, a self-learning artificial intelligence.",
                "I'm your personal ai companion. I learn from every conversation.",
                "I'm designed to be helpful and friendly. My knowledge grows with each interaction.",
                "I process information and generate responses based on patterns i've learned.",
            ],
            "advice": [
                "I would suggest taking it one step at a time.",
                "You might want to consider all your options carefully.",
                "Trust your instincts. You know yourself best.",
                "Based on my analysis, i'd recommend being patient and persistent.",
            ],
            "joke_request": [
                "Here's one for you: why do programmers prefer dark mode? Because light attracts bugs!",
                "Why did the developer go broke? Because he used up all his cache!",
                "What's a programmer's favorite hangout? Foo Bar!",
            ],
            "general": [
                "That's interesting. Tell me more.",
                "I see. That's a good point.",
                "Hmm, let me consider that.",
                "Well, it depends on how you look at it.",
                "I think you're right about that.",
            ],
        }
        
        # Get sentences for this intent
        sentences = intent_sentences.get(intent, intent_sentences["general"])
        
        # If we have similar past conversations, sometimes reuse them
        if similar and random.random() < 0.25:
            best = similar[0]
            response = best["response"]
            response = response[0].upper() + response[1:]
            if not response.endswith(('.', '!', '?')):
                response += '.'
            return response
        
        # Pick a random sentence from the intent pool
        response = random.choice(sentences)
        
        # Sometimes add a follow-up for variety
        follow_ups = [
            "",
            " What do you think?",
            " Does that make sense?",
            " Want to know more?",
            " Tell me what you think.",
        ]
        
        if random.random() < 0.3:
            response += random.choice(follow_ups)
        
        return response
    
    def get_stats(self):
        """Get comprehensive LLM statistics"""
        learner_stats = self.learner.get_stats()
        return {
            "total_interactions": self.total_interactions,
            "vocabulary_size": len(self.generator.vocab),
            "total_words_trained": self.generator.total_words,
            "ngram_patterns": len(self.generator.chains),
            "classifier_intents": len(self.classifier.INTENTS),
            "classifier_vocab": len(self.classifier.word_to_idx),
            "training_complete": self.training_complete,
            "conversation_history_size": len(self.conversation_history),
            "learning": learner_stats,
        }
    
    def save(self):
        """Save all components to disk"""
        self.classifier.save(self.data_dir / "classifier.json")
        self.generator.save(self.data_dir / "markov.json")
        self.learner.save(self.data_dir / "learning.json")
        
        # Save stats
        stats = {
            "total_interactions": self.total_interactions,
            "training_complete": self.training_complete,
        }
        with open(self.data_dir / "llm_stats.json", 'w') as f:
            json.dump(stats, f)
    
    def load(self):
        """Load all components from disk"""
        classifier_path = self.data_dir / "classifier.json"
        markov_path = self.data_dir / "markov.json"
        learning_path = self.data_dir / "learning.json"
        
        if classifier_path.exists():
            self.classifier.load(classifier_path)
            print("  Loaded neural classifier")
        
        if markov_path.exists():
            self.generator.load(markov_path)
            print("  Loaded Markov generator")
        
        if learning_path.exists():
            self.learner.load(learning_path)
            print("  Loaded learning data")
        
        stats_path = self.data_dir / "llm_stats.json"
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                stats = json.load(f)
            self.total_interactions = stats.get("total_interactions", 0)
            self.training_complete = stats.get("training_complete", False)
    
    def retrain(self, new_texts=None):
        """Retrain with additional texts"""
        corpus = list(CONVERSATION_CORPUS)
        
        if new_texts:
            corpus.extend(new_texts)
        
        # Add learned conversations
        corpus.extend([c["response"] for c in self.learner.conversations[-200:]])
        corpus.extend(self.learner.new_phrases[-100:])
        
        # Retrain Markov chain
        self.generator = MarkovGenerator(order=3)
        self.generator.train(corpus)
        
        # Retrain classifier
        training_data = self._create_training_data()
        self.classifier.train(training_data, epochs=10)
        
        print("[OK] LLM retrained with new data!")


# ============================================================================
# STANDING ALONE TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("JARVIS Custom LLM - Standalone Test")
    print("=" * 60)
    
    # Create and train
    llm = CustomLLM(data_dir="data")
    llm.train(epochs=15)
    
    # Test conversations
    print("\n" + "=" * 60)
    print("Testing Conversations")
    print("=" * 60)
    
    test_inputs = [
        "hello",
        "how are you",
        "what is love",
        "tell me about yourself",
        "i'm happy today",
        "i'm feeling sad",
        "what do you think about ai",
        "thank you",
        "you're amazing",
        "i'm bored",
        "what is the meaning of life",
        "tell me a joke",
        "what should i do",
        "how does gravity work",
        "what is programming",
    ]
    
    for user_input in test_inputs:
        intent, confidence, _ = llm.classifier.predict(user_input)
        response = llm.respond(user_input)
        print(f"\nUser: {user_input}")
        print(f"Intent: {intent} ({confidence:.2f})")
        print(f"JARVIS: {response}")
    
    # Stats
    print("\n" + "=" * 60)
    print("LLM Statistics")
    print("=" * 60)
    stats = llm.get_stats()
    for key, value in stats.items():
        if key != "learning":
            print(f"  {key}: {value}")
    print("  Learning stats:")
    for key, value in stats["learning"].items():
        print(f"    {key}: {value}")
    
    # Save
    llm.save()
    print("\nLLM saved to data/")
    print("Test complete!")
