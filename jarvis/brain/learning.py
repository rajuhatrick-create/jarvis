"""
Learning AI Engine - A completely local AI that learns from interactions.
Uses TF-IDF similarity matching and pattern generalization to understand natural language.
Learns automatically from user corrections, teaching commands, and successful interactions.
"""

import json
import re
import math
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import Counter

logger = logging.getLogger('JARVIS.brain.learning')


@dataclass
class MemoryEntry:
    """A single memory entry storing a learned pattern"""
    id: str
    patterns: List[str]  # Variations of input that map to this response
    response: str
    intent: str  # Associated intent (if any)
    success_count: int = 0
    failure_count: int = 0
    created_at: str = ""
    last_used: str = ""
    category: str = "general"  # general, fact, command, conversation
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def confidence_score(self) -> float:
        """Calculate confidence based on usage history"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5  # Neutral for new entries
        score = self.success_count / total
        # Boost score for frequently used entries
        usage_boost = min(0.2, math.log1p(self.success_count) * 0.05)
        return min(1.0, score + usage_boost)


class TFIDFMatcher:
    """Simple TF-IDF based text similarity matcher"""
    
    def __init__(self):
        self.document_freq: Counter = Counter()
        self.documents: List[str] = []
        self._idf_cache: Dict[str, float] = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        text = text.lower().strip()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split and filter short tokens
        tokens = [t for t in text.split() if len(t) > 1]
        return tokens
    
    def _ngrams(self, tokens: List[str], n: int = 2) -> List[str]:
        """Generate n-grams from tokens"""
        return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    
    def add_document(self, text: str):
        """Add a document to the index"""
        tokens = set(self._tokenize(text))
        for token in tokens:
            self.document_freq[token] += 1
        self.documents.append(text)
        self._idf_cache.clear()  # Invalidate cache
    
    def _idf(self, term: str) -> float:
        """Calculate inverse document frequency"""
        if term not in self._idf_cache:
            N = len(self.documents)
            df = self.document_freq.get(term, 0)
            self._idf_cache[term] = math.log((1 + N) / (1 + df)) + 1
        return self._idf_cache[term]
    
    def _tf(self, term: str, tokens: List[str]) -> float:
        """Calculate term frequency"""
        if not tokens:
            return 0
        return tokens.count(term) / len(tokens)
    
    def _tfidf_vector(self, text: str) -> Dict[str, float]:
        """Calculate TF-IDF vector for text"""
        tokens = self._tokenize(text)
        vector = {}
        for term in set(tokens):
            tf = self._tf(term, tokens)
            idf = self._idf(term)
            vector[term] = tf * idf
        # Also add bigrams
        bigrams = self._ngrams(tokens, 2)
        for bg in bigrams:
            vector[bg] = 0.5 * self._idf(bg)
        return vector
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        vec1 = self._tfidf_vector(text1)
        vec2 = self._tfidf_vector(text2)
        
        # Cosine similarity
        common_terms = set(vec1.keys()) & set(vec2.keys())
        if not common_terms:
            return 0.0
        
        dot_product = sum(vec1[t] * vec2[t] for t in common_terms)
        norm1 = math.sqrt(sum(v**2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v**2 for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class LearningAI:
    """Self-learning AI engine that improves from interactions"""
    
    def __init__(self, config: Dict, sqlite_db=None):
        self.config = config.get('learning', {})
        self.memory: Dict[str, MemoryEntry] = {}
        self.matcher = TFIDFMatcher()
        self.conversation_history: List[Dict] = []
        self.max_history = self.config.get('max_history', 100)
        self.auto_learn = self.config.get('auto_learn', True)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.3)
        self.max_memories = self.config.get('max_memories', 500)
        self.sqlite_db = sqlite_db
        
        # Load saved memory
        self._load_memory()
        logger.info(f"LearningAI initialized with {len(self.memory)} memories")
    
    def _get_storage_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "data" / "memory.json"
    
    def _load_memory(self):
        """Load memory from SQLite or disk"""
        # Try SQLite first
        if self.sqlite_db and self.sqlite_db.is_available():
            try:
                data = self.sqlite_db.load_memory()
                for item in data.get('memories', []):
                    # Filter out SQLite-specific fields not in MemoryEntry
                    clean_item = {k: v for k, v in item.items() if k in MemoryEntry.__dataclass_fields__}
                    entry = MemoryEntry(**clean_item)
                    self.memory[entry.id] = entry
                    for pattern in entry.patterns:
                        self.matcher.add_document(pattern)
                logger.info(f"Loaded {len(self.memory)} memories from SQLite")
                return
            except Exception as e:
                logger.error(f"Error loading memory from SQLite: {e}")
        
        # Fallback to local disk
        path = self._get_storage_path()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for item in data.get('memories', []):
                        entry = MemoryEntry(**item)
                        self.memory[entry.id] = entry
                        for pattern in entry.patterns:
                            self.matcher.add_document(pattern)
                logger.info(f"Loaded {len(self.memory)} memories from disk")
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
    
    def _save_memory(self):
        """Save memory to SQLite or disk"""
        data = {
            'memories': [asdict(m) for m in self.memory.values()],
            'stats': self.get_stats()
        }
        
        # Try SQLite first
        if self.sqlite_db and self.sqlite_db.is_available():
            try:
                self.sqlite_db.save_memory(data)
                return
            except Exception as e:
                logger.error(f"Error saving memory to SQLite: {e}")
        
        # Fallback to local disk
        path = self._get_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def find_match(self, text: str) -> Optional[Tuple[MemoryEntry, float]]:
        """Find the best matching memory entry for input text"""
        if not self.memory:
            return None
        
        best_match = None
        best_score = 0.0
        
        for entry in self.memory.values():
            # Check against all patterns in this entry
            for pattern in entry.patterns:
                score = self.matcher.similarity(text, pattern)
                # Boost score for entries with higher confidence
                weighted_score = score * (0.7 + 0.3 * entry.confidence_score())
                if weighted_score > best_score:
                    best_score = weighted_score
                    best_match = entry
        
        if best_match and best_score >= self.similarity_threshold:
            logger.info(f"LearningAI match: '{text}' → '{best_match.response}' (score: {best_score:.3f})")
            return (best_match, best_score)
        return None
    
    def learn(self, patterns: List[str], response: str, intent: str = "", 
              category: str = "general") -> MemoryEntry:
        """Add a new memory entry"""
        # Check if similar entry exists
        existing = self._find_similar_entry(patterns[0])
        if existing:
            # Merge with existing entry
            for pattern in patterns:
                if pattern not in existing.patterns:
                    existing.patterns.append(pattern)
                    self.matcher.add_document(pattern)
            existing.success_count += 1
            logger.info(f"Merged with existing memory: {existing.id}")
            self._save_memory()
            return existing
        
        # Create new entry
        entry_id = f"mem_{len(self.memory)}_{int(datetime.now().timestamp())}"
        entry = MemoryEntry(
            id=entry_id,
            patterns=patterns,
            response=response,
            intent=intent,
            category=category
        )
        
        # Add to TF-IDF index
        for pattern in patterns:
            self.matcher.add_document(pattern)
        
        self.memory[entry_id] = entry
        
        # Enforce max memories
        self._enforce_max_memories()
        
        self._save_memory()
        logger.info(f"Learned new pattern: {patterns[0]} → {response[:50]}...")
        return entry
    
    def _find_similar_entry(self, text: str) -> Optional[MemoryEntry]:
        """Find a similar existing entry"""
        best = None
        best_score = 0.0
        for entry in self.memory.values():
            for pattern in entry.patterns:
                score = self.matcher.similarity(text, pattern)
                if score > best_score and score > 0.7:  # High threshold for merging
                    best_score = score
                    best = entry
        return best
    
    def _enforce_max_memories(self):
        """Remove least useful memories if over limit"""
        if len(self.memory) <= self.max_memories:
            return
        
        # Sort by usefulness (success count * confidence)
        sorted_memories = sorted(
            self.memory.values(),
            key=lambda m: m.success_count * m.confidence_score()
        )
        
        # Remove least useful
        to_remove = sorted_memories[:len(self.memory) - self.max_memories]
        for entry in to_remove:
            del self.memory[entry.id]
        logger.info(f"Pruned {len(to_remove)} old memories")
    
    def record_success(self, entry_id: str):
        """Record a successful use of a memory"""
        if entry_id in self.memory:
            self.memory[entry_id].success_count += 1
            self.memory[entry_id].last_used = datetime.now().isoformat()
            self._save_memory()
    
    def record_failure(self, entry_id: str):
        """Record a failed use of a memory"""
        if entry_id in self.memory:
            self.memory[entry_id].failure_count += 1
            self._save_memory()
    
    def teach(self, user_input: str, response: str, category: str = "general") -> MemoryEntry:
        """Explicit teaching: user tells JARVIS how to respond"""
        # Generate variations of the input
        variations = self._generate_variations(user_input)
        entry = self.learn(variations, response, category=category)
        logger.info(f"Taught: '{user_input}' → '{response}'")
        return entry
    
    def _generate_variations(self, text: str) -> List[str]:
        """Generate variations of input text for better matching"""
        variations = [text.lower().strip()]
        
        # Add question form
        if not text.endswith('?'):
            variations.append(f"what is {text}?")
            variations.append(f"tell me about {text}")
        
        # Add command form
        variations.append(f"jarvis {text}")
        
        return list(set(variations))
    
    def forget(self, entry_id: str) -> bool:
        """Remove a memory entry"""
        if entry_id in self.memory:
            del self.memory[entry_id]
            self._save_memory()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get learning statistics"""
        total_memories = len(self.memory)
        total_patterns = sum(len(m.patterns) for m in self.memory.values())
        total_successes = sum(m.success_count for m in self.memory.values())
        total_failures = sum(m.failure_count for m in self.memory.values())
        
        # Category breakdown
        categories = Counter(m.category for m in self.memory.values())
        
        return {
            'total_memories': total_memories,
            'total_patterns': total_patterns,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'accuracy': total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0,
            'categories': dict(categories),
            'memory_usage': f"{total_memories}/{self.max_memories}",
        }
    
    def get_recent_learnings(self, limit: int = 10) -> List[Dict]:
        """Get recently learned entries"""
        sorted_entries = sorted(
            self.memory.values(),
            key=lambda m: m.created_at,
            reverse=True
        )
        return [asdict(e) for e in sorted_entries[:limit]]
    
    def get_top_patterns(self, limit: int = 10) -> List[Dict]:
        """Get most used patterns"""
        sorted_entries = sorted(
            self.memory.values(),
            key=lambda m: m.success_count,
            reverse=True
        )
        return [asdict(e) for e in sorted_entries[:limit]]
    
    def auto_learn_from_interaction(self, user_input: str, response: str, 
                                     was_successful: bool = True):
        """Automatically learn from interactions"""
        if not self.auto_learn:
            return
        
        # Only learn from successful interactions with substantial content
        if was_successful and len(response) > 20 and len(user_input) > 5:
            # Don't learn system commands - only learn new knowledge
            if not any(keyword in user_input.lower() for keyword in 
                      ['open', 'close', 'volume', 'list', 'search', 'time', 'date', 'help']):
                # Check if we already know this
                match = self.find_match(user_input)
                if match is None:
                    # Learn this new pattern
                    self.learn(
                        patterns=self._generate_variations(user_input),
                        response=response,
                        category="conversation"
                    )
    
    def add_fact(self, question: str, answer: str):
        """Add a factual knowledge entry"""
        q = question.lower().strip()
        variations = [
            q,
            f"what is {q}",
            f"what is {q}?",
            f"who is {q}",
            f"who is {q}?",
            f"tell me about {q}",
            f"{q} meaning",
            f"what does {q} mean",
            f"what does {q} mean?",
            f"explain {q}",
            f"define {q}",
            f"{q} definition",
        ]
        # Also add the answer as a variation for reverse lookup
        a = answer.lower().strip()
        variations.append(a)
        self.learn(list(set(variations)), answer, category="fact")
    
    def update_conversation_history(self, user_input: str, response: str):
        """Update conversation history for context-aware responses"""
        self.conversation_history.append({
            'user': user_input,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
