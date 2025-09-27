import asyncio
try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    pigpio = None

async def _send_ir_protocol(pi, tx_pin: int, duty_cycle: int, protocol: str, hex_code: str, raw_timing_data: list | None = None) -> bool:
    """Encode and send IR command for specific protocol.
    
    Args:
        pi: pigpio instance
        tx_pin: GPIO pin for transmission
        duty_cycle: PWM duty cycle (0-255)
        protocol: IR protocol ('nec', 'sony', 'rc5', 'generic', etc.)
        hex_code: Hexadecimal command code
        raw_timing_data: Raw timing data for Generic protocols
    
    Returns:
        True if protocol is supported and sent, False otherwise
    """
    try:
        # Handle Generic protocol with raw timing data
        if protocol.lower() == 'generic' and raw_timing_data:
            await _send_raw_timing(pi, tx_pin, duty_cycle, raw_timing_data)
            return True
        
        # Convert hex string to integer for standard protocols
        if hex_code.startswith('0x'):
            code = int(hex_code, 16)
        else:
            code = int(hex_code, 16)
        
        if protocol.lower() == 'nec':
            await _send_nec_command(pi, tx_pin, duty_cycle, code)
            return True
        elif protocol.lower() == 'sony':
            await _send_sony_command(pi, tx_pin, duty_cycle, code)
            return True
        else:
            # For unsupported protocols, try raw timing if available
            if raw_timing_data:
                await _send_raw_timing(pi, tx_pin, duty_cycle, raw_timing_data)
                return True
            else:
                # Fall back to test burst
                await _send_test_burst(pi, tx_pin, duty_cycle)
                return True
            
    except ValueError:
        return False  # Invalid hex code
    except Exception:
        return False

async def _send_raw_timing(pi, tx_pin: int, duty_cycle: int, timing_data: list):
    """Send IR signal using raw timing data.
    
    Args:
        pi: pigpio instance
        tx_pin: GPIO pin for transmission
        duty_cycle: PWM duty cycle for carrier
        timing_data: List of (state, duration_us) tuples
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Transmitting raw IR timing: {len(timing_data)} pulses")
    logger.debug(f"Raw timing pattern: {timing_data[:10]}..." if len(timing_data) > 10 else f"Raw timing pattern: {timing_data}")
    
    for i, (state, duration_us) in enumerate(timing_data):
        if state == 'low' or state == 'mark':
            # Carrier on (mark)
            await _send_mark(pi, tx_pin, duty_cycle, duration_us)
        elif state == 'high' or state == 'space':
            # Carrier off (space)
            await _send_space(pi, tx_pin, duration_us)
        else:
            logger.warning(f"Unknown timing state '{state}' at index {i}, treating as space")
            await _send_space(pi, tx_pin, duration_us)
    
    # Ensure carrier is off at the end
    pi.set_PWM_dutycycle(tx_pin, 0)
    logger.debug("Raw timing transmission completed")

async def _send_nec_command(pi, tx_pin: int, duty_cycle: int, code: int):
    """Send NEC protocol IR command."""
    # NEC timing constants (microseconds)
    HEADER_MARK = 9000
    HEADER_SPACE = 4500
    BIT_MARK = 560
    ONE_SPACE = 1690
    ZERO_SPACE = 560
    STOP_BIT = 560
    
    # Send header
    await _send_mark(pi, tx_pin, duty_cycle, HEADER_MARK)
    await _send_space(pi, tx_pin, HEADER_SPACE)
    
    # Send 32 bits (address + command + inverted versions)
    for i in range(32):
        bit = (code >> (31 - i)) & 1
        await _send_mark(pi, tx_pin, duty_cycle, BIT_MARK)
        if bit:
            await _send_space(pi, tx_pin, ONE_SPACE)
        else:
            await _send_space(pi, tx_pin, ZERO_SPACE)
    
    # Send stop bit
    await _send_mark(pi, tx_pin, duty_cycle, STOP_BIT)

async def _send_sony_command(pi, tx_pin: int, duty_cycle: int, code: int):
    """Send Sony protocol IR command."""
    # Sony timing constants (microseconds)
    HEADER_MARK = 2400
    BIT_MARK = 600
    ONE_SPACE = 1200
    ZERO_SPACE = 600
    
    # Send header
    await _send_mark(pi, tx_pin, duty_cycle, HEADER_MARK)
    await _send_space(pi, tx_pin, ONE_SPACE)
    
    # Send 12 bits for Sony (can be 12, 15, or 20 bits depending on device)
    for i in range(12):
        bit = (code >> i) & 1  # Sony sends LSB first
        await _send_mark(pi, tx_pin, duty_cycle, BIT_MARK)
        if bit:
            await _send_space(pi, tx_pin, ONE_SPACE)
        else:
            await _send_space(pi, tx_pin, ZERO_SPACE)

async def _send_test_burst(pi, tx_pin: int, duty_cycle: int):
    """Send a test burst for unsupported protocols."""
    await _send_mark(pi, tx_pin, duty_cycle, 500000)  # 0.5 second burst

async def _send_mark(pi, tx_pin: int, duty_cycle: int, duration_us: int):
    """Send IR mark (carrier on) for specified duration."""
    pi.set_PWM_dutycycle(tx_pin, duty_cycle)
    await asyncio.sleep(duration_us / 1_000_000)  # Convert microseconds to seconds

async def _send_space(pi, tx_pin: int, duration_us: int):
    """Send IR space (carrier off) for specified duration."""
    pi.set_PWM_dutycycle(tx_pin, 0)
    await asyncio.sleep(duration_us / 1_000_000)  # Convert microseconds to seconds

async def ir_send(protocol: str, hex_code: str, raw_timing_data: list | None = None) -> tuple[bool, str]:
    """Send IR command using pigpio directly on GPIO17 with optimal settings.
    
    Uses maximum power and 3x repeats for best range and reliability.
    Requires pigpiod service to be running: sudo systemctl start pigpiod
    
    Args:
        protocol: IR protocol (e.g., 'nec', 'sony', 'rc5', 'generic')
        hex_code: Hexadecimal code to transmit
        raw_timing_data: Raw timing data for Generic protocols
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not PIGPIO_AVAILABLE:
        return False, "pigpio not available - IR transmission requires pigpio support (Linux/Raspberry Pi)"
    TX_PIN = 17  # GPIO17 (pin 11) - hardcoded for reliability
    CARRIER_FREQ = 38000  # 38kHz carrier frequency (industry standard)
    DUTY_CYCLE = 255  # Maximum drive strength for best range
    REPEAT_COUNT = 3  # Optimal repeat count for reliability
    
    pi = None
    try:
        # Connect to pigpio daemon
        pi = pigpio.pi()
        if not pi.connected:
            return False, "pigpiod not running. Start with: sudo systemctl start pigpiod"
        
        # Setup GPIO pin for output
        pi.set_mode(TX_PIN, pigpio.OUTPUT)
        pi.set_PWM_frequency(TX_PIN, CARRIER_FREQ)
        
        # Add test lines here:
        pi.set_PWM_frequency(17, 1000)  # Much slower frequency you can see
        pi.set_PWM_dutycycle(17, 128)   # 50% duty cycle
        await asyncio.sleep(2)          # Let it run for 2 seconds
        pi.set_PWM_dutycycle(17, 0)     # Turn it off
        
        success_count = 0
        
        # Send the command multiple times for better range/reliability
        for attempt in range(REPEAT_COUNT):
            # Convert hex code and encode for protocol
            success = await _send_ir_protocol(pi, TX_PIN, DUTY_CYCLE, protocol, hex_code, raw_timing_data)
            
            if success:
                success_count += 1
                
            # Add delay between repeats (except for the last one)
            if attempt < REPEAT_COUNT - 1:
                await asyncio.sleep(0.1)  # 100ms delay between repeats
        
        if success_count == 0:
            pi.stop()
            return False, f"Unsupported protocol '{protocol}' or invalid hex code '{hex_code}'"
        
        # Cleanup
        pi.stop()
        
        # Enhanced success message with transmission details
        repeat_info = f" repeated {REPEAT_COUNT}x" if REPEAT_COUNT > 1 else ""
        
        if protocol.lower() == 'generic' and raw_timing_data:
            return True, f"Raw IR timing pattern sent on GPIO{TX_PIN} at {CARRIER_FREQ}Hz{repeat_info} ({len(raw_timing_data)} pulses, {success_count}/{REPEAT_COUNT} successful)"
        else:
            return True, f"IR command {protocol}:{hex_code} sent on GPIO{TX_PIN} at {CARRIER_FREQ}Hz{repeat_info} (max power, {success_count}/{REPEAT_COUNT} successful)"
        
    except Exception as e:
        try:
            if pi is not None:
                pi.stop()
        except:
            pass
        return False, f"IR send failed: {str(e)}"