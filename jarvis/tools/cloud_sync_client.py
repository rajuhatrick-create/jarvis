"""
Cloud Sync Client - Periodically syncs local JARVIS memories with the cloud JARVIS instance.
Fetches memories from the cloud and pushes local memories to the cloud via HTTP API.
"""

import json
import logging
import threading
import time
from typing import Dict, Optional
from datetime import datetime

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None

logger = logging.getLogger('JARVIS.tools.cloud_sync_client')


class CloudSyncClient:
    """Syncs local JARVIS memory with a remote cloud JARVIS instance"""
    
    def __init__(self, config: Dict, learning_ai=None, internet_learner=None):
        self.config = config.get('cloud_sync', {})
        self.enabled = self.config.get('enabled', False)
        self.cloud_url = self.config.get('cloud_url', '').rstrip('/')
        self.sync_interval = self.config.get('sync_interval_minutes', 30) * 60  # Convert to seconds
        self.pull_memories = self.config.get('pull_memories', True)
        self.push_memories = self.config.get('push_memories', True)
        self.learning_ai = learning_ai
        self.internet_learner = internet_learner
        
        self.last_sync_time = None
        self.sync_count = 0
        self.last_sync_result = None
        self.is_running = False
        self._thread = None
        
        if self.enabled and self.cloud_url:
            logger.info(f"CloudSyncClient initialized: syncing with {self.cloud_url} every {self.sync_interval}s")
        else:
            logger.info("CloudSyncClient disabled or no cloud URL configured")
    
    def start(self):
        """Start the background sync loop"""
        if not self.enabled or not self.cloud_url:
            logger.info("Cloud sync not started: disabled or no cloud URL")
            return
        
        if self._thread and self._thread.is_alive():
            logger.info("Cloud sync already running")
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        logger.info(f"Cloud sync loop started (interval: {self.sync_interval}s)")
    
    def stop(self):
        """Stop the background sync loop"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Cloud sync loop stopped")
    
    def sync_now(self) -> Dict:
        """Trigger an immediate sync"""
        try:
            result = self._do_sync()
            return result
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _sync_loop(self):
        """Background loop that periodically syncs with cloud"""
        while self.is_running:
            try:
                result = self._do_sync()
                if result.get('status') == 'success':
                    self.sync_count += 1
                    logger.info(f"Cloud sync #{self.sync_count}: {result.get('message', 'OK')}")
                elif result.get('status') == 'error':
                    logger.warning(f"Cloud sync error: {result.get('message', 'Unknown')}")
            except Exception as e:
                logger.error(f"Cloud sync loop error: {e}")
            
            # Wait for the next sync interval
            for _ in range(self.sync_interval):
                if not self.is_running:
                    break
                time.sleep(1)
    
    def _do_sync(self) -> Dict:
        """Perform one sync cycle: pull from cloud, push to cloud"""
        result = {'pulled': 0, 'pushed': 0, 'status': 'success'}
        
        # Pull memories from cloud
        if self.pull_memories:
            try:
                pulled = self._pull_from_cloud()
                result['pulled'] = pulled
            except Exception as e:
                logger.error(f"Pull from cloud failed: {e}")
                result['pull_error'] = str(e)
        
        # Push memories to cloud
        if self.push_memories:
            try:
                pushed = self._push_to_cloud()
                result['pushed'] = pushed
            except Exception as e:
                logger.error(f"Push to cloud failed: {e}")
                result['push_error'] = str(e)
        
        self.last_sync_time = datetime.now().isoformat()
        self.last_sync_result = result
        
        total = result['pulled'] + result['pushed']
        result['message'] = f"Pulled {result['pulled']} memories, pushed {result['pushed']} memories"
        
        return result
    
    def _http_get(self, endpoint: str) -> Optional[Dict]:
        """Make an HTTP GET request to the cloud JARVIS"""
        if urllib is None:
            raise RuntimeError("urllib not available")
        
        url = f"{self.cloud_url}{endpoint}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except urllib.error.URLError as e:
            logger.warning(f"HTTP GET failed for {endpoint}: {e}")
            raise
        except Exception as e:
            logger.warning(f"HTTP GET error for {endpoint}: {e}")
            raise
    
    def _http_post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make an HTTP POST request to the cloud JARVIS"""
        if urllib is None:
            raise RuntimeError("urllib not available")
        
        url = f"{self.cloud_url}{endpoint}"
        body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=body,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.URLError as e:
            logger.warning(f"HTTP POST failed for {endpoint}: {e}")
            raise
        except Exception as e:
            logger.warning(f"HTTP POST error for {endpoint}: {e}")
            raise
    
    def _pull_from_cloud(self) -> int:
        """Pull memories from the cloud JARVIS and merge into local memory"""
        # Fetch cloud memories
        cloud_data = self._http_get('/api/sync/export')
        if not cloud_data:
            return 0
        
        imported = 0
        
        # Import memories
        if self.learning_ai and 'memories' in cloud_data:
            existing_ids = set(self.learning_ai.memory.keys())
            from jarvis.brain.learning import MemoryEntry
            for item in cloud_data.get('memories', []):
                entry_id = item.get('id', '')
                if entry_id and entry_id not in existing_ids:
                    clean_item = {k: v for k, v in item.items() if k in MemoryEntry.__dataclass_fields__}
                    entry = MemoryEntry(**clean_item)
                    self.learning_ai.memory[entry_id] = entry
                    for pattern in entry.patterns:
                        self.learning_ai.matcher.add_document(pattern)
                    imported += 1
            if imported > 0:
                self.learning_ai._save_memory()
                logger.info(f"Pulled {imported} new memories from cloud")
        
        # Import internet learning topics
        if self.internet_learner and 'internet_learning' in cloud_data:
            existing_topics = set(self.internet_learner.learned_topics)
            for topic_data in cloud_data.get('internet_learning', []):
                if isinstance(topic_data, dict):
                    topic = topic_data.get('topic', '')
                    if topic and topic not in existing_topics:
                        # Add the topic to learned topics
                        self.internet_learner.learned_topics.add(topic)
                        # Also add to learning AI memory if summary is available
                        if self.learning_ai and 'summary' in topic_data:
                            self.learning_ai.add_fact(topic, topic_data['summary'])
                        imported += 1
            if imported > 0:
                self.internet_learner._save_learned_topics()
                logger.info(f"Pulled {imported} new topics from cloud")
        
        return imported
    
    def _push_to_cloud(self) -> int:
        """Push local memories to the cloud JARVIS"""
        if not self.learning_ai:
            return 0
        
        # Build export data from local memory
        from dataclasses import asdict
        local_data = {
            'memories': [asdict(m) for m in self.learning_ai.memory.values()],
            'internet_learning': []
        }
        
        # Add internet learning topics
        if self.internet_learner:
            for mem_id, entry in self.learning_ai.memory.items():
                if entry.category and entry.category.startswith('internet_'):
                    local_data['internet_learning'].append({
                        'topic': entry.response.split(':')[0].strip().lower(),
                        'summary': entry.response,
                        'category': entry.category.replace('internet_', ''),
                        'learned_at': entry.created_at
                    })
        
        # Push to cloud
        result = self._http_post('/api/sync/import', local_data)
        if result and result.get('success'):
            imported = result.get('imported', {})
            pushed = imported.get('memories', 0) + imported.get('topics', 0)
            logger.info(f"Pushed {pushed} items to cloud")
            return pushed
        
        return 0
    
    def get_status(self) -> Dict:
        """Get sync status"""
        return {
            'enabled': self.enabled,
            'cloud_url': self.cloud_url,
            'is_running': self.is_running,
            'last_sync': self.last_sync_time,
            'sync_count': self.sync_count,
            'last_result': self.last_sync_result,
            'sync_interval_minutes': self.config.get('sync_interval_minutes', 30)
        }
