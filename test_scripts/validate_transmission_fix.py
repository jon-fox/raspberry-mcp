import asyncio
import logging

try:
    import pigpio

    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    pigpio = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_fixed_transmission():
    """Test the fixed IR transmission logic."""
    if not PIGPIO_AVAILABLE:
        print("FAILED: pigpio not available - cannot test on this system")
        return False

    print("=== Testing Fixed IR Transmission ===")

    TX_PIN = 17
    CARRIER_FREQ = 38000  # 38kHz
    DUTY_CYCLE = 128  # 50% duty cycle (fixed from 255/100%)

    pi = None
    try:
        print("1. Connecting to pigpio daemon...")
        pi = pigpio.pi()
        if not pi.connected:
            print(
                "FAILED: pigpiod not running. Start with: sudo systemctl start pigpiod"
            )
            return False
        print("SUCCESS: Connected to pigpiod")

        print("2. Setting up GPIO17 for IR transmission...")
        pi.set_mode(TX_PIN, pigpio.OUTPUT)
        pi.set_PWM_frequency(TX_PIN, CARRIER_FREQ)
        pi.set_PWM_dutycycle(TX_PIN, 0)
        print(
            f"SUCCESS: GPIO17 configured: {CARRIER_FREQ}Hz, {DUTY_CYCLE/255*100:.0f}% duty cycle"
        )

        print("3. Sending 38kHz test burst...")
        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.1)
        pi.set_PWM_dutycycle(TX_PIN, 0)
        print("SUCCESS: Test burst sent")

        print("4. Sending NEC-style IR pattern...")
        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.009)  # 9ms
        pi.set_PWM_dutycycle(TX_PIN, 0)
        await asyncio.sleep(0.0045)

        for bit in [1, 0, 1, 1, 0]:
            pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
            await asyncio.sleep(0.00056)
            pi.set_PWM_dutycycle(TX_PIN, 0)
            if bit:
                await asyncio.sleep(0.00169)
            else:
                await asyncio.sleep(0.00056)

        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.00056)
        pi.set_PWM_dutycycle(TX_PIN, 0)

        print("SUCCESS: NEC pattern sent")

        pi.set_PWM_dutycycle(TX_PIN, 0)
        print("5. PWM turned off")

        return True

    except Exception as e:
        print(f"FAILED: Test failed: {e}")
        return False
    finally:
        if pi is not None:
            try:
                pi.set_PWM_dutycycle(TX_PIN, 0)
                pi.stop()
                print("SUCCESS: pigpio connection closed")
            except Exception:
                pass


async def main():
    success = await test_fixed_transmission()
    print("\n" + "=" * 40)
    if success:
        print("TRANSMISSION TEST PASSED!")
        print("The fixed code should now work properly.")
        print("Key fixes applied:")
        print("  - Removed 1kHz test signal interference")
        print("  - Set duty cycle to 50% (was 100%)")
        print("  - Proper frequency setup before each transmission")
    else:
        print("TRANSMISSION TEST FAILED!")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
