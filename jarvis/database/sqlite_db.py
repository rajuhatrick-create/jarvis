"""
SQLite Database Layer - Local file-based database for cloud deployment.
Replaces Firebase Firestore with SQLite for zero-setup cloud storage.
"""

import json
import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger('JARVIS.database.sqlite')


class SQLiteDB:
    """SQLite database wrapper for JARVIS memory storage"""
    
    def __init__(self, config: dict):
        self.config = config.get('database', {})
        self.enabled = self.config.get('enabled', True)
        self.db_path = self.config.get('path', str(Path(__file__).parent.parent.parent / "data" / "jarvis.db"))
        self.conn = None
        self._lock = threading.Lock()
        
        if self.enabled:
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database and create tables"""
        try:
            # Ensure data directory exists
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            self.enabled = False
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                patterns TEXT NOT NULL,
                response TEXT NOT NULL,
                intent TEXT DEFAULT '',
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_used TEXT,
                category TEXT DEFAULT 'fact',
                updated_at TEXT
            )
        ''')
        
        # Local learning table (key-value store for word_network, entities, preferences)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS local_learning (
                type TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        ''')
        
        # Learned topics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_topics (
                topic TEXT PRIMARY KEY,
                summary TEXT,
                category TEXT,
                learned_at TEXT
            )
        ''')
        
        # Meta table for stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        logger.info("Database tables created successfully")
    
    def is_available(self) -> bool:
        """Check if SQLite is available and initialized"""
        return self.enabled and self.conn is not None
    
    # ==================== Memory Collection ====================
    
    def save_memory(self, data: dict):
        """Save all memories to SQLite
        
        Args:
            data: Dict with 'memories' list and 'stats' dict
        """
        if not self.is_available():
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                memories = data.get('memories', [])
                
                # Upsert memories
                for mem in memories:
                    cursor.execute('''
                        INSERT OR REPLACE INTO memories 
                        (id, patterns, response, intent, success_count, failure_count, created_at, last_used, category, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        mem['id'],
                        json.dumps(mem['patterns']),
                        mem['response'],
                        mem.get('intent', ''),
                        mem.get('success_count', 0),
                        mem.get('failure_count', 0),
                        mem['created_at'],
                        mem.get('last_used'),
                        mem.get('category', 'fact'),
                        datetime.now().isoformat()
                    ))
                
                # Save stats
                stats = data.get('stats', {})
                if stats:
                    cursor.execute('INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)',
                                  ('learning_stats', json.dumps(stats)))
                
                self.conn.commit()
                logger.info(f"Saved {len(memories)} memories to SQLite")
            except Exception as e:
                logger.error(f"Error saving memory to SQLite: {e}")
    
    def load_memory(self) -> dict:
        """Load all memories from SQLite
        
        Returns:
            Dict with 'memories' list and 'stats' dict
        """
        if not self.is_available():
            return {'memories': [], 'stats': {}}
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Load memories
                cursor.execute('SELECT * FROM memories')
                rows = cursor.fetchall()
                memories = []
                for row in rows:
                    mem = dict(row)
                    mem['patterns'] = json.loads(mem['patterns'])
                    memories.append(mem)
                
                # Load stats
                cursor.execute('SELECT value FROM meta WHERE key = ?', ('learning_stats',))
                stats_row = cursor.fetchone()
                stats = json.loads(stats_row['value']) if stats_row else {}
                
                logger.info(f"Loaded {len(memories)} memories from SQLite")
                return {'memories': memories, 'stats': stats}
            except Exception as e:
                logger.error(f"Error loading memory from SQLite: {e}")
                return {'memories': [], 'stats': {}}
    
    # ==================== Local Learning Collection ====================
    
    def save_local_learning(self, data: dict):
        """Save local learning state to SQLite
        
        Args:
            data: Dict with 'stats', 'word_network', 'entities', 'preferences'
        """
        if not self.is_available():
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Save stats
                cursor.execute('INSERT OR REPLACE INTO local_learning (type, data) VALUES (?, ?)',
                              ('stats', json.dumps(data.get('stats', {}))))
                
                # Save word network
                cursor.execute('INSERT OR REPLACE INTO local_learning (type, data) VALUES (?, ?)',
                              ('word_network', json.dumps(data.get('word_network', {}))))
                
                # Save entities
                cursor.execute('INSERT OR REPLACE INTO local_learning (type, data) VALUES (?, ?)',
                              ('entities', json.dumps(data.get('entities', {}))))
                
                # Save preferences
                cursor.execute('INSERT OR REPLACE INTO local_learning (type, data) VALUES (?, ?)',
                              ('preferences', json.dumps(data.get('preferences', {}))))
                
                self.conn.commit()
                logger.info("Saved local learning state to SQLite")
            except Exception as e:
                logger.error(f"Error saving local learning to SQLite: {e}")
    
    def load_local_learning(self) -> dict:
        """Load local learning state from SQLite
        
        Returns:
            Dict with 'stats', 'word_network', 'entities', 'preferences'
        """
        if not self.is_available():
            return {
                'stats': {},
                'word_network': {},
                'entities': {},
                'preferences': {}
            }
        
        with self._lock:
            try:
                result = {
                    'stats': {},
                    'word_network': {},
                    'entities': {},
                    'preferences': {}
                }
                
                cursor = self.conn.cursor()
                cursor.execute('SELECT type, data FROM local_learning')
                rows = cursor.fetchall()
                
                for row in rows:
                    row_type = row['type']
                    row_data = json.loads(row['data'])
                    if row_type in result:
                        result[row_type] = row_data
                
                logger.info(f"Loaded local learning from SQLite: "
                           f"{len(result['word_network'])} words, "
                           f"{len(result['entities'])} entities")
                return result
            except Exception as e:
                logger.error(f"Error loading local learning from SQLite: {e}")
                return {
                    'stats': {},
                    'word_network': {},
                    'entities': {},
                    'preferences': {}
                }
    
    # ==================== Internet Learning Collection ====================
    
    def save_internet_learning(self, data: dict):
        """Save internet learning topics to SQLite
        
        Args:
            data: Dict with 'topics' list and 'stats' dict
        """
        if not self.is_available():
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Get full topic data if available
                topics_data = data.get('topics_data', {})
                
                # Upsert topics
                for topic, topic_data in topics_data.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO learned_topics (topic, summary, category, learned_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        topic,
                        topic_data.get('summary', ''),
                        topic_data.get('category', 'general'),
                        topic_data.get('learned_at', datetime.now().isoformat())
                    ))
                
                # Save stats
                stats = data.get('stats', {})
                if stats:
                    cursor.execute('INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)',
                                  ('internet_learning_stats', json.dumps(stats)))
                
                self.conn.commit()
                logger.info(f"Saved {len(topics_data)} learned topics to SQLite")
            except Exception as e:
                logger.error(f"Error saving internet learning to SQLite: {e}")
    
    def load_internet_learning(self) -> dict:
        """Load internet learning topics from SQLite
        
        Returns:
            Dict with 'topics' list and 'stats' dict
        """
        if not self.is_available():
            return {'topics': [], 'stats': {}, 'topics_data': {}}
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Load topics
                cursor.execute('SELECT * FROM learned_topics')
                rows = cursor.fetchall()
                topics = []
                topics_data = {}
                
                for row in rows:
                    topic_data = dict(row)
                    topics.append(topic_data['topic'])
                    topics_data[topic_data['topic']] = topic_data
                
                # Load stats
                cursor.execute('SELECT value FROM meta WHERE key = ?', ('internet_learning_stats',))
                stats_row = cursor.fetchone()
                stats = json.loads(stats_row['value']) if stats_row else {}
                
                logger.info(f"Loaded {len(topics)} learned topics from SQLite")
                return {'topics': topics, 'stats': stats, 'topics_data': topics_data}
            except Exception as e:
                logger.error(f"Error loading internet learning from SQLite: {e}")
                return {'topics': [], 'stats': {}, 'topics_data': {}}
    
    # ==================== Full Topic Data ====================
    
    def save_topic_full_data(self, topic: str, summary: str, category: str):
        """Save full topic data for internet learning
        
        Args:
            topic: Topic name
            summary: Wikipedia summary
            category: Category (science, technology, etc.)
        """
        if not self.is_available():
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO learned_topics (topic, summary, category, learned_at)
                    VALUES (?, ?, ?, ?)
                ''', (topic, summary, category, datetime.now().isoformat()))
                self.conn.commit()
            except Exception as e:
                logger.error(f"Error saving topic data to SQLite: {e}")
    
    def load_all_topics_full_data(self) -> dict:
        """Load all topic full data
        
        Returns:
            Dict mapping topic names to their full data
        """
        if not self.is_available():
            return {}
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT * FROM learned_topics')
                rows = cursor.fetchall()
                topics = {}
                for row in rows:
                    data = dict(row)
                    topics[data['topic']] = data
                return topics
            except Exception as e:
                logger.error(f"Error loading topic full data from SQLite: {e}")
                return {}
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            with self._lock:
                self.conn.close()
                self.conn = None
                logger.info("SQLite database connection closed")
