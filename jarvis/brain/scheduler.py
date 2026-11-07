"""
Task Scheduler - Manages reminders, alarms, and scheduled tasks.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from threading import Thread
import time

logger = logging.getLogger('JARVIS.brain.scheduler')


@dataclass
class Reminder:
    """A scheduled reminder"""
    id: str
    message: str
    trigger_time: str  # ISO format datetime
    created_at: str
    is_completed: bool = False
    completed_at: Optional[str] = None
    
    def trigger_datetime(self) -> datetime:
        return datetime.fromisoformat(self.trigger_time)
    
    def is_due(self) -> bool:
        if self.is_completed:
            return False
        return datetime.now() >= self.trigger_datetime()


class TaskScheduler:
    """Manages reminders and scheduled tasks"""
    
    def __init__(self, config: Dict):
        self.config = config.get('scheduler', {})
        self.max_reminders = self.config.get('max_reminders', 50)
        self.check_interval = self.config.get('check_interval', 10)
        
        self.reminders: Dict[str, Reminder] = {}
        self.callbacks: List[callable] = []
        self._running = False
        self._thread = None
        
        # Load saved reminders
        self._load_reminders()
        logger.info(f"TaskScheduler initialized with {len(self.reminders)} saved reminders")
    
    def _get_storage_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "data" / "reminders.json"
    
    def _load_reminders(self):
        """Load reminders from disk"""
        path = self._get_storage_path()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        reminder = Reminder(**item)
                        if not reminder.is_completed:
                            self.reminders[reminder.id] = reminder
                logger.info(f"Loaded {len(self.reminders)} reminders from disk")
            except Exception as e:
                logger.error(f"Error loading reminders: {e}")
    
    def _save_reminders(self):
        """Save reminders to disk"""
        path = self._get_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = [asdict(r) for r in self.reminders.values()]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    def add_reminder(self, message: str, trigger_time: datetime) -> Reminder:
        """Add a new reminder"""
        # Clean up old completed reminders
        self._cleanup_old_reminders()
        
        reminder_id = f"rem_{len(self.reminders)}_{int(datetime.now().timestamp())}"
        reminder = Reminder(
            id=reminder_id,
            message=message,
            trigger_time=trigger_time.isoformat(),
            created_at=datetime.now().isoformat()
        )
        self.reminders[reminder_id] = reminder
        self._save_reminders()
        logger.info(f"Added reminder: {message} at {trigger_time}")
        return reminder
    
    def _cleanup_old_reminders(self):
        """Remove old completed reminders"""
        completed = [rid for rid, r in self.reminders.items() if r.is_completed]
        if len(completed) > self.max_reminders // 2:
            # Remove oldest completed
            to_remove = sorted(completed, key=lambda x: self.reminders[x].completed_at)[:len(completed)//2]
            for rid in to_remove:
                del self.reminders[rid]
    
    def get_reminders(self, include_completed: bool = False) -> List[Reminder]:
        """Get all reminders"""
        if include_completed:
            return sorted(self.reminders.values(), key=lambda r: r.trigger_datetime())
        return sorted(
            [r for r in self.reminders.values() if not r.is_completed],
            key=lambda r: r.trigger_datetime()
        )
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            self._save_reminders()
            return True
        return False
    
    def on_reminder_due(self, callback: callable):
        """Register a callback for when a reminder is due"""
        self.callbacks.append(callback)
    
    def start(self):
        """Start the scheduler background thread"""
        if self._running:
            return
        self._running = True
        self._thread = Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        logger.info("TaskScheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("TaskScheduler stopped")
    
    def _check_loop(self):
        """Background loop to check for due reminders"""
        while self._running:
            for reminder in list(self.reminders.values()):
                if reminder.is_due() and not reminder.is_completed:
                    reminder.is_completed = True
                    reminder.completed_at = datetime.now().isoformat()
                    self._save_reminders()
                    logger.info(f"Reminder due: {reminder.message}")
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(reminder)
                        except Exception as e:
                            logger.error(f"Error in reminder callback: {e}")
            time.sleep(self.check_interval)
    
    def parse_time_expression(self, expression: str) -> Optional[datetime]:
        """Parse natural language time expressions"""
        expression = expression.lower().strip()
        now = datetime.now()
        
        # "in X minutes/hours"
        if 'in ' in expression:
            parts = expression.split()
            for i, part in enumerate(parts):
                if part.isdigit():
                    number = int(part)
                    if i + 1 < len(parts):
                        unit = parts[i + 1]
                        if 'minute' in unit:
                            return now + timedelta(minutes=number)
                        elif 'hour' in unit:
                            return now + timedelta(hours=number)
                        elif 'second' in unit:
                            return now + timedelta(seconds=number)
        
        # "at HH:MM"
        if 'at ' in expression:
            time_part = expression.split('at ')[-1].strip()
            try:
                time_obj = datetime.strptime(time_part, "%H:%M").time()
                result = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                if result < now:
                    result += timedelta(days=1)
                return result
            except ValueError:
                pass
        
        # "at X o'clock"
        if "o'clock" in expression:
            try:
                hour = int(expression.split()[expression.split().index('at') + 1])
                time_obj = datetime.strptime(str(hour), "%H").time()
                result = now.replace(hour=time_obj.hour, minute=0, second=0, microsecond=0)
                if result < now:
                    result += timedelta(days=1)
                return result
            except (ValueError, IndexError):
                pass
        
        # "tomorrow"
        if 'tomorrow' in expression:
            tomorrow = now + timedelta(days=1)
            if 'at ' in expression:
                time_part = expression.split('at ')[-1].strip()
                try:
                    time_obj = datetime.strptime(time_part, "%H:%M").time()
                    return tomorrow.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                except ValueError:
                    pass
            return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return None
