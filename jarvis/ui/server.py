"""
Web Server - Starlette app with WebSocket support for JARVIS
"""

import json
import asyncio
import logging
import math
from datetime import datetime
from typing import Dict, Set
from pathlib import Path
from dataclasses import asdict

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from jarvis.brain.router import CommandRouter, Command
from jarvis.brain.scheduler import TaskScheduler
from jarvis.brain.learning import LearningAI, MemoryEntry
from jarvis.brain.internet_learning import InternetLearner
from jarvis.brain.local_learning import LocalLearningAI
from jarvis.brain.conversation import ConversationEngine
from jarvis.tools.cloud_sync import CloudSync
from jarvis.tools.cloud_sync_client import CloudSyncClient
from jarvis.database.sqlite_db import SQLiteDB

# Windows-only imports — gracefully handle missing packages on Linux (cloud mode)
try:
    from jarvis.tools.system import SystemControl
except ImportError:
    SystemControl = None

try:
    from jarvis.tools.voice import VoiceControl
except ImportError:
    VoiceControl = None

try:
    from jarvis.tools.files import FileAssistant
except ImportError:
    FileAssistant = None

try:
    from jarvis.tools.power import PowerMonitor
except ImportError:
    PowerMonitor = None

logger = logging.getLogger('JARVIS.ui.server')

# Global state
active_connections: Set[WebSocket] = set()
jarvis_state = {}


def create_app(config: Dict):
    """Create and configure the Starlette application"""
    
    # Detect mode: "local" (full system control) or "cloud" (AI brain only)
    mode = config.get('mode', 'local')
    jarvis_state['mode'] = mode
    logger.info(f"JARVIS starting in {mode} mode")
    
    # Initialize SQLite database
    sqlite_db = SQLiteDB(config)
    jarvis_state['sqlite_db'] = sqlite_db
    
    # Initialize components
    router = CommandRouter(config)
    scheduler = TaskScheduler(config)
    learning_ai = LearningAI(config, sqlite_db=sqlite_db)
    
    # Mode-based initialization
    if mode == 'local':
        # Local mode: full system control + cloud sync
        try:
            system = SystemControl(config) if SystemControl else None
        except Exception as e:
            logger.warning(f"SystemControl failed to initialize: {e}")
            system = None
        try:
            voice = VoiceControl(config) if VoiceControl else None
        except Exception as e:
            logger.warning(f"VoiceControl failed to initialize: {e}")
            voice = None
        try:
            files = FileAssistant(config) if FileAssistant else None
        except Exception as e:
            logger.warning(f"FileAssistant failed to initialize: {e}")
            files = None
        try:
            power_monitor = PowerMonitor() if PowerMonitor else None
        except Exception as e:
            logger.warning(f"PowerMonitor failed to initialize: {e}")
            power_monitor = None
        jarvis_state['system'] = system
        jarvis_state['voice'] = voice
        jarvis_state['files'] = files
        jarvis_state['power_monitor'] = power_monitor
    else:
        # Cloud mode: no system control tools
        system = None
        voice = None
        files = None
        power_monitor = None
        logger.info("Cloud mode: system control tools disabled")
    
    # Initialize internet learner
    internet_learner = InternetLearner(
        config=config,
        learning_ai=learning_ai,
        power_monitor=power_monitor,
        sqlite_db=sqlite_db
    )
    
    # Initialize local learning AI
    local_learning = LocalLearningAI(config, learning_ai=learning_ai, sqlite_db=sqlite_db)
    
    # Initialize cloud sync (database sync)
    cloud_sync = CloudSync(
        sqlite_db=sqlite_db,
        learning_ai=learning_ai,
        local_learning=local_learning,
        internet_learner=internet_learner
    )
    jarvis_state['cloud_sync'] = cloud_sync
    
    # Initialize cloud sync client (HTTP sync with cloud JARVIS) - local mode only
    cloud_sync_client = None
    if mode == 'local':
        cloud_sync_client = CloudSyncClient(
            config=config,
            learning_ai=learning_ai,
            internet_learner=internet_learner
        )
        jarvis_state['cloud_sync_client'] = cloud_sync_client
    
    # Attach learning AI to router
    router.set_learning_ai(learning_ai)
    router.set_local_learning(local_learning)
    
    # Initialize conversation engine
    conversation_engine = ConversationEngine(
        config=config,
        learning_ai=learning_ai,
        internet_learner=internet_learner,
        local_learning=local_learning
    )
    jarvis_state['conversation_engine'] = conversation_engine
    
    # Store in global state
    jarvis_state['router'] = router
    jarvis_state['scheduler'] = scheduler
    jarvis_state['learning_ai'] = learning_ai
    jarvis_state['local_learning'] = local_learning
    jarvis_state['internet_learner'] = internet_learner
    
    # Register handlers
    _register_handlers(router, system, voice, files, scheduler, learning_ai, local_learning, internet_learner, power_monitor)
    
    # Start scheduler
    scheduler.start()
    
    # Start internet learning background loop immediately on server startup
    if internet_learner and internet_learner.enabled:
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_in_executor(None, lambda: None)  # warm up
        # Use a thread to start the async task
        import threading
        def start_learning_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_start_learning(internet_learner))
        threading.Thread(target=start_learning_loop, daemon=True).start()
        logger.info("Internet learning background loop started at server startup")
    
    # Start cloud sync client in local mode
    if cloud_sync_client and cloud_sync_client.enabled:
        cloud_sync_client.start()
        logger.info("Cloud sync client started")
    
    # Health check endpoint for Render.com
    def health_check(request):
        return JSONResponse({"status": "ok", "mode": mode})
    
    # Define routes
    routes = [
        Route("/healthz", endpoint=health_check),
        Route("/", endpoint=index),
        Route("/api/status", endpoint=get_status),
        Route("/api/system", endpoint=get_system_info),
        Route("/api/reminders", endpoint=get_reminders),
        Route("/api/voice/status", endpoint=get_voice_status),
        Route("/api/voice/toggle", endpoint=toggle_voice_speak, methods=["POST"]),
        Route("/api/learning/stats", endpoint=get_learning_stats),
        Route("/api/learning/memory", endpoint=get_learning_memory),
        Route("/api/learning/forget", endpoint=forget_memory),
        Route("/api/local-learning/status", endpoint=get_local_learning_status),
        Route("/api/local-learning/scan", endpoint=trigger_local_scan),
        Route("/api/local-learning/entities", endpoint=get_local_entities),
        Route("/api/local-learning/entity", endpoint=get_entity_info),
        Route("/api/internet-learning/status", endpoint=get_internet_learning_status),
        Route("/api/internet-learning/trigger", endpoint=trigger_internet_learning),
        Route("/api/power/status", endpoint=get_power_status),
        Route("/api/sync/status", endpoint=get_sync_status),
        Route("/api/sync/trigger", endpoint=trigger_sync, methods=["POST"]),
        Route("/api/sync/export", endpoint=export_memories),
        Route("/api/sync/import", endpoint=import_memories, methods=["POST"]),
        Route("/api/cloud-sync/status", endpoint=get_cloud_sync_status),
        Route("/api/cloud-sync/trigger", endpoint=trigger_cloud_sync, methods=["POST"]),
        WebSocketRoute("/ws", endpoint=websocket_endpoint),
    ]
    
    app = Starlette(routes=routes)
    return app


def _register_handlers(router, system, voice, files, scheduler, learning_ai, local_learning=None, internet_learner=None, power_monitor=None):
    """Register command handlers"""
    
    # Greetings - varied responses from conversation engine
    def handle_greet(cmd):
        conv_engine = jarvis_state.get('conversation_engine')
        if conv_engine:
            return conv_engine.get_greeting()
        return "Hello! How can I help you?"
    router.register_handler("greet", handle_greet)
    
    # Time
    def handle_time(cmd):
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}."
    router.register_handler("time", handle_time)
    
    # Date
    def handle_date(cmd):
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    router.register_handler("date", handle_date)
    
    # Volume (local mode only)
    if system:
        router.register_handler("volume_up", lambda cmd: system.volume_up())
        router.register_handler("volume_down", lambda cmd: system.volume_down())
        router.register_handler("volume_mute", lambda cmd: system.mute_volume())
        router.register_handler("volume_set", lambda cmd: system.set_volume(cmd.parameters.get('level', 50)))
        
        # Apps
        router.register_handler("open_app", lambda cmd: system.open_app(cmd.parameters.get('app_name', '')))
        router.register_handler("close_app", lambda cmd: system.close_app(cmd.parameters.get('app_name', '')))
        
        def handle_list_apps(cmd):
            processes = system.get_running_processes()
            if not processes:
                return "Unable to get process list."
            result = "Top running processes:\n"
            for p in processes[:10]:
                result += f"  {p['name']} (CPU: {p['cpu']}, RAM: {p['memory']})\n"
            return result.strip()
        router.register_handler("list_apps", handle_list_apps)
        
        router.register_handler("open_folder", lambda cmd: system.open_folder(cmd.parameters.get('folder', '')))
    else:
        # Cloud mode placeholders
        def cloud_not_available(cmd):
            return "This feature is only available in local mode."
        for handler in ["volume_up", "volume_down", "volume_mute", "volume_set", "open_app", "close_app", "list_apps", "open_folder"]:
            router.register_handler(handler, cloud_not_available)
    
    # Files (local mode only)
    if files:
        router.register_handler("open_file", lambda cmd: files.open_file(cmd.parameters.get('query', '')))
        
        def handle_search_files(cmd):
            query = cmd.parameters.get('query', '')
            results = files.search_files(query)
            if not results:
                return f"No files found matching '{query}'."
            result = f"Found {len(results)} files:\n"
            for f in results[:10]:
                result += f"  {f['name']} ({f['size']}) - {f['path']}\n"
            return result.strip()
        router.register_handler("search_files", handle_search_files)
        
        def handle_list_files(cmd):
            directory = cmd.parameters.get('folder')
            results = files.list_files(directory)
            if not results:
                return f"No files found or directory not accessible."
            result = f"Files in directory:\n"
            for f in results[:20]:
                icon = "📁" if f['is_directory'] else "📄"
                result += f"  {icon} {f['name']} ({f['size']})\n"
            return result.strip()
        router.register_handler("list_files", handle_list_files)
    else:
        # Cloud mode placeholders for file handlers
        def cloud_not_available(cmd):
            return "This feature is only available in local mode."
        for handler in ["open_file", "search_files", "list_files"]:
            router.register_handler(handler, cloud_not_available)
    
    # System info (local mode only)
    if system:
        def handle_system_info(cmd):
            info = system.get_system_info()
            lines = [f"System Information:"]
            lines.append(f"  Platform: {info.get('platform', 'N/A')} {info.get('platform_version', '')}")
            lines.append(f"  Processor: {info.get('processor', 'N/A')}")
            lines.append(f"  CPU: {info.get('cpu_cores', '?')} cores, {info.get('cpu_usage', '?')} usage")
            lines.append(f"  RAM: {info.get('ram_usage', '?')} used, {info.get('available_ram', '?')} free")
            lines.append(f"  Disk: {info.get('disk_usage', '?')} used, {info.get('free_disk', '?')} free")
            if info.get('has_battery'):
                lines.append(f"  Battery: {info.get('battery_percent', '?')}")
            return "\n".join(lines)
        router.register_handler("system_info", handle_system_info)
        
        def handle_system_status(cmd):
            info = system.get_system_info()
            cpu = system.get_cpu_usage()
            mem = system.get_memory_usage()
            disk = system.get_disk_space()
            lines = ["System Status Overview:"]
            lines.append(f"  Platform: {info.get('platform', 'N/A')} {info.get('platform_version', '')}")
            lines.append(f"  CPU: {cpu}")
            lines.append(f"  Memory: {mem}")
            lines.append(f"  Disk: {disk}")
            if 'battery_percent' in info:
                lines.append(f"  Battery: {info.get('battery_percent', '?')}%")
            lines.append(f"  JARVIS: Running and operational")
            return "\n".join(lines)
        router.register_handler("system_status", handle_system_status)
        
        router.register_handler("cpu_usage", lambda cmd: system.get_cpu_usage())
        router.register_handler("memory_usage", lambda cmd: system.get_memory_usage())
        router.register_handler("disk_space", lambda cmd: system.get_disk_space())
        router.register_handler("battery", lambda cmd: system.get_battery_status())
        
        router.register_handler("web_search", lambda cmd: system.web_search(cmd.parameters.get('query', '')))
        router.register_handler("open_url", lambda cmd: system.open_url(cmd.parameters.get('url', '')))
    else:
        # Cloud mode placeholders for system handlers
        def cloud_not_available(cmd):
            return "This feature is only available in local mode."
        for handler in ["system_info", "system_status", "cpu_usage", "memory_usage", "disk_space", "battery", "web_search", "open_url"]:
            router.register_handler(handler, cloud_not_available)
    
    # Reminders
    def handle_set_reminder(cmd):
        raw = cmd.raw
        # Try to extract time
        time_expr = None
        for keyword in ['in ', 'at ', 'tomorrow']:
            if keyword in raw.lower():
                time_expr = raw.lower().split(keyword, 1)[1].strip()
                break
        
        if time_expr:
            trigger = scheduler.parse_time_expression(time_expr)
            if trigger:
                message = raw.split('reminder')[-1].strip() if 'reminder' in raw else raw
                message = message.lstrip('to ,')
                if not message:
                    message = "Untitled reminder"
                reminder = scheduler.add_reminder(message, trigger)
                return f"Reminder set: '{message}' at {trigger.strftime('%I:%M %p on %A')}."
        
        return "I couldn't understand the time. Try: 'remind me in 30 minutes' or 'remind me at 3 PM'"
    router.register_handler("set_reminder", handle_set_reminder)
    
    def handle_list_reminders(cmd):
        reminders = scheduler.get_reminders()
        if not reminders:
            return "No pending reminders."
        result = f"You have {len(reminders)} pending reminder(s):\n"
        for r in reminders:
            trigger = r.trigger_datetime().strftime('%I:%M %p on %A')
            result += f"  • {r.message} (at {trigger})\n"
        return result.strip()
    router.register_handler("list_reminders", handle_list_reminders)
    
    def handle_delete_reminder(cmd):
        reminders = scheduler.get_reminders()
        if not reminders:
            return "No reminders to delete."
        # Delete oldest
        oldest = reminders[0]
        scheduler.delete_reminder(oldest.id)
        return f"Deleted reminder: '{oldest.message}'"
    router.register_handler("delete_reminder", handle_delete_reminder)
    
    # Calculator
    def handle_calculate(cmd):
        expr = cmd.parameters.get('expression', '')
        try:
            # Safe evaluation
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expr):
                result = eval(expr)
                return f"{expr} = {result}"
            else:
                return "Invalid expression."
        except Exception as e:
            return f"Calculation error: {e}"
    router.register_handler("calculate", handle_calculate)
    
    # Math expression (natural language: "what is 25 * 4")
    def handle_math_expression(cmd):
        expr = cmd.parameters.get('expression', '')
        try:
            # Safe evaluation
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expr):
                result = eval(expr)
                return f"{expr} = {result}"
            else:
                return "Invalid expression."
        except Exception as e:
            return f"Calculation error: {e}"
    router.register_handler("math_expression", handle_math_expression)
    
    # Weather (simple response)
    def handle_weather(cmd):
        location = cmd.parameters.get('location', 'your area')
        return f"I don't have real-time weather data yet, but you can check weather for {location} online. I can open a weather website for you — just say 'search weather {location}'."
    router.register_handler("weather", handle_weather)
    
    # Jokes
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the developer go broke? Because he used up all his cache!",
        "What's a programmer's favorite hangout place? Foo Bar!",
        "Why do Java developers wear glasses? Because they can't C#!",
        "I changed my password to 'incorrect' so when I forget it, the computer tells me: 'Your password is incorrect.'",
        "There are only 10 types of people in the world: those who understand binary and those who don't.",
        "A SQL query walks into a bar, sees two tables, and asks: 'Can I JOIN you?'",
    ]
    
    def handle_joke(cmd):
        import random
        return random.choice(jokes)
    router.register_handler("joke", handle_joke)
    
    # Quotes
    quotes = [
        "The only way to do great work is to love what you do. — Steve Jobs",
        "In the middle of difficulty lies opportunity. — Albert Einstein",
        "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
        "It does not matter how slowly you go as long as you do not stop. — Confucius",
        "Everything you've ever wanted is on the other side of fear. — George Addair",
    ]
    
    def handle_quote(cmd):
        import random
        return random.choice(quotes)
    router.register_handler("quote", handle_quote)
    
    # Help
    def handle_help(cmd):
        stats = learning_ai.get_stats()
        return f"""I can help you with:
  🕐 Time & Date — "what time is it", "what's the date"
  🔊 Volume — "volume up", "volume down", "mute"
  💻 Apps — "open Chrome", "close notepad", "list apps"
  📁 Files — "search for report", "open documents", "list files"
  📊 System — "system info", "CPU usage", "battery status"
  🔍 Web — "search Python tutorial", "open google.com"
  ⏰ Reminders — "remind me in 30 minutes", "list reminders"
  🧮 Calculator — "calculate 25 * 4", "what is 100 / 7"
  😄 Fun — "tell me a joke", "give me a quote"
  🧠 Learn — "teach me Python is a programming language", "remember that AI is artificial intelligence"
  
  My brain stats: {stats['total_memories']} memories, {stats['total_patterns']} patterns learned
  Say 'help' anytime for this message!"""
    router.register_handler("help", handle_help)
    
    # Goodbye - varied responses
    def handle_goodbye(cmd):
        conv_engine = jarvis_state.get('conversation_engine')
        if conv_engine:
            return conv_engine.get_goodbye()
        return "Goodbye! Have a great day."
    router.register_handler("goodbye", handle_goodbye)
    
    # Internet learning commands
    if internet_learner:
        def handle_learn_now(cmd):
            asyncio.create_task(_run_learning_session(internet_learner))
            return "Starting internet learning session... I'll fetch new knowledge from Wikipedia. Check back in a moment!"
        router.register_handler("learn_now", handle_learn_now)
        
        def handle_learning_status(cmd):
            status = internet_learner.get_status()
            lines = ["Internet Learning Status:"]
            lines.append(f"  Enabled: {'Yes' if status['enabled'] else 'No'}")
            lines.append(f"  Topics learned: {status['learned_topics']}")
            lines.append(f"  Currently learning: {'Yes' if status['is_learning'] else 'No'}")
            lines.append(f"  Can learn now: {status['reason']}")
            if status['stats']['total_sessions'] > 0:
                lines.append(f"  Total sessions: {status['stats']['total_sessions']}")
                lines.append(f"  Total facts learned: {status['stats']['total_facts_learned']}")
            return "\n".join(lines)
        router.register_handler("learning_status", handle_learning_status)
    
    # Power status command
    if power_monitor:
        def handle_power_status(cmd):
            info = power_monitor.get_status_dict()
            lines = ["Power Status:"]
            lines.append(f"  State: {info.get('state', 'unknown')}")
            lines.append(f"  Battery: {info.get('percent', '?')}%")
            lines.append(f"  Plugged in: {'Yes' if info.get('plugged') else 'No'}")
            if info.get('time_left'):
                lines.append(f"  Time remaining: {info['time_left']}")
            lines.append(f"  Internet learning: {'Active' if info.get('is_on_power') else 'Paused (on battery)'}")
            return "\n".join(lines)
        router.register_handler("power_status", handle_power_status)
    
    # Local learning commands
    if local_learning:
        def handle_local_status(cmd):
            summary = local_learning.get_learning_summary()
            lines = ["Local AI Learning Status:"]
            lines.append(f"  Enabled: {'Yes' if summary['enabled'] else 'No'}")
            lines.append(f"  Word network: {summary['word_network_size']} words")
            lines.append(f"  Entities known: {summary['entity_count']}")
            lines.append(f"  Preferences learned: {summary['preference_count']}")
            lines.append(f"  Interactions learned: {summary['stats']['total_interactions_learned']}")
            lines.append(f"  Files scanned: {summary['stats']['total_files_scanned']}")
            entities = summary.get('entities', {})
            if any(entities.values()):
                lines.append(f"  People: {entities.get('people', 0)}, Projects: {entities.get('projects', 0)}, Places: {entities.get('places', 0)}")
            return "\n".join(lines)
        router.register_handler("local_status", handle_local_status)
        
        def handle_scan_files(cmd):
            directory = cmd.parameters.get('directory', '')
            result = local_learning.scan_local_files(directory if directory else None)
            if result.get('status') == 'completed':
                return f"File scan complete: {result['files_scanned']} files scanned, {result['knowledge_extracted']} knowledge entries extracted."
            return f"Scan failed: {result.get('message', 'Unknown error')}"
        router.register_handler("scan_files", handle_scan_files)
        
        def handle_who_is(cmd):
            name = cmd.parameters.get('name', '')
            if not name:
                return "Who would you like to know about? Try: 'who is John' or 'tell me about my project'"
            
            # Check entities
            entity_info = local_learning.get_entity_info(name)
            if entity_info:
                return f"I know {entity_info['name']} ({entity_info['entity_type']}). Mentioned {entity_info['mentions']} time(s). Context: {entity_info['context'][:200]}"
            
            # Search entities
            entities = local_learning.entity_extractor.search_entities(name)
            if entities:
                entity = entities[0]
                return f"I found {entity.name} ({entity.entity_type}). Context: {entity.context[:200]}"
            
            return f"I don't know about '{name}' yet. Tell me about them and I'll remember!"
        router.register_handler("who_is", handle_who_is)
    
    # Cloud sync commands (local mode only)
    def handle_cloud_sync_status(cmd):
        cloud_sync_client = jarvis_state.get('cloud_sync_client')
        if cloud_sync_client:
            status = cloud_sync_client.get_status()
            lines = ["Cloud Sync Status:"]
            lines.append(f"  Enabled: {'Yes' if status['enabled'] else 'No'}")
            lines.append(f"  Cloud URL: {status['cloud_url']}")
            lines.append(f"  Running: {'Yes' if status['is_running'] else 'No'}")
            lines.append(f"  Sync interval: {status['sync_interval_minutes']} minutes")
            lines.append(f"  Syncs completed: {status['sync_count']}")
            if status['last_sync']:
                lines.append(f"  Last sync: {status['last_sync']}")
            if status['last_result']:
                result = status['last_result']
                lines.append(f"  Last result: {result.get('message', 'N/A')}")
            return "\n".join(lines)
        return "Cloud sync is not available in cloud mode."
    router.register_handler("cloud_sync_status", handle_cloud_sync_status)
    
    def handle_cloud_sync_now(cmd):
        cloud_sync_client = jarvis_state.get('cloud_sync_client')
        if cloud_sync_client:
            result = cloud_sync_client.sync_now()
            if result.get('status') == 'success':
                return f"Cloud sync complete! {result.get('message', 'Synced successfully')}"
            return f"Cloud sync failed: {result.get('message', 'Unknown error')}"
        return "Cloud sync is not available."
    router.register_handler("cloud_sync_now", handle_cloud_sync_now)


async def index(request):
    """Serve the main HTML page"""
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>JARVIS</h1><p>Interface not found. Place index.html in the ui/ directory.</p>")


async def get_status(request):
    """Get JARVIS status"""
    return JSONResponse({
        'status': 'online',
        'connections': len(active_connections),
        'time': datetime.now().isoformat(),
    })


async def get_system_info(request):
    """Get system information"""
    system = jarvis_state.get('system')
    if system:
        return JSONResponse(system.get_system_info())
    return JSONResponse({'error': 'System not initialized'})


async def get_reminders(request):
    """Get pending reminders"""
    scheduler = jarvis_state.get('scheduler')
    if scheduler:
        reminders = scheduler.get_reminders()
        return JSONResponse([{
            'id': r.id,
            'message': r.message,
            'trigger_time': r.trigger_time,
            'is_completed': r.is_completed,
        } for r in reminders])
    return JSONResponse([])


async def get_voice_status(request):
    """Get voice feature status"""
    voice = jarvis_state.get('voice')
    if voice:
        return JSONResponse(voice.is_available())
    return JSONResponse({'error': 'Voice not initialized'})


async def toggle_voice_speak(request):
    """Toggle text-to-speech on/off"""
    voice = jarvis_state.get('voice')
    if voice:
        try:
            data = await request.json()
            enabled = data.get('enabled', not voice.speak_enabled)
            voice.toggle_speak(enabled)
            return JSONResponse({'success': True, 'speak_enabled': voice.speak_enabled})
        except Exception as e:
            return JSONResponse({'success': False, 'error': str(e)})
    return JSONResponse({'error': 'Voice not initialized'})


async def get_learning_stats(request):
    """Get learning AI statistics"""
    learning_ai = jarvis_state.get('learning_ai')
    if learning_ai:
        stats = learning_ai.get_stats()
        return JSONResponse(stats)
    return JSONResponse({'error': 'Learning AI not initialized'})


async def get_learning_memory(request):
    """Get learned memory entries"""
    learning_ai = jarvis_state.get('learning_ai')
    if learning_ai:
        limit = request.query_params.get('limit', '20')
        limit = int(limit)
        memory = learning_ai.get_recent_learnings(limit)
        return JSONResponse({'memories': memory, 'count': len(memory)})
    return JSONResponse({'memories': [], 'count': 0})


async def forget_memory(request):
    """Forget a learned memory entry"""
    learning_ai = jarvis_state.get('learning_ai')
    if learning_ai:
        try:
            data = await request.json()
            entry_id = data.get('id', '')
            if entry_id and learning_ai.forget(entry_id):
                return JSONResponse({'success': True, 'message': f'Forgot memory: {entry_id}'})
            return JSONResponse({'success': False, 'message': 'Memory not found'})
        except Exception as e:
            return JSONResponse({'success': False, 'message': str(e)})
    return JSONResponse({'error': 'Learning AI not initialized'})


async def get_local_learning_status(request):
    """Get local AI learning status"""
    local_learning = jarvis_state.get('local_learning')
    if local_learning:
        return JSONResponse(local_learning.get_learning_summary())
    return JSONResponse({'error': 'Local learning not initialized'})


async def trigger_local_scan(request):
    """Trigger a local file scan"""
    local_learning = jarvis_state.get('local_learning')
    if local_learning:
        try:
            data = await request.json()
            directory = data.get('directory', '')
            result = local_learning.scan_local_files(directory if directory else None)
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({'status': 'error', 'message': str(e)})
    return JSONResponse({'error': 'Local learning not initialized'})


async def get_local_entities(request):
    """Get all known entities"""
    local_learning = jarvis_state.get('local_learning')
    if local_learning:
        entity_type = request.query_params.get('type', '')
        if entity_type:
            entities = local_learning.entity_extractor.get_entities_by_type(entity_type)
        else:
            entities = list(local_learning.entity_extractor.entities.values())
        return JSONResponse({
            'entities': [asdict(e) if hasattr(e, '__dataclass_fields__') else e for e in entities],
            'count': len(entities)
        })
    return JSONResponse({'entities': [], 'count': 0})


async def get_entity_info(request):
    """Get info about a specific entity"""
    local_learning = jarvis_state.get('local_learning')
    if local_learning:
        name = request.query_params.get('name', '')
        if name:
            info = local_learning.get_entity_info(name)
            if info:
                return JSONResponse(info)
            return JSONResponse({'error': f'Entity not found: {name}'})
        return JSONResponse({'error': 'Name parameter required'})
    return JSONResponse({'error': 'Local learning not initialized'})


async def get_power_status(request):
    """Get power/battery status"""
    power_monitor = jarvis_state.get('power_monitor')
    if power_monitor:
        return JSONResponse(power_monitor.get_status_dict())
    return JSONResponse({'error': 'Power monitor not initialized'})


async def get_sync_status(request):
    """Get cloud sync status"""
    cloud_sync = jarvis_state.get('cloud_sync')
    mode = jarvis_state.get('mode', 'local')
    learning_ai = jarvis_state.get('learning_ai')
    internet_learner = jarvis_state.get('internet_learner')
    local_learning = jarvis_state.get('local_learning')
    
    status = {
        'mode': mode,
        'database_connected': False,
        'memories_count': 0,
        'topics_learned': 0,
        'entities_count': 0,
        'words_count': 0,
        'last_sync': None
    }
    
    if cloud_sync:
        sync_status = cloud_sync.get_status()
        status['database_connected'] = sync_status.get('connected', False)
        status['last_sync'] = sync_status.get('last_sync')
        status['sync_count'] = sync_status.get('sync_count', 0)
    
    if learning_ai:
        status['memories_count'] = len(learning_ai.memory)
    
    if internet_learner:
        status['topics_learned'] = len(internet_learner.learned_topics)
    
    if local_learning:
        status['entities_count'] = len(local_learning.entity_extractor.entities)
        status['words_count'] = len(local_learning.word_network.network)
    
    return JSONResponse(status)


async def trigger_sync(request):
    """Trigger a manual cloud sync"""
    cloud_sync = jarvis_state.get('cloud_sync')
    if cloud_sync:
        result = cloud_sync.sync_all()
        return JSONResponse(result)
    return JSONResponse({'status': 'error', 'message': 'Cloud sync not available'})


async def export_memories(request):
    """Export all memories, local learning data, and internet learning data for sync"""
    learning_ai = jarvis_state.get('learning_ai')
    local_learning = jarvis_state.get('local_learning')
    internet_learner = jarvis_state.get('internet_learner')
    
    data = {
        'memories': [],
        'local_learning': None,
        'internet_learning': [],
        'stats': {},
        'timestamp': datetime.now().isoformat()
    }
    
    if learning_ai:
        data['memories'] = [asdict(m) for m in learning_ai.memory.values()]
        data['stats'] = learning_ai.get_stats()
    
    if local_learning:
        summary = local_learning.get_learning_summary()
        data['local_learning'] = summary
    
    if internet_learner:
        # Export learned topics with their summaries from learning AI memory
        topics_data = []
        if learning_ai:
            for mem_id, entry in learning_ai.memory.items():
                if entry.category and entry.category.startswith('internet_'):
                    topics_data.append({
                        'topic': entry.response.split(':')[0].strip().lower(),
                        'summary': entry.response,
                        'category': entry.category.replace('internet_', ''),
                        'learned_at': entry.created_at
                    })
        data['internet_learning'] = topics_data
    
    return JSONResponse(data)


async def import_memories(request):
    """Import memories from another JARVIS instance for sync"""
    learning_ai = jarvis_state.get('learning_ai')
    local_learning = jarvis_state.get('local_learning')
    internet_learner = jarvis_state.get('internet_learner')
    
    try:
        incoming = await request.json()
    except Exception:
        return JSONResponse({'success': False, 'error': 'Invalid JSON'}, status_code=400)
    
    imported = {'memories': 0, 'topics': 0, 'entities': 0}
    
    # Import memories
    if learning_ai and 'memories' in incoming:
        existing_ids = set(learning_ai.memory.keys())
        for item in incoming.get('memories', []):
            entry_id = item.get('id', '')
            if entry_id and entry_id not in existing_ids:
                # Filter out SQLite-specific fields
                clean_item = {k: v for k, v in item.items() if k in MemoryEntry.__dataclass_fields__}
                entry = MemoryEntry(**clean_item)
                learning_ai.memory[entry_id] = entry
                for pattern in entry.patterns:
                    learning_ai.matcher.add_document(pattern)
                imported['memories'] += 1
        if imported['memories'] > 0:
            learning_ai._save_memory()
            logger.info(f"Imported {imported['memories']} new memories from sync")
    
    # Import internet learning topics
    if internet_learner and 'internet_learning' in incoming:
        existing_topics = set(internet_learner.learned_topics.keys())
        for topic_data in incoming.get('internet_learning', []):
            if isinstance(topic_data, dict):
                topic = topic_data.get('topic', '')
                if topic and topic not in existing_topics:
                    internet_learner.learned_topics[topic] = topic_data
                    imported['topics'] += 1
        if imported['topics'] > 0:
            internet_learner._save_topics()
            logger.info(f"Imported {imported['topics']} new topics from sync")
    
    return JSONResponse({
        'success': True,
        'imported': imported,
        'message': f"Imported {imported['memories']} memories and {imported['topics']} topics"
    })


async def get_cloud_sync_status(request):
    """Get cloud sync client status"""
    cloud_sync_client = jarvis_state.get('cloud_sync_client')
    if cloud_sync_client:
        return JSONResponse(cloud_sync_client.get_status())
    return JSONResponse({'error': 'Cloud sync client not initialized', 'enabled': False})


async def trigger_cloud_sync(request):
    """Trigger an immediate cloud sync"""
    cloud_sync_client = jarvis_state.get('cloud_sync_client')
    if cloud_sync_client:
        result = cloud_sync_client.sync_now()
        return JSONResponse(result)
    return JSONResponse({'status': 'error', 'message': 'Cloud sync client not available'})


async def get_internet_learning_status(request):
    """Get internet learning status"""
    internet_learner = jarvis_state.get('internet_learner')
    if internet_learner:
        return JSONResponse(internet_learner.get_status())
    return JSONResponse({'error': 'Internet learner not initialized'})


async def trigger_internet_learning(request):
    """Manually trigger an internet learning session"""
    internet_learner = jarvis_state.get('internet_learner')
    if internet_learner:
        if internet_learner.is_learning:
            return JSONResponse({'status': 'learning', 'message': 'Already learning'})
        asyncio.create_task(_run_learning_session(internet_learner))
        return JSONResponse({'status': 'started', 'message': 'Learning session started'})
    return JSONResponse({'error': 'Internet learner not initialized'})


async def _start_learning(internet_learner):
    """Start the learning loop and run forever (for daemon thread)"""
    await _internet_learning_loop(internet_learner)


async def _run_learning_session(internet_learner):
    """Run a single learning session"""
    try:
        result = await internet_learner.learn_session()
        logger.info(f"Learning session result: {result}")
        
        # Broadcast result to connected clients
        await broadcast({
            'type': 'learning_update',
            'data': result
        })
    except Exception as e:
        logger.error(f"Learning session failed: {e}")


async def _internet_learning_loop(internet_learner):
    """Background loop that periodically checks and runs learning sessions"""
    while True:
        try:
            # Cloud mode: no power monitor, always use continuous interval
            # Local mode: use continuous interval only when on power
            is_on_power = True  # Default for cloud mode
            if internet_learner.power_monitor is not None:
                is_on_power = internet_learner.power_monitor.is_on_power()
            
            if internet_learner.continuous_loop and is_on_power:
                interval = internet_learner.continuous_loop_interval
                logger.debug(f"Continuous loop mode: checking every {interval}s")
            else:
                interval = 300  # 5 minutes default
            
            await asyncio.sleep(interval)
            
            if not internet_learner.enabled:
                continue
            
            can_learn, reason = internet_learner._can_learn()
            if can_learn:
                if internet_learner.continuous_loop:
                    logger.info("Continuous learning session triggered")
                else:
                    logger.info("Background learning triggered")
                await _run_learning_session(internet_learner)
            elif "cooldown" in reason.lower():
                pass  # Normal cooldown
            elif "not on power" in reason.lower():
                pass  # On battery, skip silently
        except Exception as e:
            logger.error(f"Internet learning loop error: {e}")
            await asyncio.sleep(60)  # Wait longer on error


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket connected. Total: {len(active_connections)}")
    
    # Create conversation context for this connection
    conv_engine = jarvis_state.get('conversation_engine')
    conv_context = None
    if conv_engine:
        conv_context = conv_engine.create_context()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse message
            try:
                message = json.loads(data)
                msg_type = message.get('type', 'command')
                text = message.get('text', '')
            except json.JSONDecodeError:
                msg_type = 'command'
                text = data
            
            if msg_type == 'command':
                response = await process_command(text, conv_context=conv_context)
                await websocket.send_json({
                    'type': 'response',
                    'text': response,
                    'timestamp': datetime.now().isoformat(),
                })
            
            elif msg_type == 'ping':
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat(),
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)


async def process_command(text: str, conv_context=None) -> str:
    """Process a command and return response"""
    router = jarvis_state.get('router')
    learning_ai = jarvis_state.get('learning_ai')
    local_learning = jarvis_state.get('local_learning')
    voice = jarvis_state.get('voice')
    conv_engine = jarvis_state.get('conversation_engine')
    
    if not router:
        return "System not initialized"
    
    # Process with conversation engine if available
    is_casual = False
    casual_response = None
    if conv_engine and conv_context:
        analysis = conv_engine.process_input(text, conv_context)
        is_casual = analysis['is_casual']
        casual_response = analysis['casual_response']
    
    # Always process with local learning AI for entity extraction and word network
    if local_learning:
        local_learning.word_network.add_sentence(text)
        entities = local_learning.entity_extractor.extract_from_text(text)
        if entities:
            local_learning.stats['total_entities_extracted'] += len(entities)
            local_learning.stats['total_interactions_learned'] += 1
            if local_learning.stats['total_interactions_learned'] % 10 == 0:
                local_learning._save_state()
    
    # Handle casual conversation first (before command matching)
    if is_casual and casual_response:
        if conv_context:
            conv_context.add_exchange(text, casual_response)
        if local_learning:
            local_learning.process_interaction(text, casual_response, was_successful=True)
        if voice:
            voice.speak_async(casual_response)
        return casual_response
    
    # Check for teach commands first
    teach_response = router.handle_teach_command(text)
    if teach_response:
        if conv_context:
            conv_context.add_exchange(text, teach_response)
        if local_learning:
            local_learning.process_interaction(text, teach_response, was_successful=True)
        if voice:
            voice.speak_async(teach_response)
        return teach_response
    
    # Parse command
    command = router.parse(text)
    if not command:
        response = "I didn't catch that. Could you repeat?"
        if voice:
            voice.speak_async(response)
        return response
    
    # Try rule-based execution first
    response = await router.execute(command)
    
    if response is not None:
        # Check if the response is an error from a bad match
        is_error = response.startswith("Sorry, I encountered an error") or \
                   response.startswith("Calculation error")
        
        if not is_error:
            # Wrap response with conversation engine
            if conv_engine and conv_context:
                response = conv_engine.wrap_response(response, conv_context, is_command=True)
                conv_context.add_exchange(text, response)
            
            # Auto-learn from successful interactions
            if learning_ai:
                learning_ai.auto_learn_from_interaction(text, response, was_successful=True)
                learning_ai.update_conversation_history(text, response)
            
            if local_learning:
                local_learning.process_interaction(text, response, was_successful=True)
            
            if voice:
                voice.speak_async(response)
            return response
        # If it's an error, fall through to try learning AI
    
    # Fallback: try local learning AI with context
    if local_learning:
        context_response = local_learning.answer_with_context(text)
        if context_response:
            if conv_context:
                conv_context.add_exchange(text, context_response)
            if local_learning:
                local_learning.process_interaction(text, context_response, was_successful=True)
            if voice:
                voice.speak_async(context_response)
            return context_response
    
    # Fallback: try learning AI memory
    if learning_ai:
        match = learning_ai.find_match(text)
        if match:
            entry, score = match
            learning_ai.record_success(entry.id)
            learning_ai.update_conversation_history(text, entry.response)
            if conv_context:
                conv_context.add_exchange(text, entry.response)
            if voice:
                voice.speak_async(entry.response)
            return entry.response
    
    # Last resort: use conversation engine for natural fallback
    if conv_engine and conv_context:
        response = conv_engine.generate_fallback(text, conv_context)
        conv_context.add_exchange(text, response)
        if voice:
            voice.speak_async(response)
        return response
    
    # Absolute last resort
    response = "I'm not sure about that. Try 'help' to see what I can do, or teach me something new!"
    if voice:
        voice.speak_async(response)
    return response


async def broadcast(message: dict):
    """Broadcast a message to all connected clients"""
    global active_connections
    disconnected = set()
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)
    
    # Clean up disconnected
    active_connections -= disconnected
