"""
Proactive Assistant - Monitors systems and proactively suggests actions.
Like movie JARVIS, it anticipates needs and alerts the user before being asked.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict

import psutil

logger = logging.getLogger('JARVIS.brain.proactive')


class UserPattern:
    """Tracks user behavior patterns"""
    
    def __init__(self):
        self.active_hours = defaultdict(int)  # hour -> count
        self.app_usage = defaultdict(int)  # app_name -> count
        self.common_tasks = defaultdict(int)  # task_type -> count
        self.work_sessions = []  # list of (start_time, end_time)
        self.current_session_start: Optional[datetime] = None
        self.total_interactions = 0
    
    def record_activity(self, hour: int):
        """Record activity at a specific hour"""
        self.active_hours[hour] += 1
    
    def record_app_usage(self, app_name: str):
        """Record app usage"""
        self.app_usage[app_name] += 1
    
    def record_task(self, task_type: str):
        """Record a task type"""
        self.common_tasks[task_type] += 1
    
    def start_session(self):
        """Start a work session"""
        self.current_session_start = datetime.now()
    
    def end_session(self):
        """End a work session"""
        if self.current_session_start:
            self.work_sessions.append((self.current_session_start, datetime.now()))
            self.current_session_start = None
    
    def get_peak_hours(self, top_n: int = 3) -> List[int]:
        """Get the most active hours"""
        if not self.active_hours:
            return []
        sorted_hours = sorted(self.active_hours.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:top_n]]
    
    def get_frequent_apps(self, top_n: int = 5) -> List[str]:
        """Get most frequently used apps"""
        if not self.app_usage:
            return []
        sorted_apps = sorted(self.app_usage.items(), key=lambda x: x[1], reverse=True)
        return [app for app, count in sorted_apps[:top_n]]
    
    def get_common_tasks(self, top_n: int = 5) -> List[str]:
        """Get most common task types"""
        if not self.common_tasks:
            return []
        sorted_tasks = sorted(self.common_tasks.items(), key=lambda x: x[1], reverse=True)
        return [task for task, count in sorted_tasks[:top_n]]
    
    def get_summary(self) -> Dict:
        """Get pattern summary"""
        return {
            "peak_hours": self.get_peak_hours(),
            "frequent_apps": self.get_frequent_apps(),
            "common_tasks": self.get_common_tasks(),
            "total_sessions": len(self.work_sessions),
            "total_interactions": self.total_interactions,
        }


class SystemAlert:
    """Represents a system alert"""
    
    def __init__(self, alert_type: str, message: str, urgency: str = "normal", 
                 suggested_action: str = "", timestamp: datetime = None):
        self.alert_type = alert_type
        self.message = message
        self.urgency = urgency  # "low", "normal", "high", "critical"
        self.suggested_action = suggested_action
        self.timestamp = timestamp or datetime.now()
        self.dismissed = False
    
    def to_dict(self) -> Dict:
        return {
            "type": self.alert_type,
            "message": self.message,
            "urgency": self.urgency,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
            "dismissed": self.dismissed,
        }


class ProactiveAssistant:
    """Monitors systems and proactively suggests actions"""
    
    def __init__(self, config: dict, personality=None, sqlite_db=None):
        self.config = config.get('proactive', {})
        self.enabled = self.config.get('enabled', True)
        self.check_interval = self.config.get('check_interval_seconds', 30)
        self.personality = personality
        self.sqlite_db = sqlite_db
        
        # Thresholds
        self.thresholds = {
            'battery_low': self.config.get('battery_low_threshold', 20),
            'battery_critical': self.config.get('battery_critical_threshold', 10),
            'cpu_high': self.config.get('cpu_high_threshold', 85),
            'cpu_critical': self.config.get('cpu_critical_threshold', 95),
            'memory_high': self.config.get('memory_high_threshold', 85),
            'memory_critical': self.config.get('memory_critical_threshold', 95),
            'disk_low': self.config.get('disk_low_threshold', 85),
            'disk_critical': self.config.get('disk_critical_threshold', 95),
        }
        
        # User patterns
        self.user_patterns = UserPattern()
        
        # Alert history to avoid spam
        self.alert_history: List[SystemAlert] = []
        self.recent_alerts = defaultdict(int)  # alert_type -> count in last hour
        self.max_alerts_per_hour = self.config.get('max_alerts_per_hour', 3)
        
        # Callback for sending suggestions
        self.suggestion_callback: Optional[Callable] = None
        
        # Monitoring state
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_check = {}
        
        logger.info("ProactiveAssistant initialized with check interval %ds", self.check_interval)
    
    def set_suggestion_callback(self, callback: Callable):
        """Set callback for sending suggestions to user"""
        self.suggestion_callback = callback
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if not self.enabled:
            logger.info("Proactive monitoring is disabled")
            return
        
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Proactive monitoring started")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Proactive monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                self._check_systems()
            except Exception as e:
                logger.error("Error in proactive monitoring: %s", e)
            time.sleep(self.check_interval)
    
    def _check_systems(self):
        """Check all systems and generate alerts"""
        now = datetime.now()
        
        # Clean old alerts (older than 1 hour)
        self._clean_old_alerts()
        
        # Check battery
        self._check_battery()
        
        # Check CPU
        self._check_cpu()
        
        # Check memory
        self._check_memory()
        
        # Check disk
        self._check_disk()
        
        # Check for scheduled tasks
        self._check_scheduled_tasks()
        
        # Record user activity pattern
        self.user_patterns.record_activity(now.hour)
        self.user_patterns.total_interactions += 1
    
    def _clean_old_alerts(self):
        """Remove alerts older than 1 hour from recent_alerts counter"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        self.recent_alerts = {
            k: v for k, v in self.recent_alerts.items()
            if any(alert.timestamp > one_hour_ago for alert in self.alert_history if alert.alert_type == k)
        }
    
    def _can_alert(self, alert_type: str) -> bool:
        """Check if we can send an alert (rate limiting)"""
        return self.recent_alerts.get(alert_type, 0) < self.max_alerts_per_hour
    
    def _send_alert(self, alert: SystemAlert):
        """Send an alert to the user"""
        self.alert_history.append(alert)
        self.recent_alerts[alert.alert_type] += 1
        
        # Format with personality if available
        message = alert.message
        if self.personality:
            message = self.personality.format_proactive_suggestion(message, alert.urgency)
        
        # Send via callback if available
        if self.suggestion_callback:
            try:
                self.suggestion_callback(message, alert.urgency, alert.suggested_action)
            except Exception as e:
                logger.error("Error sending alert: %s", e)
        
        logger.info("Proactive alert [%s]: %s", alert.urgency, message)
    
    def _check_battery(self):
        """Check battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return  # No battery (desktop)
            
            percent = battery.percent
            powered_on = battery.power_plugged
            
            if not powered_on:
                if percent <= self.thresholds['battery_critical']:
                    if self._can_alert('battery_critical'):
                        alert = SystemAlert(
                            alert_type="battery_critical",
                            message=f"Battery is critically low at {percent}%. "
                                   f"Shall I close some applications to conserve power?",
                            urgency="critical",
                            suggested_action="close_apps"
                        )
                        self._send_alert(alert)
                elif percent <= self.thresholds['battery_low']:
                    if self._can_alert('battery_low'):
                        minutes = battery.secsleft // 60 if battery.secsleft != -1 else 0
                        alert = SystemAlert(
                            alert_type="battery_low",
                            message=f"Battery is at {percent}% with approximately {minutes} minutes remaining. "
                                   f"Would you like me to close some applications?",
                            urgency="high",
                            suggested_action="close_apps"
                        )
                        self._send_alert(alert)
        except Exception as e:
            logger.debug("Could not check battery: %s", e)
    
    def _check_cpu(self):
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent >= self.thresholds['cpu_critical']:
                if self._can_alert('cpu_critical'):
                    # Find top CPU processes
                    processes = sorted(psutil.process_iter(['cpu_percent', 'name']), 
                                     key=lambda x: x.info.get('cpu_percent', 0), reverse=True)
                    top_process = processes[0].info.get('name', 'unknown') if processes else 'unknown'
                    
                    alert = SystemAlert(
                        alert_type="cpu_critical",
                        message=f"CPU usage is critically high at {cpu_percent}%. "
                               f"The top process is {top_process}. Shall I help you close some applications?",
                        urgency="critical",
                        suggested_action="close_high_cpu_apps"
                    )
                    self._send_alert(alert)
            elif cpu_percent >= self.thresholds['cpu_high']:
                if self._can_alert('cpu_high'):
                    alert = SystemAlert(
                        alert_type="cpu_high",
                        message=f"CPU usage is quite high at {cpu_percent}%. "
                               f"System may be running slowly. Would you like me to identify resource-heavy processes?",
                        urgency="normal",
                        suggested_action="list_processes"
                    )
                    self._send_alert(alert)
        except Exception as e:
            logger.debug("Could not check CPU: %s", e)
    
    def _check_memory(self):
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent >= self.thresholds['memory_critical']:
                if self._can_alert('memory_critical'):
                    available_gb = memory.available / (1024 ** 3)
                    alert = SystemAlert(
                        alert_type="memory_critical",
                        message=f"Memory usage is critically high at {memory.percent}%. "
                               f"Only {available_gb:.1f}GB available. Shall I close some applications?",
                        urgency="critical",
                        suggested_action="close_memory_hogs"
                    )
                    self._send_alert(alert)
            elif memory.percent >= self.thresholds['memory_high']:
                if self._can_alert('memory_high'):
                    alert = SystemAlert(
                        alert_type="memory_high",
                        message=f"Memory usage is at {memory.percent}%. "
                               f"System may slow down soon. Would you like me to check what's using memory?",
                        urgency="normal",
                        suggested_action="list_memory_usage"
                    )
                    self._send_alert(alert)
        except Exception as e:
            logger.debug("Could not check memory: %s", e)
    
    def _check_disk(self):
        """Check disk space"""
        try:
            disk = psutil.disk_usage('C:\\')
            percent_used = (disk.used / disk.total) * 100
            
            if percent_used >= self.thresholds['disk_critical']:
                if self._can_alert('disk_critical'):
                    free_gb = disk.free / (1024 ** 3)
                    alert = SystemAlert(
                        alert_type="disk_critical",
                        message=f"Disk space is critically low. Only {free_gb:.1f}GB free. "
                               f"Shall I help you find large files to delete?",
                        urgency="critical",
                        suggested_action="find_large_files"
                    )
                    self._send_alert(alert)
            elif percent_used >= self.thresholds['disk_low']:
                if self._can_alert('disk_low'):
                    free_gb = disk.free / (1024 ** 3)
                    alert = SystemAlert(
                        alert_type="disk_low",
                        message=f"Disk space is getting low at {percent_used:.0f}% used. "
                               f"{free_gb:.1f}GB remaining. Would you like me to suggest files to clean up?",
                        urgency="normal",
                        suggested_action="suggest_cleanup"
                    )
                    self._send_alert(alert)
        except Exception as e:
            logger.debug("Could not check disk: %s", e)
    
    def _check_scheduled_tasks(self):
        """Check for upcoming scheduled tasks or reminders"""
        # This will be integrated with the task scheduler
        pass
    
    def record_app_usage(self, app_name: str):
        """Record that an app was used"""
        self.user_patterns.record_app_usage(app_name)
    
    def record_task(self, task_type: str):
        """Record a task type"""
        self.user_patterns.record_task(task_type)
    
    def get_user_patterns(self) -> Dict:
        """Get user pattern summary"""
        return self.user_patterns.get_summary()
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """Get recent alert history"""
        recent = [alert.to_dict() for alert in self.alert_history[-limit:]]
        return recent
    
    def get_status(self) -> Dict:
        """Get current proactive assistant status"""
        return {
            "enabled": self.enabled,
            "monitoring": self._running,
            "check_interval": self.check_interval,
            "total_alerts": len(self.alert_history),
            "recent_alerts": len(self.recent_alerts),
            "user_patterns": self.get_user_patterns(),
            "thresholds": self.thresholds,
        }
    
    def suggest_based_on_patterns(self) -> Optional[str]:
        """Generate suggestions based on user patterns"""
        patterns = self.get_user_patterns()
        
        # Suggest based on time of day
        peak_hours = patterns.get('peak_hours', [])
        current_hour = datetime.now().hour
        
        if peak_hours and current_hour in peak_hours:
            frequent_apps = patterns.get('frequent_apps', [])
            if frequent_apps:
                return (f"I notice you typically work with {', '.join(frequent_apps[:3])} "
                       f"at this time. Would you like me to open any of these?")
        
        # Suggest based on common tasks
        common_tasks = patterns.get('common_tasks', [])
        if common_tasks and patterns['total_interactions'] > 10:
            return (f"Based on your recent activity, you often use: {', '.join(common_tasks[:3])}. "
                   f"Need help with any of these?")
        
        return None
