"""
Power Monitor - Detects laptop power state and battery status.
Uses psutil to monitor whether the laptop is plugged in and battery level.
"""

import logging
import psutil
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('JARVIS.tools.power')


class PowerState(Enum):
    """Power state enumeration"""
    ON_POWER = "on_power"       # Plugged in, charging or fully charged
    ON_BATTERY = "on_battery"   # Running on battery
    CHARGING = "charging"       # Plugged in and charging
    FULLY_CHARGED = "fully_charged"  # Plugged in and fully charged
    UNKNOWN = "unknown"         # No battery detected (desktop)


@dataclass
class PowerInfo:
    """Power status information"""
    state: PowerState
    percent: int  # Battery percentage
    plugged: bool  # Is power cable connected
    seconds_left: Optional[int]  # Seconds until empty/full (None if unlimited)
    charging: bool  # Is currently charging
    
    @property
    def is_on_power(self) -> bool:
        """Check if the device is connected to power"""
        return self.state in (PowerState.ON_POWER, PowerState.CHARGING, PowerState.FULLY_CHARGED)
    
    @property
    def time_left_text(self) -> Optional[str]:
        """Human-readable time remaining"""
        if self.seconds_left is None or self.seconds_left == psutil.POWER_TIME_UNLIMITED:
            return None
        hours = self.seconds_left // 3600
        mins = (self.seconds_left % 3600) // 60
        return f"{hours}h {mins}m"


class PowerMonitor:
    """Monitor laptop power state for conditional operations"""
    
    def __init__(self):
        self._has_battery = False
        self._last_info: Optional[PowerInfo] = None
        self._check_battery()
        logger.info(f"PowerMonitor initialized (has_battery: {self._has_battery})")
    
    def _check_battery(self) -> Optional[PowerInfo]:
        """Check current battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                self._has_battery = False
                self._last_info = PowerInfo(
                    state=PowerState.UNKNOWN,
                    percent=100,
                    plugged=True,
                    seconds_left=None,
                    charging=False
                )
                return self._last_info
            
            self._has_battery = True
            
            # Determine power state
            if battery.power_plugged:
                if battery.percent == 100:
                    state = PowerState.FULLY_CHARGED
                elif battery.secsleft == psutil.POWER_TIME_UNLIMITED:
                    state = PowerState.ON_POWER
                else:
                    state = PowerState.CHARGING
            else:
                state = PowerState.ON_BATTERY
            
            self._last_info = PowerInfo(
                state=state,
                percent=battery.percent,
                plugged=battery.power_plugged,
                seconds_left=battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                charging=battery.power_plugged and battery.percent < 100
            )
            return self._last_info
            
        except Exception as e:
            logger.error(f"Error checking battery: {e}")
            return None
    
    def get_status(self) -> PowerInfo:
        """Get current power status (refreshes data)"""
        return self._check_battery()
    
    def is_on_power(self) -> bool:
        """Check if currently on power (not battery)"""
        info = self._check_battery()
        if info is None:
            return True  # Assume desktop if can't detect
        return info.is_on_power
    
    def has_battery(self) -> bool:
        """Check if this device has a battery"""
        return self._has_battery
    
    def get_status_dict(self) -> Dict:
        """Get power status as a dictionary for API responses"""
        info = self._check_battery()
        if info is None:
            return {'error': 'Could not detect power status'}
        
        return {
            'state': info.state.value,
            'percent': info.percent,
            'plugged': info.plugged,
            'charging': info.charging,
            'seconds_left': info.seconds_left,
            'time_left': info.time_left_text,
            'is_on_power': info.is_on_power,
            'has_battery': self._has_battery
        }


# Global singleton
_power_monitor: Optional[PowerMonitor] = None


def get_power_monitor() -> PowerMonitor:
    """Get or create the global power monitor instance"""
    global _power_monitor
    if _power_monitor is None:
        _power_monitor = PowerMonitor()
    return _power_monitor
