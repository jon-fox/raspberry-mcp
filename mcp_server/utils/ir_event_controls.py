import asyncio
import time

try:
    import pigpio

    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    pigpio = None


def _send_raw_timing_sync(pi, tx_pin: int, duty_cycle: int, timing_data: list) -> bool:
    """Send IR signal using raw timing data - SYNCHRONOUS."""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"Sending raw timing: {len(timing_data)} pulses")

    try:
        # Send each pulse
        for state, duration_us in timing_data:
            if duration_us <= 0:
                continue

            if state == "low" or state == "mark":
                # Carrier ON
                pi.set_PWM_dutycycle(tx_pin, duty_cycle)
            else:  # 'high', 'space', or anything else
                # Carrier OFF
                pi.set_PWM_dutycycle(tx_pin, 0)

            # Wait for the pulse duration
            time.sleep(duration_us / 1_000_000)

        # Ensure carrier is off at end
        pi.set_PWM_dutycycle(tx_pin, 0)
        logger.info("Raw timing transmission completed")
        return True

    except Exception as e:
        logger.error(f"Raw timing transmission failed: {e}")
        return False


def _send_nec_sync(pi, tx_pin: int, duty_cycle: int, hex_code: str) -> bool:
    """Send NEC protocol IR command - SYNCHRONOUS."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Convert hex to integer
        if hex_code.startswith("0x"):
            code = int(hex_code, 16)
        else:
            code = int(hex_code, 16)

        logger.info(f"Sending NEC code: 0x{code:08X}")

        # NEC timing (microseconds)
        HEADER_MARK = 9000
        HEADER_SPACE = 4500
        BIT_MARK = 560
        ONE_SPACE = 1690
        ZERO_SPACE = 560
        STOP_BIT = 560

        # Send header
        pi.set_PWM_dutycycle(tx_pin, duty_cycle)
        time.sleep(HEADER_MARK / 1_000_000)
        pi.set_PWM_dutycycle(tx_pin, 0)
        time.sleep(HEADER_SPACE / 1_000_000)

        # Send 32 bits
        for i in range(32):
            bit = (code >> (31 - i)) & 1

            # Mark
            pi.set_PWM_dutycycle(tx_pin, duty_cycle)
            time.sleep(BIT_MARK / 1_000_000)

            # Space
            pi.set_PWM_dutycycle(tx_pin, 0)
            if bit:
                time.sleep(ONE_SPACE / 1_000_000)
            else:
                time.sleep(ZERO_SPACE / 1_000_000)

        # Stop bit
        pi.set_PWM_dutycycle(tx_pin, duty_cycle)
        time.sleep(STOP_BIT / 1_000_000)
        pi.set_PWM_dutycycle(tx_pin, 0)

        logger.info("NEC transmission completed")
        return True

    except Exception as e:
        logger.error(f"NEC transmission failed: {e}")
        return False


def _send_sony_sync(pi, tx_pin: int, duty_cycle: int, hex_code: str) -> bool:
    """Send Sony protocol IR command - SYNCHRONOUS."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Convert hex to integer
        if hex_code.startswith("0x"):
            code = int(hex_code, 16)
        else:
            code = int(hex_code, 16)

        logger.info(f"Sending Sony code: 0x{code:08X}")

        # Sony timing (microseconds)
        HEADER_MARK = 2400
        BIT_MARK = 600
        ONE_SPACE = 1200
        ZERO_SPACE = 600

        # Send header
        pi.set_PWM_dutycycle(tx_pin, duty_cycle)
        time.sleep(HEADER_MARK / 1_000_000)
        pi.set_PWM_dutycycle(tx_pin, 0)
        time.sleep(ONE_SPACE / 1_000_000)

        # Send 12 bits (Sony sends LSB first)
        for i in range(12):
            bit = (code >> i) & 1

            # Mark
            pi.set_PWM_dutycycle(tx_pin, duty_cycle)
            time.sleep(BIT_MARK / 1_000_000)

            # Space
            pi.set_PWM_dutycycle(tx_pin, 0)
            if bit:
                time.sleep(ONE_SPACE / 1_000_000)
            else:
                time.sleep(ZERO_SPACE / 1_000_000)

        logger.info("Sony transmission completed")
        return True

    except Exception as e:
        logger.error(f"Sony transmission failed: {e}")
        return False


def ir_send(
    protocol: str,
    hex_code: str,
    raw_timing_data: list | None = None,
    power_boost: bool = False,
    carrier_freq: int = 38000,
) -> tuple[bool, str]:
    """Send IR command using pigpio directly on GPIO17 - SYNCHRONOUS for reliability.

    Simple, direct transmission without async complexity.
    Requires pigpiod service to be running: sudo systemctl start pigpiod

    Args:
        protocol: IR protocol (e.g., 'nec', 'sony', 'rc5', 'generic')
        hex_code: Hexadecimal command code to transmit
        raw_timing_data: Raw timing data for Generic protocols
        power_boost: If True, use maximum power (255/100% duty cycle)
        carrier_freq: Carrier frequency in Hz (default 38000)

    Returns:
        Tuple of (success: bool, message: str)
    """
    import logging

    logger = logging.getLogger(__name__)

    if not PIGPIO_AVAILABLE:
        return (
            False,
            "pigpio not available - IR transmission requires pigpio support (Linux/Raspberry Pi)",
        )

    TX_PIN = 17
    DUTY_CYCLE = 255 if power_boost else 200  # ~78% duty cycle normally

    logger.info(f"IR Send: {protocol} protocol, code {hex_code}")

    pi = None
    try:
        # Connect to pigpio daemon
        pi = pigpio.pi()
        if not pi.connected:
            return (
                False,
                "pigpiod not running. Start with: sudo systemctl start pigpiod",
            )

        # Setup GPIO
        pi.set_mode(TX_PIN, pigpio.OUTPUT)
        pi.set_PWM_frequency(TX_PIN, carrier_freq)
        pi.set_PWM_dutycycle(TX_PIN, 0)  # Start OFF

        success = False

        # Handle different protocols
        if protocol.lower() == "generic" and raw_timing_data:
            success = _send_raw_timing_sync(pi, TX_PIN, DUTY_CYCLE, raw_timing_data)
        elif protocol.lower() == "nec":
            success = _send_nec_sync(pi, TX_PIN, DUTY_CYCLE, hex_code)
        elif protocol.lower() == "sony":
            success = _send_sony_sync(pi, TX_PIN, DUTY_CYCLE, hex_code)
        else:
            # Fallback to raw timing if available, otherwise error
            if raw_timing_data:
                success = _send_raw_timing_sync(pi, TX_PIN, DUTY_CYCLE, raw_timing_data)
            else:
                pi.stop()
                return (
                    False,
                    f"Unsupported protocol '{protocol}' and no raw timing data available",
                )

        # Ensure carrier is off
        pi.set_PWM_dutycycle(TX_PIN, 0)
        pi.stop()

        if success:
            duty_info = "100% power" if power_boost else "78% power"
            if protocol.lower() == "generic" and raw_timing_data:
                return (
                    True,
                    f"Generic IR signal sent ({len(raw_timing_data)} pulses, {duty_info})",
                )
            else:
                return True, f"{protocol.upper()} signal {hex_code} sent ({duty_info})"
        else:
            return False, f"Failed to send {protocol} signal {hex_code}"

    except Exception as e:
        if pi:
            try:
                pi.set_PWM_dutycycle(TX_PIN, 0)
                pi.stop()
            except:
                pass
        return False, f"IR transmission error: {str(e)}"

    except Exception as e:
        try:
            if pi is not None:
                pi.stop()
        except:
            pass
        return False, f"IR send failed: {str(e)}"
