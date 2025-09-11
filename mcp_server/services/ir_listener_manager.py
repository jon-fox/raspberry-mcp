import asyncio
import logging
import RPi.GPIO as GPIO
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class IRListenerManager:
    """Manages the background IR listener process."""
    
    _instance = None
    _listener_task = None
    _ir_events = []
    _is_listening = False
    # GPIO pin 27 is hardcoded - this should not be configurable by clients
    # The IR receiver hardware is expected to be connected to this specific pin
    PIN = 27  # GPIO27 (pin 13)
    _signal_buffer = []
    _last_signal_time = 0
    _signal_timeout = 0.1  # 100ms timeout between signals
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    def is_listening(self) -> bool:
        return self._is_listening
    
    async def start_listening(self) -> tuple[bool, str]:
        """Start the IR listener in the background."""       
        if self._is_listening:
            logger.info("IR listener start requested but already running")
            return True, "IR listener is already running."
        
        try:
            logger.info(f"Initializing GPIO pin {self.PIN} for IR listening")
            # Initialize GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Clear any existing events
            self._ir_events.clear()
            self._signal_buffer.clear()
            
            # Start the listener task
            logger.info("Starting IR listener background task")
            self._listener_task = asyncio.create_task(self._listen_loop())
            self._is_listening = True
            
            logger.info(f"IR listener started successfully on GPIO{self.PIN} and ready to capture signals")
            return True, f"IR listener started successfully on GPIO pin {self.PIN}. Press remote buttons to capture signals."
            
        except Exception as e:
            logger.error(f"Failed to start IR listener: {str(e)}")
            return False, f"Failed to start IR listener: {str(e)}"
    
    async def stop_listening(self) -> tuple[bool, str]:
        """Stop the IR listener."""
        if not self._is_listening:
            logger.info("IR listener stop requested but not currently running")
            return True, "IR listener is not running."
        
        try:
            logger.info("Stopping IR listener")
            self._is_listening = False
            
            if self._listener_task:
                logger.info("Cancelling IR listener background task")
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    logger.info("IR listener task cancelled successfully")
                    pass
                self._listener_task = None
            
            logger.info("Cleaning up GPIO resources")
            GPIO.cleanup()
            
            events_count = len(self._ir_events)
            logger.info(f"IR listener stopped successfully. Captured {events_count} events total")
            return True, "IR listener stopped successfully."
            
        except Exception as e:
            logger.error(f"Failed to stop IR listener: {str(e)}")
            return False, f"Failed to stop IR listener: {str(e)}"
    
    def get_recent_events(self, horizon_s: int = 20) -> list:
        """Get IR events from the last horizon_s seconds."""
        cutoff_time = datetime.now().timestamp() - horizon_s
        recent_events = [
            event for event in self._ir_events 
            if event['timestamp'].timestamp() > cutoff_time
        ]
        logger.info(f"Retrieving {len(recent_events)} IR events from last {horizon_s} seconds (total events: {len(self._ir_events)})")
        return recent_events
    
    def clear_events(self):
        """Clear all recorded IR events."""
        events_count = len(self._ir_events)
        self._ir_events.clear()
        self._signal_buffer.clear()
        logger.info(f"Cleared {events_count} IR events from memory")
    
    def get_listener_status(self) -> dict:
        """Get detailed status information about the IR listener."""
        status = {
            'is_listening': self._is_listening,
            'gpio_pin': self.PIN,
            'total_events': len(self._ir_events),
            'listener_task_active': self._listener_task is not None and not self._listener_task.done(),
            'recent_events_1min': len(self.get_recent_events(60)),
            'recent_events_5min': len(self.get_recent_events(300))
        }
        
        if self._ir_events:
            latest_event = self._ir_events[-1]
            status['latest_event_time'] = latest_event['timestamp'].isoformat()
            status['latest_event_type'] = latest_event.get('type', 'unknown')
            
        logger.info(f"IR listener status: {status}")
        return status
    
    async def _listen_loop(self):
        """Background loop that listens for IR signals."""
        logger.info("IR listener loop started - monitoring GPIO pin for IR signals")
        signal_count = 0
        last_log_time = time.time()
        
        try:
            while self._is_listening:
                current_time = time.time()
                
                # Log heartbeat every 30 seconds to show listener is alive
                if current_time - last_log_time > 30:
                    logger.info(f"IR listener heartbeat - still monitoring GPIO{self.PIN}, {signal_count} signals detected so far")
                    last_log_time = current_time
                
                # Check for IR signal (active low)
                if GPIO.input(self.PIN) == 0:
                    signal_start_time = time.time()
                    signal_count += 1
                    
                    logger.info(f"IR signal detected! (Signal #{signal_count}) - Starting to capture timing data")
                    
                    # Capture the signal timing pattern
                    timing_data = []
                    last_state = 0
                    state_start_time = signal_start_time
                    
                    # Record the initial low state
                    while GPIO.input(self.PIN) == 0 and self._is_listening:
                        await asyncio.sleep(0.00005)  # 50 microsecond sampling
                    
                    if self._is_listening:
                        low_duration = (time.time() - state_start_time) * 1000000  # Convert to microseconds
                        timing_data.append(('low', int(low_duration)))
                        logger.debug(f"Signal {signal_count}: Initial low pulse = {int(low_duration)}μs")
                    
                    # Continue capturing the rest of the signal
                    state_start_time = time.time()
                    timeout_start = time.time()
                    max_signal_duration = 0.5  # 500ms max signal duration
                    
                    while self._is_listening and (time.time() - timeout_start) < max_signal_duration:
                        current_pin_state = GPIO.input(self.PIN)
                        
                        if current_pin_state != last_state:
                            # State changed, record the duration
                            duration = (time.time() - state_start_time) * 1000000  # microseconds
                            state_name = 'low' if last_state == 0 else 'high'
                            timing_data.append((state_name, int(duration)))
                            
                            last_state = current_pin_state
                            state_start_time = time.time()
                        
                        await asyncio.sleep(0.00005)  # 50 microsecond sampling
                    
                    # Record the final state if signal ended
                    if timing_data:
                        final_duration = (time.time() - state_start_time) * 1000000
                        final_state = 'low' if last_state == 0 else 'high'
                        timing_data.append((final_state, int(final_duration)))
                    
                    # Create IR event with captured timing
                    timestamp = datetime.now()
                    total_duration = sum(duration for _, duration in timing_data)
                    
                    ir_event = {
                        'timestamp': timestamp,
                        'type': 'ir_signal',
                        'signal_number': signal_count,
                        'timing_data': timing_data,
                        'total_duration_us': total_duration,
                        'pulse_count': len(timing_data)
                    }
                    
                    self._ir_events.append(ir_event)
                    
                    logger.info(f"Signal {signal_count} captured: {len(timing_data)} pulses, {total_duration}μs total duration")
                    logger.debug(f"Signal {signal_count} timing pattern: {timing_data[:10]}..." if len(timing_data) > 10 else f"Signal {signal_count} timing pattern: {timing_data}")
                    
                    # Wait a bit before looking for the next signal to avoid double-detection
                    await asyncio.sleep(0.05)  # 50ms debounce
                
                else:
                    # No signal detected, short sleep to prevent CPU spinning
                    await asyncio.sleep(0.001)  # Check every 1ms when idle
                
        except asyncio.CancelledError:
            logger.info(f"IR listener loop cancelled - captured {signal_count} signals total")
            raise
        except Exception as e:
            logger.error(f"IR listener error after capturing {signal_count} signals: {e}")
            self._is_listening = False
            raise
