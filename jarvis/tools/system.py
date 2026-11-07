"""
System Control - Manage Windows system operations
"""

import os
import subprocess
import logging
import platform
from typing import Dict, List, Optional
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import ctypes
    from ctypes import wintypes
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

logger = logging.getLogger('JARVIS.tools.system')


class SystemControl:
    """Control system operations on Windows"""
    
    def __init__(self, config: Dict):
        self.config = config.get('system', {})
        self.allowed_apps = {app['name'].lower(): app['path'] for app in self.config.get('allowed_apps', [])}
        self.favorite_dirs = self.config.get('favorite_dirs', {})
        logger.info("SystemControl initialized")
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'username': os.getenv('USERNAME', 'Unknown'),
            'hostname': platform.node(),
        }
        
        if HAS_PSUTIL:
            # CPU info
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                info['cpu_freq'] = f"{cpu_freq.current/1000:.2f} GHz"
            info['cpu_cores'] = psutil.cpu_count(logical=False)
            info['cpu_logical'] = psutil.cpu_count(logical=True)
            info['cpu_usage'] = f"{psutil.cpu_percent(interval=1)}%"
            
            # Memory info
            mem = psutil.virtual_memory()
            info['total_ram'] = f"{mem.total / (1024**3):.1f} GB"
            info['available_ram'] = f"{mem.available / (1024**3):.1f} GB"
            info['ram_usage'] = f"{mem.percent}%"
            
            # Disk info
            disk = psutil.disk_usage('/')
            info['total_disk'] = f"{disk.total / (1024**3):.1f} GB"
            info['free_disk'] = f"{disk.free / (1024**3):.1f} GB"
            info['disk_usage'] = f"{disk.percent}%"
            
            # Battery (if laptop)
            battery = psutil.sensors_battery()
            if battery:
                info['has_battery'] = True
                info['battery_percent'] = f"{battery.percent}%"
                info['battery_plugged'] = battery.power_plugged
                if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                    hours = battery.secsleft // 3600
                    mins = (battery.secsleft % 3600) // 60
                    info['battery_time_left'] = f"{hours}h {mins}m"
        
        return info
    
    def get_cpu_usage(self) -> str:
        """Get current CPU usage"""
        if HAS_PSUTIL:
            usage = psutil.cpu_percent(interval=1)
            per_cpu = psutil.cpu_percent(interval=1, percpu=True)
            return f"CPU usage: {usage}% (per core: {per_cpu})"
        return "psutil not available"
    
    def get_memory_usage(self) -> str:
        """Get current memory usage"""
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            return (f"RAM: {mem.percent}% used, "
                    f"{mem.available / (1024**3):.1f} GB available of "
                    f"{mem.total / (1024**3):.1f} GB total")
        return "psutil not available"
    
    def get_disk_space(self) -> str:
        """Get disk space information"""
        if HAS_PSUTIL:
            parts = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    parts.append(
                        f"{part.device}: {usage.free / (1024**3):.1f} GB free of "
                        f"{usage.total / (1024**3):.1f} GB ({usage.percent}% used)"
                    )
                except PermissionError:
                    continue
            return "\n".join(parts) if parts else "No disk info available"
        return "psutil not available"
    
    def get_battery_status(self) -> str:
        """Get battery status"""
        if HAS_PSUTIL:
            battery = psutil.sensors_battery()
            if battery:
                status = "Charging" if battery.power_plugged else "Discharging"
                return f"Battery: {battery.percent}%, {status}"
            return "No battery detected (desktop PC)"
        return "psutil not available"
    
    def get_running_processes(self) -> List[Dict]:
        """Get list of running processes"""
        if not HAS_PSUTIL:
            return []
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': f"{proc.info['cpu_percent'] or 0:.1f}%",
                    'memory': f"{proc.info['memory_percent'] or 0:.1f}%"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:20]  # Top 20
    
    def open_app(self, app_name: str) -> str:
        """Open an application"""
        app_name = app_name.lower().strip()
        
        # Check allowed apps
        if app_name in self.allowed_apps:
            app_path = self.allowed_apps[app_name]
            if os.path.exists(app_path):
                try:
                    subprocess.Popen([app_path])
                    return f"Opening {app_name}..."
                except Exception as e:
                    return f"Error opening {app_name}: {e}"
            else:
                return f"Application not found at: {app_path}"
        
        # Try common Windows commands
        common_commands = {
            'notepad': 'notepad',
            'calculator': 'calc',
            'paint': 'mspaint',
            'terminal': 'powershell',
            'cmd': 'cmd',
            'explorer': 'explorer',
            'chrome': 'chrome',
            'firefox': 'firefox',
        }
        
        if app_name in common_commands:
            try:
                subprocess.Popen([common_commands[app_name]])
                return f"Opening {app_name}..."
            except Exception as e:
                return f"Error opening {app_name}: {e}"
        
        return f"Unknown application: {app_name}. Allowed apps: {', '.join(self.allowed_apps.keys())}"
    
    def close_app(self, app_name: str) -> str:
        """Close an application"""
        if not HAS_PSUTIL:
            return "Process management not available"
        
        app_name = app_name.lower().strip()
        closed = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_name in proc.info['name'].lower():
                    proc.kill()
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed > 0:
            return f"Closed {closed} process(es) matching '{app_name}'"
        return f"No running process found matching '{app_name}'"
    
    def set_volume(self, level: int) -> str:
        """Set system volume (0-100)"""
        level = max(0, min(100, level))
        
        # Use Windows API
        if HAS_WIN32:
            try:
                # Send volume set key event
                ctypes.windll.winmm.audioMessageW = 0
            except Exception:
                pass
        
        # Fallback: use PowerShell
        try:
            subprocess.run(
                ['powershell', '-Command',
                 f'$wsh = New-Object -ComObject WScript.Shell; '
                 f'for ($i=0; $i -lt {"{0}" if level < 50 else "1"}; $i++) '
                 f'{{ $wsh.SendKeys("{chr(0xB1) if level < 50 else chr(0xAE)}") }}'],
                capture_output=True, timeout=5
            )
            return f"Volume set to {level}%"
        except Exception as e:
            return f"Could not set volume: {e}"
    
    def volume_up(self) -> str:
        """Increase volume"""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys("' + chr(0xAE) + '")'],
                capture_output=True, timeout=5
            )
            return "Volume increased"
        except Exception:
            return "Could not increase volume"
    
    def volume_down(self) -> str:
        """Decrease volume"""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys("' + chr(0xB1) + '")'],
                capture_output=True, timeout=5
            )
            return "Volume decreased"
        except Exception:
            return "Could not decrease volume"
    
    def mute_volume(self) -> str:
        """Mute/unmute volume"""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys("' + chr(0xAD) + '")'],
                capture_output=True, timeout=5
            )
            return "Volume toggled"
        except Exception:
            return "Could not toggle volume"
    
    def open_folder(self, folder_name: str) -> str:
        """Open a folder"""
        folder_name = folder_name.lower().strip()
        
        # Check favorite directories
        if folder_name in self.favorite_dirs:
            folder_path = self.favorite_dirs[folder_name]
            if os.path.exists(folder_path):
                os.startfile(folder_path)
                return f"Opening {folder_name}..."
            else:
                return f"Folder not found: {folder_path}"
        
        # Try to find the folder
        for name, path in self.favorite_dirs.items():
            if folder_name in name.lower():
                if os.path.exists(path):
                    os.startfile(path)
                    return f"Opening {name}..."
        
        return f"Unknown folder: {folder_name}. Available: {', '.join(self.favorite_dirs.keys())}"
    
    def open_url(self, url: str) -> str:
        """Open a URL in default browser"""
        try:
            import webbrowser
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return f"Opening {url}..."
        except Exception as e:
            return f"Error opening URL: {e}"
    
    def web_search(self, query: str) -> str:
        """Search the web"""
        try:
            import webbrowser
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching for '{query}' on Google..."
        except Exception as e:
            return f"Error searching: {e}"
