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
                    
                    # Analyze and decode the signal
                    signal_analysis = self._analyze_ir_signal(timing_data, signal_count)
                    
                    ir_event = {
                        'timestamp': timestamp,
                        'type': 'ir_signal',
                        'signal_number': signal_count,
                        'timing_data': timing_data,
                        'total_duration_us': total_duration,
                        'pulse_count': len(timing_data),
                        'analysis': signal_analysis
                    }
                    
                    self._ir_events.append(ir_event)
                    
                    logger.info(f"Signal {signal_count} captured: {len(timing_data)} pulses, {total_duration}μs total duration")
                    logger.info(f"Signal {signal_count} analysis: Protocol={signal_analysis.get('protocol', 'Unknown')}, Code={signal_analysis.get('code', 'N/A')}")
                    logger.debug(f"Signal {signal_count} timing pattern: {timing_data[:10]}..." if len(timing_data) > 10 else f"Signal {signal_count} timing pattern: {timing_data}")
                    
                    # Log detailed signal characteristics
                    if signal_analysis.get('protocol') != 'Unknown':
                        logger.info(f"Signal {signal_count} decoded: {signal_analysis}")
                    else:
                        logger.warning(f"Signal {signal_count} could not be decoded - unknown protocol")
                    
                    # Log signal fingerprint for debugging
                    fingerprint = self._generate_signal_fingerprint(timing_data)
                    logger.debug(f"Signal {signal_count} fingerprint: {fingerprint}")
                    
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
    
    def _analyze_ir_signal(self, timing_data: list, signal_number: int) -> dict:
        """Analyze IR signal timing data to identify protocol and decode commands."""
        logger.debug(f"Analyzing signal {signal_number} with {len(timing_data)} pulses")
        
        if not timing_data or len(timing_data) < 4:
            logger.warning(f"Signal {signal_number}: Insufficient timing data for analysis")
            return {'protocol': 'Unknown', 'reason': 'Insufficient data'}
        
        # Extract pulse durations for analysis
        pulses = [duration for state, duration in timing_data]
        
        # Log detailed timing information for unknown protocols
        logger.debug(f"Signal {signal_number} timing analysis:")
        logger.debug(f"  First 10 pulses: {pulses[:10]}")
        logger.debug(f"  Min/Max/Avg: {min(pulses)}/{max(pulses)}/{sum(pulses)//len(pulses)}μs")
        logger.debug(f"  Total duration: {sum(pulses)}μs, Pulse count: {len(pulses)}")
        
        # Try to identify common IR protocols
        analysis = {
            'protocol': 'Unknown',
            'code': None,
            'address': None,
            'command': None,
            'repeat': False,
            'pulse_analysis': {
                'total_pulses': len(pulses),
                'min_pulse': min(pulses),
                'max_pulse': max(pulses),
                'avg_pulse': sum(pulses) // len(pulses)
            }
        }
        
        # NEC Protocol Analysis (most common)
        nec_result = self._analyze_nec_protocol(timing_data)
        if nec_result['protocol'] == 'NEC':
            analysis.update(nec_result)
            logger.info(f"Signal {signal_number}: NEC protocol detected - Address: 0x{nec_result.get('address', 0):02X}, Command: 0x{nec_result.get('command', 0):02X}")
            return analysis
        
        # Sony SIRC Protocol Analysis
        sony_result = self._analyze_sony_protocol(timing_data)
        if sony_result['protocol'] == 'Sony':
            analysis.update(sony_result)
            logger.info(f"Signal {signal_number}: Sony SIRC protocol detected - Command: 0x{sony_result.get('command', 0):02X}")
            return analysis
        
        # RC5 Protocol Analysis
        rc5_result = self._analyze_rc5_protocol(timing_data)
        if rc5_result['protocol'] == 'RC5':
            analysis.update(rc5_result)
            logger.info(f"Signal {signal_number}: RC5 protocol detected - Address: 0x{rc5_result.get('address', 0):02X}, Command: 0x{rc5_result.get('command', 0):02X}")
            return analysis
        
        # Generic pattern analysis for unknown protocols
        pattern_info = self._analyze_signal_pattern(timing_data)
        analysis.update(pattern_info)
        
        # Try to create a usable code even for unknown protocols
        generic_result = self._create_generic_code(timing_data, signal_number)
        if generic_result.get('code'):
            analysis.update(generic_result)
            logger.info(f"Signal {signal_number}: Created generic code - {generic_result.get('code')}")
        
        # Enhanced logging for unknown protocols
        logger.warning(f"Signal {signal_number}: Unknown protocol - Pattern: {pattern_info.get('pattern_type', 'Unrecognized')}")
        logger.info(f"Signal {signal_number} detailed analysis:")
        logger.info(f"  Pattern type: {pattern_info.get('pattern_type', 'Unknown')}")
        logger.info(f"  First few pulses: {timing_data[:6]}...")
        logger.info(f"  Unique pulse widths: {len(set(pulses))}")
        logger.info(f"  Possible protocol clues:")
        
        # Add protocol detection hints
        first_pulse = pulses[0] if pulses else 0
        if first_pulse > 8000:
            logger.info(f"    - Long initial pulse ({first_pulse}μs) suggests AGC header")
        if len(pulses) in [24, 26, 28]:
            logger.info(f"    - Pulse count ({len(pulses)}) suggests 12-14 bit protocol")
        if len(pulses) in [66, 68, 70]:
            logger.info(f"    - Pulse count ({len(pulses)}) suggests 32-34 bit protocol")
        
        return analysis
    
    def _create_generic_code(self, timing_data: list, signal_number: int) -> dict:
        """Create a generic IR code for unknown protocols based on timing fingerprint."""
        if not timing_data:
            return {}
        
        # Create a hash-like code from the timing pattern
        pulses = [duration for state, duration in timing_data]
        
        # Normalize timing to create a consistent pattern
        if len(pulses) >= 4:
            # Use first few pulses and total duration to create unique code
            fingerprint_data = pulses[:8] + [sum(pulses), len(pulses)]
            
            # Create a simple hash-like code
            code_value = 0
            for val in fingerprint_data:
                code_value = (code_value * 37 + val) % 0xFFFFFFFF
            
            # Format as hex code
            generic_code = f"0xGEN{code_value:08X}"
            
            logger.debug(f"Generated generic code {generic_code} for signal {signal_number}")
            
            return {
                'protocol': 'Generic',
                'code': generic_code,
                'raw_timing_data': timing_data,  # Store the actual timing data for transmission
                'fingerprint_based': True,
                'note': 'Generated from timing pattern - uses raw timing for replay'
            }
        
        return {}
    
    def _analyze_nec_protocol(self, timing_data: list) -> dict:
        """Analyze timing data for NEC IR protocol."""
        logger.debug("Attempting NEC protocol analysis")
        
        if len(timing_data) < 34:  # NEC needs at least 34 pulses (minimum for repeat code)
            logger.debug(f"NEC: Insufficient pulses - got {len(timing_data)}, need at least 34")
            return {'protocol': 'Unknown', 'reason': f'Too few pulses for NEC ({len(timing_data)})'}
        
        # NEC protocol characteristics
        # AGC burst: ~9ms low, ~4.5ms high
        # Bit 0: ~560μs low, ~560μs high
        # Bit 1: ~560μs low, ~1690μs high
        
        pulses = [duration for state, duration in timing_data]
        
        # Log first few pulses for debugging
        logger.debug(f"NEC analysis - First 6 pulses: {pulses[:6]}")
        
        # Check for NEC AGC burst (first two pulses)
        agc_low = pulses[0]
        agc_high = pulses[1] if len(pulses) > 1 else 0
        
        logger.debug(f"NEC AGC check: low={agc_low}μs (expect ~9000), high={agc_high}μs (expect ~4500)")
        
        if agc_low < 7000 or agc_low > 11000:  # More flexible range ~9ms ±2ms
            logger.debug(f"NEC: AGC low pulse out of range: {agc_low}μs (expected 7000-11000μs)")
            return {'protocol': 'Unknown', 'reason': f'No NEC AGC burst - got {agc_low}μs'}
        
        if agc_high < 3000 or agc_high > 6000:  # More flexible range ~4.5ms ±1.5ms  
            logger.debug(f"NEC: AGC high pulse out of range: {agc_high}μs (expected 3000-6000μs)")
            return {'protocol': 'Unknown', 'reason': f'No NEC AGC response - got {agc_high}μs'}
        
        logger.debug("NEC AGC burst detected - analyzing data bits")
        
        # Check for NEC repeat code (short sequence)
        if len(timing_data) < 68:  # Less than full 32-bit command
            if len(timing_data) == 4:  # Repeat code pattern
                logger.info("NEC repeat code detected")
                return {
                    'protocol': 'NEC',
                    'code': 'REPEAT',
                    'repeat': True,
                    'verified': True
                }
            else:
                logger.debug(f"NEC: Incomplete data - got {len(timing_data)} pulses, need 68 for full command")
                return {'protocol': 'Unknown', 'reason': f'Incomplete NEC data ({len(timing_data)} pulses)'}
        
        # Decode data bits (skip AGC burst)
        data_bits = []
        bit_errors = []
        
        for i in range(2, min(len(pulses) - 1, 66), 2):  # Process pairs of pulses
            if i + 1 >= len(pulses):
                break
                
            low_pulse = pulses[i]
            high_pulse = pulses[i + 1]
            bit_num = (i - 2) // 2
            
            # NEC bit timing analysis - more flexible ranges
            if 300 <= low_pulse <= 900:  # ~560μs ±240μs (more flexible)
                if 300 <= high_pulse <= 900:  # Bit 0
                    data_bits.append(0)
                    logger.debug(f"NEC bit {bit_num}: 0 (low={low_pulse}, high={high_pulse})")
                elif 1200 <= high_pulse <= 2200:  # Bit 1  
                    data_bits.append(1)
                    logger.debug(f"NEC bit {bit_num}: 1 (low={low_pulse}, high={high_pulse})")
                else:
                    error_msg = f"Bit {bit_num}: Invalid high pulse {high_pulse}μs"
                    bit_errors.append(error_msg)
                    logger.debug(f"NEC: {error_msg}")
                    break
            else:
                error_msg = f"Bit {bit_num}: Invalid low pulse {low_pulse}μs"
                bit_errors.append(error_msg)
                logger.debug(f"NEC: {error_msg}")
                break
        
        logger.debug(f"NEC decoded {len(data_bits)} bits, errors: {bit_errors}")
        
        if len(data_bits) >= 32:
            # Convert bits to bytes
            address = self._bits_to_byte(data_bits[0:8])
            address_inv = self._bits_to_byte(data_bits[8:16])
            command = self._bits_to_byte(data_bits[16:24])
            command_inv = self._bits_to_byte(data_bits[24:32])
            
            logger.debug(f"NEC bytes: addr={address:02X}, addr_inv={address_inv:02X}, cmd={command:02X}, cmd_inv={command_inv:02X}")
            
            # Verify inverse bytes
            if address == (address_inv ^ 0xFF) and command == (command_inv ^ 0xFF):
                logger.info(f"NEC protocol verified: Address=0x{address:02X}, Command=0x{command:02X}")
                return {
                    'protocol': 'NEC',
                    'address': address,
                    'command': command,
                    'code': f"0x{address:02X}{command:02X}",
                    'bits_decoded': len(data_bits),
                    'verified': True
                }
            else:
                logger.warning(f"NEC verification failed:")
                logger.warning(f"  Address check: {address:02X} vs {address_inv^0xFF:02X}")
                logger.warning(f"  Command check: {command:02X} vs {command_inv^0xFF:02X}")
                # Still return as NEC but unverified
                return {
                    'protocol': 'NEC',
                    'address': address,
                    'command': command,
                    'code': f"0x{address:02X}{command:02X}",
                    'bits_decoded': len(data_bits),
                    'verified': False,
                    'verification_error': 'Inverse byte check failed'
                }
        
        logger.debug(f"NEC decoding failed - only got {len(data_bits)} bits, need 32")
        return {'protocol': 'Unknown', 'reason': f'NEC decoding failed - {len(data_bits)} bits, errors: {bit_errors}'}
    
    def _analyze_sony_protocol(self, timing_data: list) -> dict:
        """Analyze timing data for Sony SIRC protocol."""
        logger.debug("Attempting Sony SIRC protocol analysis")
        
        # Sony SIRC characteristics
        # AGC: ~2.4ms low
        # Bit 0: ~600μs low, ~600μs high
        # Bit 1: ~600μs low, ~1200μs high
        
        if len(timing_data) < 24:  # Sony needs at least 12 bits
            return {'protocol': 'Unknown', 'reason': 'Too few pulses for Sony'}
        
        pulses = [duration for state, duration in timing_data]
        
        # Check for Sony AGC
        if pulses[0] < 2000 or pulses[0] > 2800:  # ~2.4ms ±400μs
            return {'protocol': 'Unknown', 'reason': 'No Sony AGC'}
        
        logger.debug("Sony AGC detected")
        
        # Decode bits
        data_bits = []
        for i in range(1, len(pulses) - 1, 2):
            low_pulse = pulses[i]
            high_pulse = pulses[i + 1]
            
            if 400 <= low_pulse <= 800:  # ~600μs ±200μs
                if 400 <= high_pulse <= 800:  # Bit 0
                    data_bits.append(0)
                elif 1000 <= high_pulse <= 1400:  # Bit 1
                    data_bits.append(1)
                else:
                    break
            else:
                break
        
        if len(data_bits) >= 12:
            command = self._bits_to_value(data_bits[0:7])  # 7-bit command
            address = self._bits_to_value(data_bits[7:12])  # 5-bit address
            
            logger.info(f"Sony SIRC protocol detected: Address=0x{address:02X}, Command=0x{command:02X}")
            return {
                'protocol': 'Sony',
                'address': address,
                'command': command,
                'code': f"0x{address:02X}{command:02X}",
                'bits_decoded': len(data_bits)
            }
        
        return {'protocol': 'Unknown', 'reason': 'Sony decoding failed'}
    
    def _analyze_rc5_protocol(self, timing_data: list) -> dict:
        """Analyze timing data for RC5 protocol."""
        logger.debug("Attempting RC5 protocol analysis")
        
        # RC5 is Manchester encoded, more complex to decode
        # For now, just check basic characteristics
        
        if len(timing_data) < 28:  # RC5 has 14 bits
            return {'protocol': 'Unknown', 'reason': 'Too few pulses for RC5'}
        
        pulses = [duration for state, duration in timing_data]
        avg_pulse = sum(pulses) // len(pulses)
        
        # RC5 uses ~889μs base timing
        if 700 <= avg_pulse <= 1100:
            logger.info("RC5-like timing detected (basic check)")
            return {
                'protocol': 'RC5',
                'code': 'RC5_DETECTED',
                'note': 'Basic RC5 detection - full decoding not implemented'
            }
        
        return {'protocol': 'Unknown', 'reason': 'No RC5 pattern'}
    
    def _analyze_signal_pattern(self, timing_data: list) -> dict:
        """Analyze general signal patterns for unknown protocols."""
        logger.debug("Performing generic signal pattern analysis")
        
        pulses = [duration for state, duration in timing_data]
        
        if not pulses:
            return {'pattern_type': 'Empty'}
        
        # Basic statistical analysis
        min_pulse = min(pulses)
        max_pulse = max(pulses)
        avg_pulse = sum(pulses) // len(pulses)
        
        # Pattern classification
        if max_pulse > 5000:  # Long initial pulse suggests AGC
            pattern_type = "AGC_BASED"
        elif len(set(pulses)) <= 4:  # Very few unique pulse widths
            pattern_type = "SIMPLE_ENCODING"
        elif avg_pulse < 1000:  # Short pulses
            pattern_type = "HIGH_FREQUENCY"
        else:
            pattern_type = "COMPLEX_ENCODING"
        
        logger.debug(f"Signal pattern classified as: {pattern_type}")
        
        return {
            'pattern_type': pattern_type,
            'pulse_stats': {
                'min': min_pulse,
                'max': max_pulse,
                'avg': avg_pulse,
                'unique_widths': len(set(pulses))
            }
        }
    
    def _bits_to_byte(self, bits: list) -> int:
        """Convert list of bits to byte value (LSB first)."""
        value = 0
        for i, bit in enumerate(bits):
            if bit:
                value |= (1 << i)
        return value
    
    def _bits_to_value(self, bits: list) -> int:
        """Convert list of bits to integer value (MSB first)."""
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        return value
    
    def _generate_signal_fingerprint(self, timing_data: list) -> str:
        """Generate a unique fingerprint for the signal pattern."""
        if not timing_data:
            return "EMPTY"
        
        # Create a simplified pattern representation
        pulses = [duration for state, duration in timing_data]
        
        # Normalize pulses to categories (Short, Medium, Long)
        avg_pulse = sum(pulses) // len(pulses)
        normalized = []
        
        for pulse in pulses[:20]:  # Limit to first 20 pulses for fingerprint
            if pulse < avg_pulse * 0.7:
                normalized.append('S')
            elif pulse > avg_pulse * 1.3:
                normalized.append('L')
            else:
                normalized.append('M')
        
        fingerprint = ''.join(normalized)
        logger.debug(f"Generated signal fingerprint: {fingerprint}")
        return fingerprint
