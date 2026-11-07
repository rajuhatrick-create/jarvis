"""
Cloud Sync - Bidirectional sync between local cache and SQLite database.
Keeps local JARVIS memory in sync with the cloud brain.
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger('JARVIS.tools.cloud_sync')


class CloudSync:
    """Handles bidirectional sync between local cache and SQLite"""
    
    def __init__(self, sqlite_db, learning_ai=None, local_learning=None, internet_learner=None):
        self.sqlite_db = sqlite_db
        self.learning_ai = learning_ai
        self.local_learning = local_learning
        self.internet_learner = internet_learner
        
        self.last_sync_time: Optional[datetime] = None
        self.sync_count = 0
        self.pending_changes = 0
    
    def is_available(self) -> bool:
        """Check if cloud sync is available"""
        return self.sqlite_db is not None and self.sqlite_db.is_available()
    
    def sync_all(self) -> Dict:
        """Perform a full sync of all data"""
        if not self.is_available():
            return {
                'status': 'error',
                'message': 'SQLite database not available',
                'timestamp': datetime.now().isoformat()
            }
        
        results = {
            'memories': False,
            'local_learning': False,
            'internet_learning': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Sync memories
        if self.learning_ai:
            try:
                data = {
                    'memories': [
                        {
                            'id': m.id,
                            'patterns': m.patterns,
                            'response': m.response,
                            'intent': m.intent,
                            'success_count': m.success_count,
                            'failure_count': m.failure_count,
                            'created_at': m.created_at,
                            'last_used': m.last_used,
                            'category': m.category
                        }
                        for m in self.learning_ai.memory.values()
                    ],
                    'stats': self.learning_ai.get_stats()
                }
                self.sqlite_db.save_memory(data)
                results['memories'] = True
                logger.info(f"Synced {len(data['memories'])} memories to SQLite")
            except Exception as e:
                logger.error(f"Error syncing memories: {e}")
        
        # Sync local learning
        if self.local_learning:
            try:
                from jarvis.brain.local_learning import asdict
                data = {
                    'stats': self.local_learning.stats,
                    'word_network': {
                        word: {
                            'associations': wa.associations,
                            'category': wa.category
                        }
                        for word, wa in self.local_learning.word_network.network.items()
                    },
                    'entities': {
                        key: asdict(entity)
                        for key, entity in self.local_learning.entity_extractor.entities.items()
                    },
                    'preferences': {
                        key: asdict(pref)
                        for key, pref in self.local_learning.preference_learner.preferences.items()
                    }
                }
                self.sqlite_db.save_local_learning(data)
                results['local_learning'] = True
                logger.info("Synced local learning to SQLite")
            except Exception as e:
                logger.error(f"Error syncing local learning: {e}")
        
        # Sync internet learning
        if self.internet_learner:
            try:
                data = {
                    'topics': list(self.internet_learner.learned_topics),
                    'stats': self.internet_learner.stats
                }
                self.sqlite_db.save_internet_learning(data)
                results['internet_learning'] = True
                logger.info(f"Synced {len(data['topics'])} topics to SQLite")
            except Exception as e:
                logger.error(f"Error syncing internet learning: {e}")
        
        self.last_sync_time = datetime.now()
        self.sync_count += 1
        results['status'] = 'success'
        results['sync_count'] = self.sync_count
        
        return results
    
    def get_status(self) -> Dict:
        """Get current sync status"""
        return {
            'connected': self.is_available(),
            'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_count': self.sync_count,
            'pending_changes': self.pending_changes
        }
