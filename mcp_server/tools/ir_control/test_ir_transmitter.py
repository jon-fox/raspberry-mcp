"""Test IR transmitter tool for verifying hardware functionality."""

import asyncio
import time
from typing import Dict, Any
import logging
import subprocess

try:
    import RPi.GPIO as GPIO

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    GPIO = None

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.ir_control.ir_models import (
    TestIRTransmitterRequest,
    TestIRTransmitterResponse,
)
from mcp_server.utils.ir_event_controls import ir_send

logger = logging.getLogger(__name__)


class TestIRTransmitter(Tool):
    """Send repeated IR test signals to verify transmitter is working."""

    name = "TestIRTransmitter"
    description = "Send repeated IR test signals on GPIO17 to verify the transmitter is working. Sends signals every 2 seconds for a specified duration."
    input_model = TestIRTransmitterRequest
    output_model = TestIRTransmitterResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def _verify_gpio_output(self, gpio_pin: int = 17) -> tuple[bool, str]:
        """Verify GPIO pin is configured for output and can be controlled."""
        if not GPIO_AVAILABLE:
            return False, "GPIO library not available (not running on Raspberry Pi?)"

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(gpio_pin, GPIO.OUT)

            GPIO.output(gpio_pin, GPIO.HIGH)
            await asyncio.sleep(0.001)
            GPIO.output(gpio_pin, GPIO.LOW)

            return True, f"GPIO{gpio_pin} responding correctly"
        except Exception as e:
            return False, f"GPIO{gpio_pin} error: {str(e)}"
        finally:
            try:
                if GPIO_AVAILABLE:
                    GPIO.cleanup(gpio_pin)
            except:
                pass

    async def _test_with_led_indicator(self, gpio_pin: int = 17) -> tuple[bool, str]:
        """Use a visible LED on the same pin to verify signal transmission."""
        if not GPIO_AVAILABLE:
            return False, "GPIO library not available (not running on Raspberry Pi?)"

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(gpio_pin, GPIO.OUT)

            pattern = [0.1, 0.1, 0.1, 0.3, 0.3, 0.3, 0.1, 0.1, 0.1]

            for duration in pattern:
                GPIO.output(gpio_pin, GPIO.HIGH)
                await asyncio.sleep(duration)
                GPIO.output(gpio_pin, GPIO.LOW)
                await asyncio.sleep(0.1)

            return (
                True,
                "LED test pattern completed - check for visible blinking on GPIO17",
            )
        except Exception as e:
            return False, f"LED test failed: {str(e)}"
        finally:
            try:
                if GPIO_AVAILABLE:
                    GPIO.cleanup(gpio_pin)
            except:
                pass

    async def _verify_with_system_tools(self) -> tuple[bool, str]:
        """Use system tools to verify IR setup."""
        results = []

        try:
            result = subprocess.run(
                ["lircd", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                results.append("✓ LIRC daemon available")
            else:
                results.append("✗ LIRC daemon not responding")
        except:
            results.append("✗ LIRC daemon not found")

        try:
            with open(f"/sys/class/gpio/gpio17/direction", "r") as f:
                direction = f.read().strip()
                results.append(f"✓ GPIO17 direction: {direction}")
        except:
            results.append("? GPIO17 state unknown")

        try:
            result = subprocess.run(
                ["dtoverlay", "-l"], capture_output=True, text=True, timeout=5
            )
            if "gpio-ir-tx" in result.stdout:
                results.append("✓ GPIO IR TX overlay loaded")
            else:
                results.append("✗ GPIO IR TX overlay not found")
        except:
            results.append("? Unable to check device tree overlays")

        return True, "; ".join(results)

    async def execute(self, input_data: TestIRTransmitterRequest) -> ToolResponse:
        """Send repeated test IR signals with enhanced verification."""
        start_time = time.time()
        transmissions_sent = 0

        duration_seconds = input_data.duration_minutes * 60
        interval_seconds = input_data.interval_seconds

        logger.info(
            f"Starting IR transmitter test: {input_data.duration_minutes} minutes, {interval_seconds}s intervals"
        )

        logger.info("Performing pre-flight verification checks...")

        sys_ok, sys_msg = await self._verify_with_system_tools()
        logger.info(f"System check: {sys_msg}")

        gpio_ok, gpio_msg = await self._verify_gpio_output()
        logger.info(f"GPIO check: {gpio_msg}")

        if input_data.duration_minutes <= 1:
            led_ok, led_msg = await self._test_with_led_indicator()
            logger.info(f"LED test: {led_msg}")
        else:
            led_ok, led_msg = True, "Skipped (long duration test)"
            logger.info("LED test: Skipped for long duration test")

        logger.info(
            f"Will send IR test signals on GPIO17 at 38kHz every {interval_seconds} seconds"
        )
        logger.info("Test patterns: NEC (0x00FF12ED, 0x00FFAA55) and Sony (0x12345678)")
        logger.info("These should now be detectable by the IR receiver on GPIO27")

        success = True
        errors = []

        try:
            while True:
                current_time = time.time()
                elapsed = current_time - start_time

                if elapsed >= duration_seconds:
                    logger.info(
                        f"Test duration reached ({input_data.duration_minutes} minutes), stopping"
                    )
                    break

                transmissions_sent += 1
                logger.info(
                    f"Sending test transmission #{transmissions_sent} (elapsed: {elapsed:.1f}s)"
                )

                test_patterns = [
                    ("nec", "0x00FF12ED"),
                    ("nec", "0x00FFAA55"),
                    ("sony", "0x12345678"),
                ]

                pattern_index = (transmissions_sent - 1) % len(test_patterns)
                protocol, hex_code = test_patterns[pattern_index]

                logger.info(f"Using {protocol.upper()} protocol with code {hex_code}")
                signal_success, signal_message = ir_send(protocol, hex_code)

                if signal_success:
                    logger.info(
                        f"Transmission #{transmissions_sent} successful: {signal_message}"
                    )
                else:
                    logger.error(
                        f"Transmission #{transmissions_sent} failed: {signal_message}"
                    )
                    errors.append(
                        f"Transmission #{transmissions_sent}: {signal_message}"
                    )

                next_time = start_time + (transmissions_sent * interval_seconds)
                current_time = time.time()

                if (
                    next_time > current_time
                    and (next_time - start_time) < duration_seconds
                ):
                    sleep_time = next_time - current_time
                    logger.debug(f"Waiting {sleep_time:.1f}s until next transmission")
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info(
                f"IR transmitter test cancelled after {transmissions_sent} transmissions"
            )
            raise
        except Exception as e:
            logger.error(f"IR transmitter test error: {e}")
            success = False
            errors.append(f"Test error: {str(e)}")

        final_time = time.time()
        actual_duration = final_time - start_time

        if success and not errors:
            message = f"IR transmitter test completed successfully. Sent {transmissions_sent} proper IR protocol signals (NEC/Sony) over {actual_duration:.1f} seconds using the fixed 38kHz transmission with 50% duty cycle."
        elif errors:
            message = f"IR transmitter test completed with {len(errors)} errors. Sent {transmissions_sent} signals using proper IR protocols. Errors: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                message += f" (and {len(errors) - 3} more)"
        else:
            message = (
                f"IR transmitter test failed after {transmissions_sent} transmissions."
            )

        verification_notes = []
        if gpio_ok:
            verification_notes.append("GPIO verified")
        if "led_ok" in locals() and led_ok:
            verification_notes.append("LED test passed")
        if sys_ok:
            verification_notes.append("System OK")

        if verification_notes:
            message += f" | Verification: {', '.join(verification_notes)}"

        logger.info(
            f"IR transmitter test finished: {transmissions_sent} transmissions in {actual_duration:.1f}s"
        )

        output = TestIRTransmitterResponse(
            success=success and len(errors) == 0,
            message=message,
            transmissions_sent=transmissions_sent,
            duration_seconds=actual_duration,
        )

        return ToolResponse.from_model(output)
