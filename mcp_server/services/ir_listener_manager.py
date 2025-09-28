import asyncio
import logging
import time
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
    _pi = None  # pigpio.pi instance
    _callback = None
    
    # GPIO pin 27 for IR receiver (keep consistent with original)
    PIN = 27
    
    # Signal processing
    _current_signal = []
    _signal_start_time = 0
    _last_edge_time = 0
    _signal_timeout_ms = 50  # 50ms gap = end of signal
    _signal_counter = 0
    _recent_signals = []  # For pattern matching
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    def enable_debug_logging(self):
        """Enable debug logging for troubleshooting."""
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info("Debug logging enabled for IR listener")
    
    def is_listening(self) -> bool:
        return self._is_listening
    
    async def start_listening(self) -> Tuple[bool, str]:
        """Start the IR listener using pigpio callbacks."""
        if not PIGPIO_AVAILABLE:
            logger.error("pigpio not available - IR listening requires pigpio support")
            return False, "pigpio not available - IR listening requires pigpio support"
            
        if self._is_listening:
            logger.info("IR listener already running")
            return True, "IR listener is already running."
        
        try:
            # Connect to pigpio daemon
            logger.info("Connecting to pigpio daemon...")
            self._pi = pigpio.pi()
            
            if not self._pi.connected:
                logger.error("pigpiod not running - start with: sudo systemctl start pigpiod")
                return False, "pigpiod not running - start with: sudo systemctl start pigpiod"
            
            logger.info(f"Connected to pigpiod, setting up IR receiver on GPIO{self.PIN}")
            
            # Configure GPIO pin
            self._pi.set_mode(self.PIN, pigpio.INPUT)
            self._pi.set_pull_up_down(self.PIN, pigpio.PUD_UP)
            
            # Read initial GPIO state
            initial_state = self._pi.read(self.PIN)
            logger.info(f"GPIO{self.PIN} initial state: {initial_state}")
            
            # Clear events and reset counters
            self._ir_events.clear()
            self._recent_signals.clear()
            self._current_signal = []
            self._signal_counter = 0
            
            # Set up callback for both edges (pigpio handles timing precisely)
            logger.info(f"Setting up GPIO callback on pin {self.PIN} for EITHER_EDGE")
            self._callback = self._pi.callback(self.PIN, pigpio.EITHER_EDGE, self._gpio_callback)
            logger.info(f"Callback setup complete: {self._callback}")
            
            self._is_listening = True
            logger.info(f"IR listener started successfully on GPIO{self.PIN}")
            logger.info("Ready to capture IR signals - press remote buttons now!")
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
            logger.info("IR listener not running")
            return True, "IR listener is not running."
        
        try:
            logger.info("Stopping IR listener")
            self._is_listening = False
            
            # Cancel callback
            if self._callback:
                self._callback.cancel()
                self._callback = None
            
            # Disconnect from pigpio
            if self._pi and self._pi.connected:
                self._pi.stop()
                self._pi = None
            
            events_count = len(self._ir_events)
            logger.info(f"IR listener stopped successfully. Captured {events_count} events total")
            return True, f"IR listener stopped successfully. Captured {events_count} events."
            
        except Exception as e:
            logger.error(f"Failed to stop IR listener: {e}")
            return False, f"Failed to stop IR listener: {e}"
    
    def _gpio_callback(self, gpio: int, level: int, tick: int):
        """Hardware-timed GPIO callback."""
        if not self._is_listening:
            return
        
        current_time_us = tick
        
        # Handle signal start (first edge)
        if not self._current_signal:
            self._signal_start_time = current_time_us
            self._last_edge_time = current_time_us
            self._current_signal = []
            return
        
        # Calculate duration since last edge
        duration_us = self._tick_diff(current_time_us, self._last_edge_time)
        
        # If gap is too long, finish previous signal and start new one
        if duration_us > (self._signal_timeout_ms * 1000):
            self._finish_current_signal()
            self._signal_start_time = current_time_us
            self._last_edge_time = current_time_us
            self._current_signal = []
            return
        
        # Add pulse to current signal
        state = 'high' if level else 'low'
        self._current_signal.append((state, duration_us))
        self._last_edge_time = current_time_us
        
        # Check for signal completion
        asyncio.create_task(self._check_signal_completion())
    
    async def _check_signal_completion(self):
        """Check if current signal should be completed (non-blocking)."""
        if not self._current_signal:
            return
        
        # Wait a bit to see if more pulses come
        await asyncio.sleep(self._signal_timeout_ms / 1000.0)
        
        # If no new pulses arrived, finish the signal
        if self._current_signal and self._is_listening:
            current_time = self._pi.get_current_tick() if self._pi else 0
            time_since_last = self._tick_diff(current_time, self._last_edge_time)
            
            if time_since_last > (self._signal_timeout_ms * 1000):
                self._finish_current_signal()
    
    def _finish_current_signal(self):
        """Process and store the completed signal."""
        if not self._current_signal:
            return
        
        self._signal_counter += 1
        signal_number = self._signal_counter
        timing_data = self._current_signal.copy()
        
        logger.info(f"Signal {signal_number} completed: {len(timing_data)} pulses")
        
        try:
            # Analyze the signal
            analysis = self._analyze_signal(timing_data, signal_number)
            
            # Check for matching previous signals
            matched = self._find_matching_signal(timing_data)
            if matched:
                logger.info(f"Signal {signal_number} matches previous: {matched['code']}")
                analysis.update(matched)
                analysis['matched_previous'] = True
            else:
                self._store_recent_signal(timing_data, analysis)
            
            # Create event
            total_duration = sum(duration for _, duration in timing_data)
            ir_event = {
                'timestamp': datetime.now(),
                'type': 'ir_signal',
                'signal_number': signal_number,
                'timing_data': timing_data,
                'total_duration_us': total_duration,
                'pulse_count': len(timing_data),
                'analysis': analysis
            }
            
            self._ir_events.append(ir_event)
            
            logger.info(f"Signal {signal_number}: {analysis.get('protocol', 'Unknown')} - {analysis.get('code', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Signal {signal_number} processing failed: {e}")
            # Still store the raw signal
            ir_event = {
                'timestamp': datetime.now(),
                'type': 'ir_signal',
                'signal_number': signal_number,
                'timing_data': timing_data,
                'total_duration_us': sum(duration for _, duration in timing_data),
                'pulse_count': len(timing_data),
                'analysis': {'protocol': 'Raw', 'code': f'0xRAW{signal_number:04X}', 'error': str(e)}
            }
            self._ir_events.append(ir_event)
        
        # Clear current signal
        self._current_signal = []
    
    def _tick_diff(self, tick1: int, tick2: int) -> int:
        """Calculate difference between pigpio ticks (handles wraparound)."""
        return pigpio.tickDiff(tick2, tick1) if pigpio else abs(tick1 - tick2)
    
    def _analyze_signal(self, timing_data: List[Tuple[str, int]], signal_number: int) -> Dict:
        """Simple, reliable signal analysis."""
        if not timing_data:
            return {'protocol': 'Empty', 'code': '0x00000000'}
        
        durations = [duration for _, duration in timing_data]
        total_duration = sum(durations)
        
        # Basic validation
        if total_duration < 1000:  # Less than 1ms
            return {'protocol': 'Noise', 'code': '0x00000000'}
        
        # Simple NEC detection
        if len(timing_data) >= 4:
            first_low = timing_data[0][1] if timing_data[0][0] == 'low' else 0
            first_high = timing_data[1][1] if len(timing_data) > 1 and timing_data[1][0] == 'high' else 0
            
            # Look for NEC-like AGC (9ms low, 4.5ms high)
            if 7000 <= first_low <= 12000 and 3000 <= first_high <= 6000:
                # Try to decode NEC
                nec_result = self._decode_nec(timing_data)
                if nec_result:
                    return nec_result
        
        # Fallback: create stable hash-based code
        # Normalize timings to reduce noise sensitivity
        normalized = []
        for state, duration in timing_data[:16]:  # Use first 16 pulses
            # Round to nearest 100μs for stability
            normalized_duration = round(duration / 100) * 100
            normalized.append(normalized_duration)
        
        # Create stable hash
        code_hash = hash(tuple(normalized)) & 0xFFFFFFFF
        
        return {
            'protocol': 'Generic',
            'code': f'0x{code_hash:08X}',
            'pulse_count': len(timing_data),
            'total_duration_us': total_duration,
            'normalized_timing': normalized
        }
    
    def _decode_nec(self, timing_data: List[Tuple[str, int]]) -> Optional[Dict]:
        """Simple NEC decoding."""
        if len(timing_data) < 34:  # Need at least 34 pulses for NEC
            return None
        
        try:
            # Skip AGC (first 2 pulses)
            data_bits = []
            
            for i in range(2, min(66, len(timing_data) - 1), 2):
                if i + 1 >= len(timing_data):
                    break
                
                low_pulse = timing_data[i][1]
                high_pulse = timing_data[i + 1][1]
                
                # Simple bit detection based on high pulse length
                if 300 <= low_pulse <= 800:  # Valid low pulse
                    if 300 <= high_pulse <= 800:  # Short high = bit 0
                        data_bits.append(0)
                    elif 1200 <= high_pulse <= 2200:  # Long high = bit 1
                        data_bits.append(1)
                    else:
                        break  # Invalid pulse
                else:
                    break
            
            if len(data_bits) >= 16:
                # Extract address and command (first 16 bits)
                address = 0
                command = 0
                
                for i in range(8):
                    if i < len(data_bits) and data_bits[i]:
                        address |= (1 << i)
                
                for i in range(8):
                    if (i + 8) < len(data_bits) and data_bits[i + 8]:
                        command |= (1 << i)
                
                return {
                    'protocol': 'NEC',
                    'address': address,
                    'command': command,
                    'code': f'0x{address:02X}{command:02X}0000',
                    'bits_decoded': len(data_bits)
                }
        except Exception as e:
            logger.debug(f"NEC decode failed: {e}")
        
        return None
    
    def _find_matching_signal(self, timing_data: List[Tuple[str, int]]) -> Optional[Dict]:
        """Find if this signal matches a recent one."""
        if not timing_data:
            return None
        
        # Create normalized pattern for matching
        normalized = []
        for state, duration in timing_data[:16]:
            normalized.append(round(duration / 100) * 100)
        
        # Check recent signals
        for recent in self._recent_signals[-10:]:
            if self._patterns_match(normalized, recent['normalized']):
                return recent['analysis']
        
        return None
    
    def _patterns_match(self, pattern1: List[int], pattern2: List[int], tolerance: float = 0.2) -> bool:
        """Check if two timing patterns match within tolerance."""
        if len(pattern1) != len(pattern2):
            return False
        
        matches = 0
        for p1, p2 in zip(pattern1, pattern2):
            if p1 == 0 and p2 == 0:
                matches += 1
            elif p1 == 0 or p2 == 0:
                continue  # Skip zero values
            else:
                diff = abs(p1 - p2) / max(p1, p2)
                if diff <= tolerance:
                    matches += 1
        
        return matches >= len(pattern1) * 0.8  # 80% match required
    
    def _store_recent_signal(self, timing_data: List[Tuple[str, int]], analysis: Dict):
        """Store signal for future matching."""
        normalized = []
        for state, duration in timing_data[:16]:
            normalized.append(round(duration / 100) * 100)
        
        self._recent_signals.append({
            'normalized': normalized,
            'analysis': analysis,
            'timestamp': time.time()
        })
        
        # Keep only recent signals
        if len(self._recent_signals) > 20:
            self._recent_signals = self._recent_signals[-20:]
    
    def get_recent_events(self, horizon_s: int = 20) -> List[Dict]:
        """Get IR events from the last horizon_s seconds."""
        cutoff_time = datetime.now().timestamp() - horizon_s
        recent_events = [
            event for event in self._ir_events 
            if event['timestamp'].timestamp() > cutoff_time
        ]
        logger.info(f"Retrieved {len(recent_events)} IR events from last {horizon_s} seconds")
        return recent_events
    
    def clear_events(self):
        """Clear all recorded IR events."""
        events_count = len(self._ir_events)
        self._ir_events.clear()
        self._recent_signals.clear()
        logger.info(f"Cleared {events_count} IR events from memory")
    
    def get_listener_status(self) -> Dict:
        """Get detailed status information."""
        status = {
            'is_listening': self._is_listening,
            'gpio_pin': self.PIN,
            'total_events': len(self._ir_events),
            'pigpio_connected': self._pi.connected if self._pi else False,
            'recent_events_1min': len(self.get_recent_events(60)),
            'recent_events_5min': len(self.get_recent_events(300))
        }
        
        if self._ir_events:
            latest_event = self._ir_events[-1]
            status['latest_event_time'] = latest_event['timestamp'].isoformat()
            status['latest_event_type'] = latest_event.get('type', 'unknown')
            
        return status