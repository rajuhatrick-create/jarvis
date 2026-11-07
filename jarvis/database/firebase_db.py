"""
Firebase Database Layer - Firestore integration for cloud-synced memory.
Replaces local JSON file storage with Firebase Firestore for cloud deployment.
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

logger = logging.getLogger('JARVIS.database.firebase')


class FirebaseDB:
    """Firebase Firestore database wrapper for JARVIS memory storage"""
    
    def __init__(self, config: dict):
        self.config = config.get('firebase', {})
        self.enabled = self.config.get('enabled', False)
        self.db = None
        self._initialized = False
        
        if self.enabled:
            self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            cred_path = self.config.get('credentials_path', 'firebase_config.json')
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'projectId': self.config.get('project_id', 'jarvis-cloud')
            })
            self.db = firestore.client()
            self._initialized = True
            logger.info("Firebase Firestore initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self._initialized = False
            self.enabled = False
    
    def is_available(self) -> bool:
        """Check if Firebase is available and initialized"""
        return self.enabled and self._initialized and self.db is not None
    
    # ==================== Memory Collection ====================
    
    def save_memory(self, data: dict):
        """Save all memories to Firestore
        
        Args:
            data: Dict with 'memories' list and 'stats' dict
        """
        if not self.is_available():
            return
        
        try:
            memories_ref = self.db.collection('memories')
            
            # Build index of existing document IDs
            existing = {doc.id: doc.to_dict() for doc in memories_ref.stream()}
            
            # Build index of incoming memories by ID
            incoming = {mem['id']: mem for mem in data.get('memories', [])}
            
            # Upsert memories
            for mem_id, mem in incoming.items():
                doc_ref = memories_ref.document(mem_id)
                mem['updated_at'] = datetime.now().isoformat()
                doc_ref.set(mem, merge=True)
            
            # Delete memories no longer in local data
            for doc_id in existing:
                if doc_id not in incoming:
                    memories_ref.document(doc_id).delete()
            
            # Save stats as a single document
            stats_ref = self.db.collection('meta').document('learning_stats')
            stats_ref.set(data.get('stats', {}), merge=True)
            
            logger.info(f"Saved {len(incoming)} memories to Firestore")
        except Exception as e:
            logger.error(f"Error saving memory to Firestore: {e}")
    
    def load_memory(self) -> dict:
        """Load all memories from Firestore
        
        Returns:
            Dict with 'memories' list and 'stats' dict
        """
        if not self.is_available():
            return {'memories': [], 'stats': {}}
        
        try:
            memories_ref = self.db.collection('memories')
            memories = []
            
            for doc in memories_ref.stream():
                mem = doc.to_dict()
                memories.append(mem)
            
            # Load stats
            stats_ref = self.db.collection('meta').document('learning_stats')
            stats_doc = stats_ref.get()
            stats = stats_doc.to_dict() if stats_doc.exists else {}
            
            logger.info(f"Loaded {len(memories)} memories from Firestore")
            return {'memories': memories, 'stats': stats}
        except Exception as e:
            logger.error(f"Error loading memory from Firestore: {e}")
            return {'memories': [], 'stats': {}}
    
    # ==================== Local Learning Collection ====================
    
    def save_local_learning(self, data: dict):
        """Save local learning state to Firestore
        
        Args:
            data: Dict with 'stats', 'word_network', 'entities', 'preferences'
        """
        if not self.is_available():
            return
        
        try:
            # Save as a single document with sub-collections for large data
            ll_ref = self.db.collection('local_learning').document('state')
            
            # Save stats
            stats_ref = self.db.collection('local_learning').document('stats')
            stats_ref.set(data.get('stats', {}), merge=True)
            
            # Save word network (can be large, so use sub-collection)
            wn_ref = self.db.collection('local_learning').document('word_network')
            wn_ref.set({'data': data.get('word_network', {})}, merge=True)
            
            # Save entities
            entities_ref = self.db.collection('local_learning').document('entities')
            entities_ref.set({'data': data.get('entities', {})}, merge=True)
            
            # Save preferences
            prefs_ref = self.db.collection('local_learning').document('preferences')
            prefs_ref.set({'data': data.get('preferences', {})}, merge=True)
            
            logger.info("Saved local learning state to Firestore")
        except Exception as e:
            logger.error(f"Error saving local learning to Firestore: {e}")
    
    def load_local_learning(self) -> dict:
        """Load local learning state from Firestore
        
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
        
        try:
            result = {
                'stats': {},
                'word_network': {},
                'entities': {},
                'preferences': {}
            }
            
            # Load stats
            stats_doc = self.db.collection('local_learning').document('stats').get()
            if stats_doc.exists:
                result['stats'] = stats_doc.to_dict()
            
            # Load word network
            wn_doc = self.db.collection('local_learning').document('word_network').get()
            if wn_doc.exists:
                result['word_network'] = wn_doc.to_dict().get('data', {})
            
            # Load entities
            ent_doc = self.db.collection('local_learning').document('entities').get()
            if ent_doc.exists:
                result['entities'] = ent_doc.to_dict().get('data', {})
            
            # Load preferences
            pref_doc = self.db.collection('local_learning').document('preferences').get()
            if pref_doc.exists:
                result['preferences'] = pref_doc.to_dict().get('data', {})
            
            logger.info(f"Loaded local learning from Firestore: "
                       f"{len(result['word_network'])} words, "
                       f"{len(result['entities'])} entities")
            return result
        except Exception as e:
            logger.error(f"Error loading local learning from Firestore: {e}")
            return {
                'stats': {},
                'word_network': {},
                'entities': {},
                'preferences': {}
            }
    
    # ==================== Internet Learning Collection ====================
    
    def save_internet_learning(self, data: dict):
        """Save internet learning topics to Firestore
        
        Args:
            data: Dict with 'topics' list and 'stats' dict
        """
        if not self.is_available():
            return
        
        try:
            topics_ref = self.db.collection('learned_topics')
            
            # Build index of existing topics
            existing = {doc.id: doc.to_dict() for doc in topics_ref.stream()}
            
            # Get incoming topics
            incoming_topics = set(data.get('topics', []))
            incoming = {}
            
            # Load full topic data from local learning AI if available
            for topic in incoming_topics:
                topic_doc = self.db.collection('learned_topics').document(topic)
                # Check if we have the topic data in the full_data collection
                full_doc = self.db.collection('learned_topics_full').document(topic).get()
                if full_doc.exists:
                    incoming[topic] = full_doc.to_dict()
                else:
                    incoming[topic] = {'topic': topic, 'learned_at': datetime.now().isoformat()}
            
            # Upsert topics
            for topic, topic_data in incoming.items():
                doc_ref = topics_ref.document(topic)
                doc_ref.set(topic_data, merge=True)
            
            # Delete topics no longer in local data
            for doc_id in existing:
                if doc_id not in incoming_topics:
                    topics_ref.document(doc_id).delete()
            
            # Save stats
            stats_ref = self.db.collection('meta').document('internet_learning_stats')
            stats_ref.set(data.get('stats', {}), merge=True)
            
            logger.info(f"Saved {len(incoming_topics)} learned topics to Firestore")
        except Exception as e:
            logger.error(f"Error saving internet learning to Firestore: {e}")
    
    def load_internet_learning(self) -> dict:
        """Load internet learning topics from Firestore
        
        Returns:
            Dict with 'topics' list and 'stats' dict
        """
        if not self.is_available():
            return {'topics': [], 'stats': {}}
        
        try:
            topics_ref = self.db.collection('learned_topics')
            topics = []
            
            for doc in topics_ref.stream():
                topic_data = doc.to_dict()
                topic_name = topic_data.get('topic', doc.id)
                topics.append(topic_name)
            
            # Also save full topic data for learning AI
            full_topics = {}
            for doc in topics_ref.stream():
                topic_data = doc.to_dict()
                topic_name = topic_data.get('topic', doc.id)
                full_topics[topic_name] = topic_data
            
            # Save full data to learned_topics_full collection
            for topic_name, topic_data in full_topics.items():
                full_ref = self.db.collection('learned_topics_full').document(topic_name)
                full_ref.set(topic_data, merge=True)
            
            # Load stats
            stats_ref = self.db.collection('meta').document('internet_learning_stats')
            stats_doc = stats_ref.get()
            stats = stats_doc.to_dict() if stats_doc.exists else {}
            
            logger.info(f"Loaded {len(topics)} learned topics from Firestore")
            return {'topics': topics, 'stats': stats}
        except Exception as e:
            logger.error(f"Error loading internet learning from Firestore: {e}")
            return {'topics': [], 'stats': {}}
    
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
        
        try:
            doc_ref = self.db.collection('learned_topics_full').document(topic)
            doc_ref.set({
                'topic': topic,
                'summary': summary,
                'category': category,
                'learned_at': datetime.now().isoformat()
            }, merge=True)
        except Exception as e:
            logger.error(f"Error saving topic data to Firestore: {e}")
    
    def load_all_topics_full_data(self) -> dict:
        """Load all topic full data
        
        Returns:
            Dict mapping topic names to their full data
        """
        if not self.is_available():
            return {}
        
        try:
            topics = {}
            for doc in self.db.collection('learned_topics_full').stream():
                data = doc.to_dict()
                topic_name = data.get('topic', doc.id)
                topics[topic_name] = data
            return topics
        except Exception as e:
            logger.error(f"Error loading topic full data from Firestore: {e}")
            return {}
