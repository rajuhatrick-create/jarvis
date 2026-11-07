"""
Local AI Learning Engine - Learns from local files, conversations, and user interactions.
Builds a personal knowledge base completely offline, improving JARVIS's understanding over time.

Features:
- Scans local files (documents, notes, code) for personal knowledge
- Learns from conversation context and patterns
- Builds word association networks (local thesaurus)
- Remembers user preferences and habits
- Extracts entities (names, places, projects) from interactions
- Generates smart response variations
"""

import json
import re
import os
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from collections import Counter, defaultdict
import math

logger = logging.getLogger('JARVIS.brain.local_learning')


# Common English stop words to filter out
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'because', 'but', 'and', 'or', 'if', 'while', 'about', 'what', 'which',
    'who', 'whom', 'this', 'that', 'these', 'those', 'i', 'me', 'my',
    'myself', 'we', 'our', 'ours', 'you', 'your', 'yours', 'he', 'him',
    'his', 'it', 'its', 'she', 'her', 'they', 'them', 'their', 'also',
    'get', 'go', 'make', 'like', 'know', 'take', 'see', 'come', 'think',
    'look', 'want', 'give', 'use', 'find', 'tell', 'ask', 'work', 'seem',
    'feel', 'try', 'leave', 'call', 'turn', 'start', 'show', 'help',
    'put', 'mean', 'keep', 'let', 'begin', 'seem', 'should', 'one',
}


@dataclass
class WordAssociation:
    """Represents a word and its associated words with weights"""
    word: str
    associations: Dict[str, float] = field(default_factory=dict)  # word -> weight
    category: str = "general"  # name, place, project, tech, concept, etc.


@dataclass
class Entity:
    """An extracted entity (person, place, project, etc.)"""
    name: str
    entity_type: str  # person, place, project, company, file, concept
    context: str = ""  # Where/how it was mentioned
    mentions: int = 1
    first_seen: str = ""
    last_seen: str = ""
    related_entities: List[str] = field(default_factory=list)


@dataclass
class UserPreference:
    """A learned user preference or habit"""
    key: str
    value: str
    confidence: float = 1.0  # How confident we are about this preference
    times_used: int = 0
    category: str = "general"  # app, time, file, command, schedule


@dataclass
class ConversationPattern:
    """A pattern learned from conversations"""
    pattern: str  # The input pattern
    response: str  # The response given
    success_count: int = 0
    failure_count: int = 0
    variations: List[str] = field(default_factory=list)
    learned_at: str = ""


class WordNetwork:
    """Builds a network of word associations for semantic understanding"""
    
    def __init__(self):
        self.network: Dict[str, WordAssociation] = {}
        self.co_occurrence: Dict[str, Counter] = defaultdict(Counter)
    
    def add_association(self, word1: str, word2: str, weight: float = 1.0):
        """Add an association between two words"""
        if word1 not in self.network:
            self.network[word1] = WordAssociation(word=word1)
        if word2 not in self.network:
            self.network[word2] = WordAssociation(word=word2)
        
        # Update associations
        self.network[word1].associations[word2] = self.network[word1].associations.get(word2, 0) + weight
        self.network[word2].associations[word1] = self.network[word2].associations.get(word1, 0) + weight
        
        # Track co-occurrence
        self.co_occurrence[word1][word2] += 1
        self.co_occurrence[word2][word1] += 1
    
    def add_sentence(self, sentence: str, category: str = "general"):
        """Extract word associations from a sentence"""
        words = self._extract_keywords(sentence)
        
        # Associate consecutive keywords
        for i in range(len(words) - 1):
            self.add_association(words[i], words[i + 1], weight=2.0)
        
        # Associate all keywords in the sentence (weaker weight)
        for i in range(len(words)):
            for j in range(i + 2, len(words)):
                self.add_association(words[i], words[j], weight=0.5)
        
        # Set category for keywords
        for word in words:
            if word in self.network:
                self.network[word].category = category
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in STOP_WORDS]
    
    def get_associations(self, word: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top associations for a word"""
        if word not in self.network:
            return []
        
        associations = self.network[word].associations
        sorted_assocs = sorted(associations.items(), key=lambda x: x[1], reverse=True)
        return sorted_assocs[:limit]
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity based on word associations"""
        keywords1 = set(self._extract_keywords(text1))
        keywords2 = set(self._extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Count overlapping keywords
        direct_overlap = len(keywords1 & keywords2)
        
        # Count associated keywords (one word in text1 is associated with a word in text2)
        associated_overlap = 0
        for k1 in keywords1:
            if k1 in self.network:
                for assoc_word in self.network[k1].associations:
                    if assoc_word in keywords2:
                        associated_overlap += 0.5  # Partial credit for associations
        
        total_keywords = len(keywords1 | keywords2)
        similarity = (direct_overlap + associated_overlap) / total_keywords
        return min(1.0, similarity)
    
    def expand_query(self, query: str, max_expansions: int = 5) -> List[str]:
        """Expand a query with associated words for better matching"""
        keywords = self._extract_keywords(query)
        expanded_terms = set(keywords)
        
        for keyword in keywords:
            associations = self.get_associations(keyword, limit=3)
            for assoc_word, weight in associations:
                if weight > 1.0:  # Only strong associations
                    expanded_terms.add(assoc_word)
        
        # Generate expanded queries
        expansions = [query]
        extra_terms = list(expanded_terms - set(keywords))[:max_expansions]
        if extra_terms:
            expansions.append(f"{query} {' '.join(extra_terms)}")
        
        return expansions


class EntityExtractor:
    """Extracts and tracks entities (people, places, projects) from interactions"""
    
    # Phrases that should NOT trigger entity extraction (commands, questions, etc.)
    EXCLUDED_PHRASES = [
        r'^\s*who\s+is\b',
        r'^\s*who\s+are\b',
        r'^\s*what\s+is\b',
        r'^\s*what\s+are\b',
        r'^\s*what\s+does\b',
        r'^\s*what\s+do\b',
        r'^\s*teach\s+me\b',
        r'^\s*remember\s+that\b',
        r'^\s*explain\s+',
        r'^\s*tell\s+me\s+about\b',
        r'^\s*help\b',
        r'^\s*date\b',
        r'^\s*time\b',
        r'^\s*system\s+',
        r'^\s*open\s+',
        r'^\s*close\s+',
        r'^\s*search\s+',
        r'^\s*volume\s+',
        r'^\s*joke\b',
        r'^\s*learn\b',
        r'^\s*scan\s+',
    ]
    
    # Patterns for entity extraction
    PATTERNS = {
        'person': [
            r'(?:my|a|the)\s+(?:friend|colleague|boss|teacher|mentor|partner|wife|husband|son|daughter|brother|sister|parent|sister|cousin|uncle|aunt|nephew|niece)\s+(?:named|called|is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:my|a|the)\s+(?:friend|colleague|boss|teacher|mentor|partner|wife|husband|son|daughter|brother|sister|parent|sister|cousin|uncle|aunt|nephew|niece)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|was)\s+(?:my|a|the)',
            r'(?:my|a|the)\s+(?:friend|colleague|boss|teacher|mentor|partner|wife|husband|son|daughter|brother|sister|parent|sister|cousin|uncle|aunt|nephew|niece)\s+(?:named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ],
        'project': [
            r'(?:my|the)\s+(?:project|app|application|software|game)\s+(?:named|called|is)\s+([A-Za-z][A-Za-z0-9_ -]{2,})',
            r'I\s+(?:am|was|worked)\s+(?:on|building|creating|developing)\s+(?:a|an|the)\s+(?:project\s+called\s+|app\s+called\s+)?([A-Za-z][A-Za-z0-9_ -]{2,})',
        ],
        'company': [
            r'(?:I\s+(?:work|worked)|my\s+company)\s+(?:at|is|named|called)?\s*([A-Z][A-Za-z &]+(?:\s+(?:Inc|LLC|Ltd|Corp|Co))?)',
            r'(?:the\s+company|company)\s+([A-Z][A-Za-z &]+(?:\s+(?:Inc|LLC|Ltd|Corp|Co))?)',
        ],
        'place': [
            r'(?:I\s+(?:live|lived|work|worked|study|studied)|my\s+(?:home|house|office|city))\s+(?:in|at|is)?\s*([A-Z][A-Za-z &]+(?:\s+[A-Z][A-Za-z &]+)*)',
            r'(?:lives|lived|works|worked)\s+(?:in|at)\s+([A-Z][A-Za-z &]+(?:\s+[A-Z][A-Za-z &]+)*)',
        ],
        'concept': [
            r'(?:I\s+(?:like|love|enjoy|prefer|am\s+interested\s+in|am\s+good\s+at))\s+([A-Za-z][A-Za-z0-9 &]+(?:\s+[A-Za-z][A-Za-z0-9 &]+)*)',
        ]
    }
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
    
    def _is_command_or_question(self, text: str) -> bool:
        """Check if text is a command or question that should not be scanned for entities"""
        text_stripped = text.strip()
        for excluded in self.EXCLUDED_PHRASES:
            if re.search(excluded, text_stripped, re.IGNORECASE):
                return True
        return False
    
    def _clean_entity_name(self, name: str) -> str:
        """Clean extracted entity name by removing context words"""
        # Remove common context words that often get captured
        context_words = [
            'named', 'called', 'is', 'was', 'are', 'were',
            'project', 'called', 'the', 'a', 'an',
            'in', 'at', 'on', 'of', 'and', 'with',
            'makes', 'make', 'do', 'does',
        ]
        words = name.split()
        cleaned = [w for w in words if w.lower() not in context_words]
        if cleaned:
            return ' '.join(cleaned)
        return name
    
    def extract_from_text(self, text: str) -> List[Entity]:
        """Extract entities from text"""
        found_entities = []
        
        # Skip commands and questions - don't extract entities from them
        if self._is_command_or_question(text):
            return found_entities
        
        for entity_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1).strip()
                    # Clean the entity name
                    name = self._clean_entity_name(name)
                    if len(name) > 1:
                        entity = self._add_entity(name, entity_type, text)
                        found_entities.append(entity)
        
        return found_entities
    
    def _add_entity(self, name: str, entity_type: str, context: str) -> Entity:
        """Add or update an entity"""
        now = datetime.now().isoformat()
        key = name.lower()
        
        if key in self.entities:
            entity = self.entities[key]
            entity.mentions += 1
            entity.last_seen = now
            # Update context if new
            if context not in entity.context:
                entity.context = f"{entity.context} | {context}"[:500]
        else:
            entity = Entity(
                name=name,
                entity_type=entity_type,
                context=context[:200],
                first_seen=now,
                last_seen=now
            )
            self.entities[key] = entity
        
        return entity
    
    def get_entity(self, name: str) -> Optional[Entity]:
        """Get an entity by name (case-insensitive)"""
        return self.entities.get(name.lower())
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type"""
        return [e for e in self.entities.values() if e.entity_type == entity_type]
    
    def search_entities(self, query: str) -> List[Entity]:
        """Search entities by name or context"""
        query_lower = query.lower()
        results = []
        for entity in self.entities.values():
            if query_lower in entity.name.lower() or query_lower in entity.context.lower():
                results.append(entity)
        return results


class LocalFileLearner:
    """Learns from local files on the system"""
    
    # File types to scan
    TEXT_EXTENSIONS = {'.txt', '.md', '.rst', '.log', '.csv', '.json', '.yaml', '.yml'}
    CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.kt', '.cpp', '.c', '.h', '.go', '.rs', '.rb'}
    DOC_EXTENSIONS = {'.html', '.xml', '.cfg', '.ini', '.conf'}
    
    def __init__(self, config: Dict):
        self.config = config.get('local_learning', {}).get('file_scanner', {})
        # scan_directories is at local_learning.scan_directories, not under file_scanner
        self.scan_directories = config.get('local_learning', {}).get('scan_directories', [])
        if not self.scan_directories:
            self.scan_directories = self.config.get('scan_directories', [])
        self.max_file_size = self.config.get('max_file_size_kb', 500) * 1024
        self.max_files_per_scan = self.config.get('max_files_per_scan', 100)
        self.scanned_files: Dict[str, datetime] = {}  # file_hash -> last_scan_time
        self.extracted_knowledge: List[Dict] = []
    
    def scan_directory(self, directory: str, learning_ai=None) -> Dict:
        """Scan a directory for learnable content"""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return {'status': 'error', 'message': f'Directory not found: {directory}'}
        
        files_scanned = 0
        knowledge_extracted = 0
        errors = 0
        
        try:
            # Walk directory
            for file_path in dir_path.rglob('*'):
                if files_scanned >= self.max_files_per_scan:
                    break
                
                if not file_path.is_file():
                    continue
                
                # Check extension
                if file_path.suffix.lower() not in self.TEXT_EXTENSIONS | self.CODE_EXTENSIONS:
                    continue
                
                # Check file size
                if file_path.stat().st_size > self.max_file_size:
                    continue
                
                # Check if recently scanned
                file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
                if file_hash in self.scanned_files:
                    last_scan = self.scanned_files[file_hash]
                    if (datetime.now() - last_scan).total_seconds() < 3600:  # 1 hour cooldown
                        continue
                
                # Try to read and extract knowledge
                try:
                    knowledge = self._extract_knowledge_from_file(file_path)
                    if knowledge and learning_ai:
                        self._add_knowledge_to_learning(knowledge, learning_ai)
                        knowledge_extracted += 1
                    
                    self.scanned_files[file_hash] = datetime.now()
                    files_scanned += 1
                except Exception as e:
                    logger.debug(f"Error reading {file_path}: {e}")
                    errors += 1
        
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")
            errors += 1
        
        return {
            'status': 'completed',
            'files_scanned': files_scanned,
            'knowledge_extracted': knowledge_extracted,
            'errors': errors
        }
    
    def _extract_knowledge_from_file(self, file_path: Path) -> Optional[Dict]:
        """Extract knowledge from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # Read first 10KB
            
            if not content.strip():
                return None
            
            # Extract meaningful content
            lines = content.strip().split('\n')
            meaningful_lines = [l.strip() for l in lines if len(l.strip()) > 10]
            
            if not meaningful_lines:
                return None
            
            # Determine file type
            is_code = file_path.suffix.lower() in self.CODE_EXTENSIONS
            
            knowledge = {
                'source': str(file_path),
                'file_name': file_path.name,
                'is_code': is_code,
                'content_preview': content[:500],
                'key_phrases': self._extract_key_phrases(meaningful_lines),
                'definitions': self._extract_definitions(meaningful_lines) if not is_code else [],
            }
            
            return knowledge
        
        except Exception as e:
            logger.debug(f"Error extracting knowledge from {file_path}: {e}")
            return None
    
    def _extract_key_phrases(self, lines: List[str]) -> List[str]:
        """Extract key phrases from lines"""
        phrases = []
        for line in lines[:50]:  # First 50 lines
            # Look for definitions, assignments, comments
            if ':=' in line or ' = ' in line or '#' in line or '//' in line:
                # Extract the phrase
                phrase = re.sub(r'[=:#/\s]+', ' ', line).strip()
                if len(phrase) > 5 and len(phrase) < 200:
                    phrases.append(phrase)
        return phrases[:20]
    
    def _extract_definitions(self, lines: List[str]) -> List[Tuple[str, str]]:
        """Extract definition-like patterns (X is Y, X means Y)"""
        definitions = []
        patterns = [
            r'(.+?)\s+(?:is|means|refers\s+to|defined\s+as)\s+(.+)',
            r'(.+?)\s*[:=]\s*(.+)',
        ]
        
        for line in lines:
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    term = match.group(1).strip()
                    definition = match.group(2).strip()
                    if 3 < len(term) < 100 and 10 < len(definition) < 500:
                        definitions.append((term, definition))
        
        return definitions[:10]
    
    def _add_knowledge_to_learning(self, knowledge: Dict, learning_ai):
        """Add extracted knowledge to the learning AI"""
        # Add key phrases as patterns
        for phrase in knowledge.get('key_phrases', []):
            patterns = [
                phrase.lower(),
                f"what is {phrase}",
                f"tell me about {phrase}",
            ]
            learning_ai.learn(
                patterns=patterns,
                response=f"Found in {knowledge['file_name']}: {knowledge['content_preview'][:200]}",
                category="local_file"
            )
        
        # Add definitions
        for term, definition in knowledge.get('definitions', []):
            learning_ai.add_fact(term, definition)


class PreferenceLearner:
    """Learns user preferences and habits from interactions"""
    
    def __init__(self):
        self.preferences: Dict[str, UserPreference] = {}
        self.command_history: List[Dict] = []
        self.time_patterns: Counter = Counter()  # hour -> command_type
    
    def record_interaction(self, user_input: str, response: str, was_successful: bool):
        """Record an interaction to learn preferences"""
        now = datetime.now()
        
        # Track time-based patterns
        self.time_patterns[now.hour] += 1
        
        # Record command in history
        self.command_history.append({
            'input': user_input,
            'response': response,
            'timestamp': now.isoformat(),
            'success': was_successful
        })
        
        # Keep only recent history
        if len(self.command_history) > 500:
            self.command_history = self.command_history[-500:]
        
        # Extract preferences
        self._extract_preferences(user_input, was_successful)
    
    def _extract_preferences(self, user_input: str, was_successful: bool):
        """Extract preferences from user input"""
        input_lower = user_input.lower()
        
        # App preferences
        app_patterns = [
            (r'(?:open|launch|start)\s+(\w+)', 'app'),
            (r'I\s+(?:like|prefer|use)\s+(\w+)', 'app'),
        ]
        
        for pattern, category in app_patterns:
            match = re.search(pattern, input_lower)
            if match:
                app_name = match.group(1)
                self._update_preference(f"favorite_{category}", app_name, was_successful)
        
        # Time preferences
        if 'morning' in input_lower or 'good morning' in input_lower:
            self._update_preference("active_time", "morning", True)
        elif 'evening' in input_lower or 'good evening' in input_lower:
            self._update_preference("active_time", "evening", True)
        
        # File location preferences
        file_match = re.search(r'(?:open|go\s+to|show)\s+(?:my\s+)?(\w+)\s+(?:folder|directory|files)', input_lower)
        if file_match:
            folder = file_match.group(1)
            self._update_preference("favorite_folder", folder, was_successful)
    
    def _update_preference(self, key: str, value: str, confidence_boost: bool):
        """Update a preference"""
        if key not in self.preferences:
            self.preferences[key] = UserPreference(key=key, value=value)
        
        pref = self.preferences[key]
        if pref.value == value:
            pref.times_used += 1
            pref.confidence = min(1.0, pref.confidence + (0.1 if confidence_boost else 0))
        else:
            # New value, adjust confidence
            pref.confidence = max(0.1, pref.confidence - 0.2)
    
    def get_preference(self, key: str) -> Optional[str]:
        """Get a preference value"""
        if key in self.preferences:
            return self.preferences[key].value
        return None
    
    def get_top_commands_by_time(self, hour: int) -> List[str]:
        """Get most common commands for a specific hour"""
        hour_commands = [
            h['input'] for h in self.command_history
            if datetime.fromisoformat(h['timestamp']).hour == hour
        ]
        return [item for item, _ in Counter(hour_commands).most_common(5)]
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        if not self.command_history:
            return {'total_interactions': 0}
        
        # Time distribution
        hours = [datetime.fromisoformat(h['timestamp']).hour for h in self.command_history]
        hour_dist = Counter(hours)
        
        # Success rate
        successes = sum(1 for h in self.command_history if h['success'])
        total = len(self.command_history)
        
        return {
            'total_interactions': total,
            'success_rate': successes / total if total > 0 else 0,
            'peak_hours': [h for h, _ in hour_dist.most_common(3)],
            'preferences_count': len(self.preferences)
        }


class LocalLearningAI:
    """Main local AI learning engine that coordinates all learning components"""
    
    def __init__(self, config: Dict, learning_ai=None, sqlite_db=None):
        self.config = config.get('local_learning', {})
        self.enabled = self.config.get('enabled', True)
        self.auto_scan = self.config.get('auto_scan', False)
        self.scan_interval_hours = self.config.get('scan_interval_hours', 24)
        
        # Core components
        self.learning_ai = learning_ai  # Reference to existing LearningAI
        self.word_network = WordNetwork()
        self.entity_extractor = EntityExtractor()
        self.file_learner = LocalFileLearner(config)
        self.preference_learner = PreferenceLearner()
        self.sqlite_db = sqlite_db
        
        # Learning stats
        self.stats = {
            'total_interactions_learned': 0,
            'total_entities_extracted': 0,
            'total_files_scanned': 0,
            'total_knowledge_entries': 0,
            'last_scan_time': None,
        }
        
        # Load saved state
        self._load_state()
        logger.info(f"LocalLearningAI initialized (enabled: {self.enabled})")
    
    def _get_storage_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "data" / "local_learning.json"
    
    def _load_state(self):
        """Load saved learning state from SQLite or disk"""
        # Try SQLite first
        if self.sqlite_db and self.sqlite_db.is_available():
            try:
                data = self.sqlite_db.load_local_learning()
                loaded_stats = data.get('stats', {})
                # Merge with defaults to ensure all keys exist
                for key, value in self.stats.items():
                    if key not in loaded_stats:
                        loaded_stats[key] = value
                self.stats = loaded_stats
                
                # Restore word network
                for word, assoc_data in data.get('word_network', {}).items():
                    wa = WordAssociation(
                        word=word,
                        associations=assoc_data.get('associations', {}),
                        category=assoc_data.get('category', 'general')
                    )
                    self.word_network.network[word] = wa
                
                # Restore entities
                for key, entity_data in data.get('entities', {}).items():
                    self.entity_extractor.entities[key] = Entity(**entity_data)
                
                # Restore preferences
                for key, pref_data in data.get('preferences', {}).items():
                    self.preference_learner.preferences[key] = UserPreference(**pref_data)
                
                logger.info(f"Loaded local learning state from SQLite: {len(self.word_network.network)} words, "
                          f"{len(self.entity_extractor.entities)} entities")
                return
            except Exception as e:
                logger.error(f"Error loading local learning state from SQLite: {e}")
        
        # Fallback to local disk
        path = self._get_storage_path()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    loaded_stats = data.get('stats', {})
                    # Merge with defaults to ensure all keys exist
                    for key, value in self.stats.items():
                        if key not in loaded_stats:
                            loaded_stats[key] = value
                    self.stats = loaded_stats
                    
                    # Restore word network
                    for word, assoc_data in data.get('word_network', {}).items():
                        wa = WordAssociation(
                            word=word,
                            associations=assoc_data.get('associations', {}),
                            category=assoc_data.get('category', 'general')
                        )
                        self.word_network.network[word] = wa
                    
                    # Restore entities
                    for key, entity_data in data.get('entities', {}).items():
                        self.entity_extractor.entities[key] = Entity(**entity_data)
                    
                    # Restore preferences
                    for key, pref_data in data.get('preferences', {}).items():
                        self.preference_learner.preferences[key] = UserPreference(**pref_data)
                    
                    logger.info(f"Loaded local learning state: {len(self.word_network.network)} words, "
                              f"{len(self.entity_extractor.entities)} entities")
            except Exception as e:
                logger.error(f"Error loading local learning state: {e}")
    
    def _save_state(self):
        """Save learning state to SQLite or disk"""
        data = {
            'stats': self.stats,
            'word_network': {
                word: {
                    'associations': wa.associations,
                    'category': wa.category
                }
                for word, wa in self.word_network.network.items()
            },
            'entities': {
                key: asdict(entity)
                for key, entity in self.entity_extractor.entities.items()
            },
            'preferences': {
                key: asdict(pref)
                for key, pref in self.preference_learner.preferences.items()
            }
        }
        
        # Try SQLite first
        if self.sqlite_db and self.sqlite_db.is_available():
            try:
                self.sqlite_db.save_local_learning(data)
                return
            except Exception as e:
                logger.error(f"Error saving local learning state to SQLite: {e}")
        
        # Fallback to local disk
        path = self._get_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving local learning state: {e}")
    
    def process_interaction(self, user_input: str, response: str, was_successful: bool = True):
        """Process an interaction to learn from it"""
        if not self.enabled:
            return
        
        # 1. Build word network from conversation
        self.word_network.add_sentence(user_input)
        if was_successful and response:
            self.word_network.add_sentence(response)
        
        # 2. Extract entities
        entities = self.entity_extractor.extract_from_text(user_input)
        if entities:
            self.stats['total_entities_extracted'] += len(entities)
            logger.info(f"Extracted entities: {[e.name for e in entities]}")
        
        # 3. Learn preferences
        self.preference_learner.record_interaction(user_input, response, was_successful)
        
        # 4. If we have the base learning AI, enhance it with semantic understanding
        if self.learning_ai and was_successful:
            # Add semantic associations to learning AI
            keywords = self.word_network._extract_keywords(user_input)
            if keywords and response:
                # Create semantic variations for better matching
                for keyword in keywords[:3]:  # Top 3 keywords
                    associations = self.word_network.get_associations(keyword, limit=2)
                    for assoc_word, _ in associations:
                        # Add the association as a pattern variation
                        variation = user_input.replace(keyword, assoc_word, 1)
                        if variation.lower() != user_input.lower():
                            self.learning_ai.update_conversation_history(variation, response)
        
        self.stats['total_interactions_learned'] += 1
        
        # Periodically save state
        if self.stats['total_interactions_learned'] % 10 == 0:
            self._save_state()
    
    def scan_local_files(self, directory: Optional[str] = None) -> Dict:
        """Scan local files for knowledge"""
        directories = [directory] if directory else self.file_learner.scan_directories
        
        if not directories:
            return {'status': 'error', 'message': 'No directories configured for scanning'}
        
        total_results = {'files_scanned': 0, 'knowledge_extracted': 0, 'errors': 0}
        
        for directory in directories:
            result = self.file_learner.scan_directory(directory, self.learning_ai)
            if result['status'] == 'completed':
                total_results['files_scanned'] += result['files_scanned']
                total_results['knowledge_extracted'] += result['knowledge_extracted']
                total_results['errors'] += result['errors']
        
        self.stats['total_files_scanned'] += total_results['files_scanned']
        self.stats['last_scan_time'] = datetime.now().isoformat()
        self._save_state()
        
        total_results['status'] = 'completed'
        return total_results
    
    def answer_with_context(self, query: str) -> Optional[str]:
        """Try to answer using local knowledge and context"""
        if not self.enabled:
            return None
        
        # 1. Check entities first
        entities = self.entity_extractor.search_entities(query)
        if entities:
            entity = entities[0]
            return f"I know about {entity.name} ({entity.entity_type}). {entity.context}"
        
        # 2. Check preferences
        if 'prefer' in query.lower() or 'favorite' in query.lower():
            for key, pref in self.preference_learner.preferences.items():
                if key.replace('favorite_', '') in query.lower():
                    return f"Based on our conversations, you seem to prefer {pref.value}."
        
        # 3. Use word network for semantic matching
        expanded_queries = self.word_network.expand_query(query)
        if self.learning_ai:
            for expanded_query in expanded_queries[1:]:  # Skip original, already tried
                match = self.learning_ai.find_match(expanded_query)
                if match:
                    entry, score = match
                    return entry.response
        
        return None
    
    def get_learning_summary(self) -> Dict:
        """Get a summary of what JARVIS has learned locally"""
        return {
            'enabled': self.enabled,
            'stats': self.stats,
            'scan_directories': self.file_learner.scan_directories,
            'word_network_size': len(self.word_network.network),
            'entity_count': len(self.entity_extractor.entities),
            'preference_count': len(self.preference_learner.preferences),
            'entities': {
                'people': len(self.entity_extractor.get_entities_by_type('person')),
                'projects': len(self.entity_extractor.get_entities_by_type('project')),
                'companies': len(self.entity_extractor.get_entities_by_type('company')),
                'places': len(self.entity_extractor.get_entities_by_type('place')),
                'concepts': len(self.entity_extractor.get_entities_by_type('concept')),
            },
            'usage_stats': self.preference_learner.get_usage_stats(),
        }
    
    def get_entity_info(self, name: str) -> Optional[Dict]:
        """Get information about a known entity"""
        entity = self.entity_extractor.get_entity(name)
        if entity:
            return asdict(entity)
        return None
