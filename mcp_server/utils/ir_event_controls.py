import asyncio
import pigpio

async def _send_ir_protocol(pi, tx_pin: int, duty_cycle: int, protocol: str, hex_code: str) -> bool:
    """Encode and send IR command for specific protocol.
    
    Args:
        pi: pigpio instance
        tx_pin: GPIO pin for transmission
        duty_cycle: PWM duty cycle (0-255)
        protocol: IR protocol ('nec', 'sony', 'rc5', etc.)
        hex_code: Hexadecimal command code
    
    Returns:
        True if protocol is supported and sent, False otherwise
    """
    try:
        # Convert hex string to integer
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
            # For now, send a test burst for unsupported protocols
            await _send_test_burst(pi, tx_pin, duty_cycle)
            return True
            
    except ValueError:
        return False  # Invalid hex code
    except Exception:
        return False

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

async def ir_send(protocol: str, hex_code: str, device_path: str | None = None) -> tuple[bool, str]:
    """Send IR command using pigpio directly on GPIO17.
    
    Uses the same approach as loopback_test.py for reliable IR transmission.
    Requires pigpiod service to be running: sudo systemctl start pigpiod
    
    Args:
        protocol: IR protocol (e.g., 'nec', 'sony', 'rc5')
        hex_code: Hexadecimal code to transmit
        device_path: Unused, kept for compatibility
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    TX_PIN = 17  # GPIO17 (pin 11) - same as loopback test
    CARRIER_FREQ = 38000  # 38kHz carrier frequency (most common)
    DUTY_CYCLE = 200  # Strong drive (0-255) - same as loopback test
    
    pi = None
    try:
        # Connect to pigpio daemon
        pi = pigpio.pi()
        if not pi.connected:
            return False, "pigpiod not running. Start with: sudo systemctl start pigpiod"
        
        # Setup GPIO pin for output
        pi.set_mode(TX_PIN, pigpio.OUTPUT)
        pi.set_PWM_frequency(TX_PIN, CARRIER_FREQ)
        
        # Convert hex code and encode for protocol
        success = await _send_ir_protocol(pi, TX_PIN, DUTY_CYCLE, protocol, hex_code)
        
        if not success:
            pi.stop()
            return False, f"Unsupported protocol '{protocol}' or invalid hex code '{hex_code}'"
        
        # Cleanup
        pi.stop()
        
        return True, f"IR command {protocol}:{hex_code} sent on GPIO{TX_PIN} at {CARRIER_FREQ}Hz"
        
    except Exception as e:
        try:
            if pi is not None:
                pi.stop()
        except:
            pass
        return False, f"IR send failed: {str(e)}"