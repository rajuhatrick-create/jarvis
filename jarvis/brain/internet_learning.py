"""
Internet Learning - Automatically learns knowledge from the internet when on power.
Fetches facts from Wikipedia API and integrates them into JARVIS's learning memory.
Only runs when the laptop is connected to power to save battery.
"""

import json
import re
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    urllib = None

logger = logging.getLogger('JARVIS.brain.internet_learning')


@dataclass
class KnowledgeEntry:
    """A knowledge entry fetched from the internet"""
    topic: str
    summary: str
    source: str  # wikipedia, etc.
    category: str  # science, technology, history, geography, etc.
    fetched_at: str
    question_patterns: List[str]  # Generated question patterns for this knowledge


class WikipediaFetcher:
    """Fetch knowledge from Wikipedia API"""
    
    BASE_URL = "https://en.wikipedia.org/w/api.php"
    
    # Categories and their search topics
    TOPICS_BY_CATEGORY = {
        "science": [
            "physics", "chemistry", "biology", "astronomy", "geology",
            "quantum mechanics", "evolution", "DNA", "gravity", "light speed",
            "black hole", "neutron star", "photosynthesis", "mitochondria",
            "periodic table", "element", "atom", "molecule", "cell biology",
            "neuron", "brain", "human body", "immune system", "vaccine"
        ],
        "technology": [
            "artificial intelligence", "machine learning", "neural network",
            "blockchain", "cryptocurrency", "quantum computing", "robotics",
            "internet", "computer network", "operating system", "database",
            "algorithm", "data structure", "compiler", "programming language",
            "Python programming", "JavaScript", "Rust programming", "WebAssembly",
            "cloud computing", "cybersecurity", "encryption", "API"
        ],
        "history": [
            "ancient Egypt", "Roman Empire", "Middle Ages", "Renaissance",
            "Industrial Revolution", "World War", "Cold War", "French Revolution",
            "American Revolution", "Civil Rights Movement", "Moon landing",
            "Silk Road", "Viking", "Ming Dynasty", "Ottoman Empire",
            "Alexander the Great", "Julius Caesar", "Napoleon", "Gandhi",
            "Martin Luther King", "Marie Curie", "Albert Einstein"
        ],
        "geography": [
            "continent", "ocean", "mountain range", "river", "desert",
            "Amazon rainforest", "Sahara", "Himalayas", "Great Barrier Reef",
            "country capital", "population", "climate", "ecosystem",
            "biodiversity", "plate tectonics", "volcano", "earthquake",
            "tornado", "hurricane", "monsoon", "coral reef"
        ],
        "mathematics": [
            "algebra", "geometry", "calculus", "statistics", "probability",
            "prime number", "Fibonacci sequence", "Pi", "Euler number",
            "theorem", "proof", "matrix", "vector", "integral", "derivative",
            "fractal", "chaos theory", "game theory", "cryptography math"
        ],
        "general": [
            "democracy", "economics", "inflation", "supply and demand",
            "philosophy", "ethics", "logic", "rhetoric", "psychology",
            "sociology", "anthropology", "linguistics", "music theory",
            "art movement", "architecture", "literature", "mythology",
            "religion", "culture", "language family"
        ]
    }
    
    def __init__(self, config: Dict):
        self.config = config
        self.rate_limit_delay = config.get('rate_limit_delay', 2)  # Seconds between requests
        self.rate_limit_backoff = config.get('rate_limit_backoff', 10)  # Backoff on 429
        self.max_requests_per_session = config.get('max_requests_per_session', 20)
        self.requests_made = 0
        self.last_request_time = 0
        self.backoff_until = 0  # Timestamp until which we should back off
    
    def _rate_limit(self):
        """Enforce rate limiting between requests with backoff support"""
        # Check backoff first
        now = time.time()
        if now < self.backoff_until:
            wait_time = self.backoff_until - now
            time.sleep(wait_time)
        
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """Search Wikipedia for a query"""
        if urllib is None:
            logger.error("urllib not available")
            return []
        
        if self.requests_made >= self.max_requests_per_session:
            logger.info("Rate limit reached for this session")
            return []
        
        self._rate_limit()
        
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srlimit': limit,
            'format': 'json'
        }
        
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'JARVIS Learning Bot/1.0 (educational AI assistant)')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = []
                for page in data.get('query', {}).get('search', []):
                    results.append({
                        'title': page.get('title', ''),
                        'snippet': page.get('snippet', '').strip('...'),
                        'pageid': page.get('pageid', 0)
                    })
                self.requests_made += 1
                return results
        except urllib.error.HTTPError as e:
            if e.code == 429:
                logger.warning(f"Wikipedia rate limit (429) — backing off for {self.rate_limit_backoff}s")
                self.backoff_until = time.time() + self.rate_limit_backoff
                return []
            logger.error(f"Wikipedia search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    def get_summary(self, title: str, sentences: int = 3) -> Optional[str]:
        """Get a summary of a Wikipedia page. Uses search-first fallback if direct title lookup fails."""
        if urllib is None:
            return None
        
        if self.requests_made >= self.max_requests_per_session:
            return None
        
        self._rate_limit()
        
        # Try direct title lookup first
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
            'exsentences': sentences,
            'format': 'json'
        }
        
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'JARVIS Learning Bot/1.0 (educational AI assistant)')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                pages = data.get('query', {}).get('pages', {})
                for page_id, page_data in pages.items():
                    if 'extract' in page_data:
                        self.requests_made += 1
                        return page_data['extract']
        except urllib.error.HTTPError as e:
            if e.code == 429:
                logger.warning(f"Wikipedia rate limit (429) — backing off for {self.rate_limit_backoff}s")
                self.backoff_until = time.time() + self.rate_limit_backoff
                return None
            logger.error(f"Wikipedia summary error: {e}")
        except Exception as e:
            logger.error(f"Wikipedia summary error: {e}")
        
        # Fallback: search for the topic and get summary of first result
        if self.requests_made >= self.max_requests_per_session:
            return None
        
        search_results = self.search(title, limit=1)
        if search_results and search_results[0].get('title'):
            actual_title = search_results[0]['title']
            logger.info(f"Title '{title}' not found directly, using search result: '{actual_title}'")
            return self.get_summary_from_title(actual_title, sentences)
        
        return None
    
    def get_summary_from_title(self, title: str, sentences: int = 3) -> Optional[str]:
        """Get summary from an exact Wikipedia page title (used by fallback)."""
        if urllib is None:
            return None
        
        if self.requests_made >= self.max_requests_per_session:
            return None
        
        self._rate_limit()
        
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
            'exsentences': sentences,
            'format': 'json'
        }
        
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'JARVIS Learning Bot/1.0 (educational AI assistant)')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                pages = data.get('query', {}).get('pages', {})
                for page_id, page_data in pages.items():
                    if 'extract' in page_data:
                        self.requests_made += 1
                        return page_data['extract']
                return None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                logger.warning(f"Wikipedia rate limit (429) — backing off for {self.rate_limit_backoff}s")
                self.backoff_until = time.time() + self.rate_limit_backoff
                return None
            logger.error(f"Wikipedia summary error: {e}")
            return None
        except Exception as e:
            logger.error(f"Wikipedia summary error: {e}")
            return None


class InternetLearner:
    """Manages automatic learning from the internet when on power"""
    
    def __init__(self, config: Dict, learning_ai=None, power_monitor=None, sqlite_db=None):
        self.config = config.get('internet_learning', {})
        self.enabled = self.config.get('enabled', False)
        self.continuous_loop = self.config.get('continuous_loop', False)
        self.continuous_loop_interval = self.config.get('continuous_loop_interval', 60)
        self.categories = self.config.get('categories', list(WikipediaFetcher.TOPICS_BY_CATEGORY.keys()))
        self.learn_on_startup = self.config.get('learn_on_startup', True)
        self.learning_interval_hours = self.config.get('learning_interval_hours', 2)
        self.max_new_entries_per_session = self.config.get('max_new_entries_per_session', 20)
        
        self.learning_ai = learning_ai
        self.power_monitor = power_monitor
        self.fetcher = WikipediaFetcher(self.config)
        self.sqlite_db = sqlite_db
        
        # Track what we've already learned
        self.learned_topics: Set[str] = set()
        self.last_learning_time: Optional[datetime] = None
        self.is_learning = False
        self.stats = {
            'total_sessions': 0,
            'total_facts_learned': 0,
            'last_session_time': None,
            'last_session_facts': 0,
            'errors': 0
        }
        
        # Load learned topics from disk
        self._load_learned_topics()
        logger.info(f"InternetLearner initialized (enabled: {self.enabled}, learned_topics: {len(self.learned_topics)})")
    
    def _get_storage_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "data" / "learned_topics.json"
    
    def _load_learned_topics(self):
        """Load already learned topics from SQLite or disk"""
        # Try SQLite first
        if self.sqlite_db and self.sqlite_db.is_available():
            try:
                data = self.sqlite_db.load_internet_learning()
                self.learned_topics = set(data.get('topics', []))
                # Merge stats to preserve defaults
                loaded_stats = data.get('stats', {})
                for key in self.stats:
                    if key not in loaded_stats:
                        loaded_stats[key] = self.stats[key]
                self.stats = loaded_stats
                logger.info(f"Loaded {len(self.learned_topics)} previously learned topics from SQLite")
                return
            except Exception as e:
                logger.error(f"Error loading learned topics from SQLite: {e}")
        
        # Fallback to local disk
        path = self._get_storage_path()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.learned_topics = set(data.get('topics', []))
                    # Merge stats to preserve defaults
                    loaded_stats = data.get('stats', {})
                    for key in self.stats:
                        if key not in loaded_stats:
                            loaded_stats[key] = self.stats[key]
                    self.stats = loaded_stats
                    logger.info(f"Loaded {len(self.learned_topics)} previously learned topics")
            except Exception as e:
                logger.error(f"Error loading learned topics: {e}")
    
    def _save_learned_topics(self):
        """Save learned topics to SQLite or disk"""
        # Build topics_data from learning AI memory
        topics_data = {}
        if self.learning_ai:
            for mem_id, entry in self.learning_ai.memory.items():
                if entry.category and entry.category.startswith('internet_'):
                    # Extract topic name from category
                    topic = entry.response[:50].lower().replace(' ', '_')
                    topics_data[topic] = {
                        'summary': entry.response,
                        'category': entry.category.replace('internet_', ''),
                        'learned_at': entry.created_at
                    }
        
        data = {
            'topics': list(self.learned_topics),
            'stats': self.stats,
            'topics_data': topics_data
        }
        
        # Try SQLite first
        if self.sqlite_db and self.sqlite_db.is_available():
            try:
                self.sqlite_db.save_internet_learning(data)
                return
            except Exception as e:
                logger.error(f"Error saving learned topics to SQLite: {e}")
        
        # Fallback to local disk
        path = self._get_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving learned topics: {e}")
    
    def _can_learn(self) -> Tuple[bool, str]:
        """Check if learning can proceed"""
        if not self.enabled:
            return False, "Internet learning is disabled"
        
        # Cloud mode: no power monitor, always allow learning
        if self.power_monitor is not None:
            if not self.power_monitor.is_on_power():
                return False, "Not on power — learning paused to save battery"
        
        if self.is_learning:
            return False, "Already learning"
        
        # In continuous loop mode, skip the cooldown check
        if not self.continuous_loop:
            # Check if enough time has passed since last learning
            if self.last_learning_time:
                elapsed = (datetime.now() - self.last_learning_time).total_seconds() / 3600
                if elapsed < self.learning_interval_hours:
                    remaining = self.learning_interval_hours - elapsed
                    return False, f"Learning cooldown: {remaining:.1f}h remaining"
        
        return True, "Ready to learn"
    
    def _generate_question_patterns(self, topic: str, summary: str) -> List[str]:
        """Generate question patterns for a knowledge entry"""
        patterns = []
        
        # Basic question forms
        patterns.append(f"what is {topic}")
        patterns.append(f"tell me about {topic}")
        patterns.append(f"explain {topic}")
        patterns.append(f"{topic}")
        
        # Extract key terms from the topic
        terms = topic.lower().split()
        for term in terms:
            if len(term) > 3:  # Skip short words
                patterns.append(f"what is {term}")
                patterns.append(f"tell me about {term}")
        
        # Generate variations
        patterns.append(f"jarvis what is {topic}")
        patterns.append(f"jarvis explain {topic}")
        
        return list(set(patterns))
    
    def _filter_content(self, text: str) -> bool:
        """Filter inappropriate or irrelevant content"""
        # Simple content filter
        inappropriate = ['violence', 'hate', 'explicit', 'adult']
        text_lower = text.lower()
        return not any(word in text_lower for word in inappropriate)
    
    async def learn_session(self) -> Dict:
        """Run a learning session — fetch new knowledge from Wikipedia"""
        can_learn, reason = self._can_learn()
        if not can_learn:
            logger.info(f"Learning skipped: {reason}")
            return {'status': 'skipped', 'reason': reason}
        
        self.is_learning = True
        facts_learned = 0
        errors = 0
        
        try:
            self.last_learning_time = datetime.now()
            self.stats['total_sessions'] += 1
            self.fetcher.requests_made = 0  # Reset rate limit counter
            
            logger.info("Starting internet learning session...")
            
            # Get topics to learn from enabled categories
            topics_to_learn = []
            for category in self.categories:
                if category in WikipediaFetcher.TOPICS_BY_CATEGORY:
                    topics = WikipediaFetcher.TOPICS_BY_CATEGORY[category]
                    # Filter out already learned topics
                    new_topics = [t for t in topics if t.lower() not in self.learned_topics]
                    for topic in new_topics:
                        topics_to_learn.append((topic, category))
            
            logger.info(f"Found {len(topics_to_learn)} new topics to learn")
            
            # Learn from topics
            for topic, category in topics_to_learn:
                if facts_learned >= self.max_new_entries_per_session:
                    logger.info(f"Reached max new entries per session ({self.max_new_entries_per_session})")
                    break
                
                # Get summary from Wikipedia
                summary = self.fetcher.get_summary(topic, sentences=4)
                if not summary:
                    errors += 1
                    continue
                
                # Filter content
                if not self._filter_content(summary):
                    logger.info(f"Filtered inappropriate content for: {topic}")
                    continue
                
                # Generate question patterns
                patterns = self._generate_question_patterns(topic, summary)
                
                # Add to learning AI memory
                if self.learning_ai:
                    response = f"{topic}: {summary}"
                    self.learning_ai.learn(
                        patterns=patterns,
                        response=response,
                        category=f"internet_{category}"
                    )
                    facts_learned += 1
                    self.learned_topics.add(topic.lower())
                    logger.info(f"Learned: {topic} ({category})")
                
                # Small delay between topics
                await asyncio.sleep(0.5)
            
            # Update stats
            self.stats['total_facts_learned'] += facts_learned
            self.stats['last_session_time'] = datetime.now().isoformat()
            self.stats['last_session_facts'] = facts_learned
            self.stats['errors'] += errors
            
            # Save learned topics
            self._save_learned_topics()
            
            logger.info(f"Learning session complete: {facts_learned} facts learned, {errors} errors")
            
            return {
                'status': 'success',
                'facts_learned': facts_learned,
                'errors': errors,
                'total_known': len(self.learned_topics)
            }
            
        except Exception as e:
            logger.error(f"Learning session error: {e}")
            self.stats['errors'] += 1
            return {'status': 'error', 'error': str(e)}
        finally:
            self.is_learning = False
    
    def get_status(self) -> Dict:
        """Get current learning status"""
        can_learn, reason = self._can_learn()
        
        # Determine display status
        if not self.enabled:
            status = "disabled"
        elif self.is_learning:
            status = "learning"
        elif self.power_monitor is not None and not self.power_monitor.is_on_power():
            status = "paused (on battery)"
        elif can_learn:
            status = "active (continuous loop)" if self.continuous_loop else "ready"
        else:
            status = reason
        
        return {
            'enabled': self.enabled,
            'continuous_loop': self.continuous_loop,
            'is_learning': self.is_learning,
            'can_learn': can_learn,
            'reason': reason,
            'status': status,
            'learned_topics': len(self.learned_topics),
            'learned_topics_list': list(self.learned_topics),
            'categories': self.categories,
            'last_learning': self.last_learning_time.isoformat() if self.last_learning_time else None,
            'stats': self.stats
        }
    
    def get_known_topics(self, category: Optional[str] = None) -> List[str]:
        """Get list of known topics, optionally filtered by category"""
        topics = list(self.learned_topics)
        if category:
            # Filter by checking prefix in learning AI memory
            pass
        return sorted(topics)
