"""Simulated environment for testing climate control without real sensors.

Simple singleton to simulate temperature/humidity that can be controlled programmatically.
"""

import threading
import time
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SimulatedEnvironment:
    """Singleton that manages simulated temperature and humidity for testing.
    
    This allows testing climate control logic without requiring real sensors.
    The environment naturally drifts toward ambient conditions unless actively controlled.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the simulated environment."""
        self._simulation_enabled = False
        self._current_temp_f = 70.0
        self._current_humidity = 50.0
        self._ambient_temp_f = 75.0
        self._ambient_humidity = 55.0
        self._ac_cooling_rate = 0.3  # Degrees F per second
        self._drift_rate = 0.05  # How fast temp returns to ambient per second
        self._last_update = time.time()
        self._update_thread = None
        self._stop_thread = False
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        return cls()
    
    def enable_simulation(self, temp_f: float = 70.0, humidity: float = 50.0):
        """Enable simulation mode - simple!"""
        with self._lock:
            self._simulation_enabled = True
            self._current_temp_f = temp_f
            self._current_humidity = humidity
            self._ambient_temp_f = temp_f + 5.0  # Natural drift slightly warmer
            self._last_update = time.time()
            
            if self._update_thread is None or not self._update_thread.is_alive():
                self._stop_thread = False
                self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
                self._update_thread.start()
            
            logger.info(f"Simulation enabled: {temp_f}°F, {humidity}%")
    
    def disable_simulation(self):
        """Disable simulation mode."""
        with self._lock:
            self._simulation_enabled = False
            self._stop_thread = True
            logger.info("Simulation disabled")
    
    def is_simulation_enabled(self) -> bool:
        """Check if simulation is enabled."""
        return self._simulation_enabled
    
    def read_sensor(self) -> Tuple[bool, Optional[float], Optional[float], Optional[float], str]:
        """Read the simulated sensor values."""
        if not self._simulation_enabled:
            return False, None, None, None, "Simulation not enabled"
        
        with self._lock:
            temp_f = self._current_temp_f
            temp_c = (temp_f - 32.0) * 5.0 / 9.0
            humidity = self._current_humidity
            message = f"Simulated: {temp_c:.1f}°C ({temp_f:.1f}°F), {humidity:.1f}%"
            return True, temp_c, temp_f, humidity, message
    
    def adjust_temperature(self, delta_f: float):
        """Adjust temperature by delta amount (positive or negative)."""
        with self._lock:
            self._current_temp_f += delta_f
            logger.info(f"Temperature adjusted by {delta_f:+.1f}°F to {self._current_temp_f:.1f}°F")
    
    def _update_loop(self):
        """Background thread that continuously updates environment state."""
        logger.info("Environment update loop started")
        
        while not self._stop_thread:
            try:
                time.sleep(2)  # Update every 2 seconds
                self._update_environment()
            except Exception as e:
                logger.error(f"Error in environment update loop: {e}")
        
        logger.info("Environment update loop stopped")
    
    def _update_environment(self):
        """Update simulated environment - natural drift toward ambient."""
        with self._lock:
            if not self._simulation_enabled:
                return
            
            current_time = time.time()
            time_delta = current_time - self._last_update
            self._last_update = current_time
            
            # Natural drift toward ambient (gets warmer over time)
            temp_diff = self._ambient_temp_f - self._current_temp_f
            drift_amount = temp_diff * self._drift_rate * time_delta
            self._current_temp_f += drift_amount
    
    def get_status(self) -> dict:
        """Get current status."""
        with self._lock:
            return {
                'enabled': self._simulation_enabled,
                'temp_f': round(self._current_temp_f, 1),
                'temp_c': round((self._current_temp_f - 32.0) * 5.0 / 9.0, 1),
                'humidity': round(self._current_humidity, 1),
            }
