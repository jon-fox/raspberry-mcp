import logging
import time
import threading
from datetime import datetime
from typing import Optional, Dict, List, Tuple

try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    pigpio = None

logger = logging.getLogger(__name__)


class IRListenerManager:
    """Simplified IR listener using pigpio for hardware-precise timing."""

    _instance = None
    _ir_events = []
    _is_listening = False
    _pi = None
    _callback = None

    # GPIO pin for IR receiver
    PIN = 27

    # Signal processing
    _current_signal = []
    _last_tick = None
    _last_level = None
    _last_signal_time = 0
    _signal_timeout_ms = 200
    _signal_counter = 0

    # Thread safety
    _signal_lock = None
    _completion_timer = None

    # Memory management
    _max_events = 1000

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._signal_lock = threading.Lock()
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def is_listening(self) -> bool:
        return self._is_listening

    async def start_listening(self) -> Tuple[bool, str]:
        """Start the IR listener using pigpio callbacks."""
        if not PIGPIO_AVAILABLE:
            return False, "pigpio not available - IR listening requires pigpio support"

        if self._is_listening:
            return True, "IR listener is already running."

        try:
            self._pi = pigpio.pi()

            if not self._pi.connected:
                return False, "pigpiod not running - start with: sudo systemctl start pigpiod"

            logger.info(f"Setting up IR receiver on GPIO{self.PIN}")

            # Configure GPIO pin
            self._pi.set_mode(self.PIN, pigpio.INPUT)
            self._pi.set_pull_up_down(self.PIN, pigpio.PUD_UP)

            # Clear events and reset state
            self._ir_events.clear()
            with self._signal_lock:
                self._current_signal = []
                self._last_tick = None
                self._last_level = None
                self._last_signal_time = 0
                self._signal_counter = 0

            if self._completion_timer:
                self._completion_timer.cancel()
                self._completion_timer = None

            # Set up callback for edge detection
            self._callback = self._pi.callback(
                self.PIN, pigpio.EITHER_EDGE, self._gpio_callback
            )

            self._is_listening = True
            logger.info(f"IR listener started on GPIO{self.PIN}")
            return True, f"IR listener started on GPIO{self.PIN}. Press remote buttons to capture signals."

        except Exception as e:
            logger.error(f"Failed to start IR listener: {e}")
            if self._pi and self._pi.connected:
                self._pi.stop()
                self._pi = None
            return False, f"Failed to start IR listener: {e}"

    async def stop_listening(self) -> Tuple[bool, str]:
        """Stop the IR listener."""
        if not self._is_listening:
            return True, "IR listener is not running."

        try:
            self._is_listening = False

            if self._completion_timer:
                self._completion_timer.cancel()
                self._completion_timer = None

            if self._callback:
                self._callback.cancel()
                self._callback = None

            if self._pi and self._pi.connected:
                self._pi.stop()
                self._pi = None

            with self._signal_lock:
                self._current_signal = []
                self._last_tick = None
                self._last_level = None
                self._last_signal_time = 0

            events_count = len(self._ir_events)
            logger.info(f"IR listener stopped. Captured {events_count} events")
            return True, f"IR listener stopped successfully. Captured {events_count} events."

        except Exception as e:
            logger.error(f"Failed to stop IR listener: {e}")
            return False, f"Failed to stop IR listener: {e}"

    def _gpio_callback(self, _gpio, level, tick):
        """Handle GPIO state changes with hardware-precise timing."""
        try:
            with self._signal_lock:
                current_time = time.time()

                # Calculate pulse duration if we have a previous tick
                if self._last_tick is not None:
                    duration_us = self._tick_diff(self._last_tick, tick)

                    # Filter noise - ignore very short pulses
                    if duration_us < 50:
                        return

                    # Add pulse to current signal
                    self._current_signal.append((self._last_level, duration_us))
                    self._last_signal_time = current_time

                # Update state
                self._last_tick = tick
                self._last_level = level

                # Cancel any existing completion timer
                if self._completion_timer:
                    self._completion_timer.cancel()

                # Start new completion timer
                self._completion_timer = threading.Timer(
                    self._signal_timeout_ms / 1000.0, self._complete_signal_sync
                )
                self._completion_timer.start()

        except Exception as e:
            logger.error(f"Error in GPIO callback: {e}")
            with self._signal_lock:
                self._current_signal = []
                self._last_tick = None
                self._last_level = None

    def _complete_signal_sync(self):
        """Complete signal processing - called from timer thread."""
        try:
            with self._signal_lock:
                if not self._current_signal or not self._is_listening:
                    return

                current_time = time.time()
                time_since_last = (current_time - self._last_signal_time) * 1000

                if time_since_last >= self._signal_timeout_ms:
                    self._finish_current_signal()

        except Exception as e:
            logger.error(f"Error completing signal: {e}")

    def _finish_current_signal(self):
        """Process and store the completed signal."""
        if not self._current_signal:
            return

        self._signal_counter += 1
        signal_number = self._signal_counter
        timing_data = self._current_signal.copy()

        try:
            # Analyze the signal
            analysis = self._analyze_signal(timing_data, signal_number)
            total_duration = sum(duration for _, duration in timing_data)

            # Create event
            ir_event = {
                "timestamp": datetime.now(),
                "type": "ir_signal",
                "signal_number": signal_number,
                "timing_data": timing_data,
                "total_duration_us": total_duration,
                "pulse_count": len(timing_data),
                "analysis": analysis,
            }

            self._ir_events.append(ir_event)

            # Memory management - trim oldest events if needed
            if len(self._ir_events) > self._max_events:
                remove_count = self._max_events // 10
                self._ir_events = self._ir_events[remove_count:]

            logger.info(f"Signal {signal_number}: {len(timing_data)} pulses, {total_duration}μs")

        except Exception as e:
            logger.error(f"Signal processing failed: {e}")

        # Clear current signal
        self._current_signal = []

    def _tick_diff(self, tick1: int, tick2: int) -> int:
        """Calculate difference between pigpio ticks (handles wraparound)."""
        if pigpio:
            try:
                return pigpio.tickDiff(tick1, tick2)
            except Exception:
                pass

        # Fallback for tick wraparound (32-bit microsecond counter)
        diff = tick2 - tick1
        if diff < -2147483648:
            diff += 4294967296
        elif diff > 2147483647:
            diff -= 4294967296
        return abs(diff)

    def _analyze_signal(self, timing_data: List[Tuple[str, int]], signal_number: int) -> Dict:
        """Analyze IR signal and generate unique code."""
        if not timing_data:
            return {"protocol": "Empty", "code": "0x00000000", "raw_timing_data": []}

        total_duration = sum(duration for _, duration in timing_data)

        # Basic validation
        if total_duration < 1000:
            return {"protocol": "Noise", "code": "0x00000000", "raw_timing_data": timing_data}

        # Try NEC protocol detection
        if len(timing_data) >= 4:
            first_low = timing_data[0][1] if timing_data[0][0] == "low" else 0
            first_high = timing_data[1][1] if len(timing_data) > 1 and timing_data[1][0] == "high" else 0

            # NEC AGC pattern: 9ms low, 4.5ms high
            if 7000 <= first_low <= 12000 and 3000 <= first_high <= 6000:
                nec_result = self._decode_nec(timing_data)
                if nec_result:
                    return nec_result

        # Generic protocol: use simple unique code based on signal number
        return {
            "protocol": "Generic",
            "code": f"0xSIG{signal_number:04X}",
            "pulse_count": len(timing_data),
            "total_duration_us": total_duration,
            "raw_timing_data": timing_data,
        }

    def _decode_nec(self, timing_data: List[Tuple[str, int]]) -> Optional[Dict]:
        """Decode NEC protocol IR signal."""
        if len(timing_data) < 34:
            return None

        try:
            data_bits = []

            # Skip AGC (first 2 pulses), decode data bits
            for i in range(2, min(66, len(timing_data) - 1), 2):
                if i + 1 >= len(timing_data):
                    break

                low_pulse = timing_data[i][1]
                high_pulse = timing_data[i + 1][1]

                if 300 <= low_pulse <= 800:
                    if 300 <= high_pulse <= 800:
                        data_bits.append(0)
                    elif 1200 <= high_pulse <= 2200:
                        data_bits.append(1)
                    else:
                        break
                else:
                    break

            if len(data_bits) >= 16:
                address = sum(data_bits[i] << i for i in range(8) if i < len(data_bits))
                command = sum(data_bits[i + 8] << i for i in range(8) if (i + 8) < len(data_bits))

                return {
                    "protocol": "NEC",
                    "address": address,
                    "command": command,
                    "code": f"0x{address:02X}{command:02X}",
                    "raw_timing_data": timing_data,
                }

        except Exception as e:
            logger.debug(f"NEC decode failed: {e}")

        return None

    def get_recent_events(self, horizon_s: int = 20) -> List[Dict]:
        """Get IR events from the last horizon_s seconds."""
        cutoff_time = datetime.now().timestamp() - horizon_s
        return [
            event
            for event in self._ir_events
            if event["timestamp"].timestamp() > cutoff_time
        ]

    def clear_events(self):
        """Clear all recorded IR events."""
        self._ir_events.clear()
        with self._signal_lock:
            self._signal_counter = 0

    def get_listener_status(self) -> Dict:
        """Get status information."""
        status = {
            "is_listening": self._is_listening,
            "gpio_pin": self.PIN,
            "total_events": len(self._ir_events),
            "pigpio_available": PIGPIO_AVAILABLE,
            "pigpio_connected": self._pi.connected if self._pi else False,
            "signal_counter": self._signal_counter,
            "current_signal_pulses": len(self._current_signal),
        }

        if self._pi and self._pi.connected:
            try:
                status["current_gpio_state"] = self._pi.read(self.PIN)
            except Exception:
                pass

        if self._ir_events:
            latest = self._ir_events[-1]
            status["latest_event_time"] = latest["timestamp"].isoformat()
            status["latest_event_code"] = latest.get("analysis", {}).get("code", "N/A")

        return status
