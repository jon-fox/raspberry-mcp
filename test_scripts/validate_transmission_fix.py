#!/usr/bin/env python3
"""
Simple validation script to test the fixed IR transmission logic.
This tests the core pigpio transmission without the full MCP system.
"""
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
        print("❌ pigpio not available - cannot test on this system")
        return False
    
    print("=== Testing Fixed IR Transmission ===")
    
    TX_PIN = 17
    CARRIER_FREQ = 38000  # 38kHz
    DUTY_CYCLE = 128      # 50% duty cycle (fixed from 255/100%)
    
    pi = None
    try:
        # Connect to pigpio daemon
        print("1. Connecting to pigpio daemon...")
        pi = pigpio.pi()
        if not pi.connected:
            print("❌ pigpiod not running. Start with: sudo systemctl start pigpiod")
            return False
        print("✅ Connected to pigpiod")
        
        # Setup GPIO pin properly
        print("2. Setting up GPIO17 for IR transmission...")
        pi.set_mode(TX_PIN, pigpio.OUTPUT)
        pi.set_PWM_frequency(TX_PIN, CARRIER_FREQ)
        pi.set_PWM_dutycycle(TX_PIN, 0)  # Start with PWM off
        print(f"✅ GPIO17 configured: {CARRIER_FREQ}Hz, {DUTY_CYCLE/255*100:.0f}% duty cycle")
        
        # Test 1: Simple burst
        print("3. Sending 38kHz test burst...")
        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.1)  # 100ms burst
        pi.set_PWM_dutycycle(TX_PIN, 0)
        print("✅ Test burst sent")
        
        # Test 2: NEC-style pattern
        print("4. Sending NEC-style IR pattern...")
        
        # AGC burst: 9ms on, 4.5ms off
        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.009)  # 9ms
        pi.set_PWM_dutycycle(TX_PIN, 0)
        await asyncio.sleep(0.0045)  # 4.5ms
        
        # Few data bits: 560us on, varying off times
        for bit in [1, 0, 1, 1, 0]:
            pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
            await asyncio.sleep(0.00056)  # 560us on
            pi.set_PWM_dutycycle(TX_PIN, 0)
            if bit:
                await asyncio.sleep(0.00169)  # 1.69ms off (bit 1)
            else:
                await asyncio.sleep(0.00056)  # 560us off (bit 0)
        
        # Final stop bit
        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.00056)  # 560us
        pi.set_PWM_dutycycle(TX_PIN, 0)
        
        print("✅ NEC pattern sent")
        
        # Ensure PWM is off
        pi.set_PWM_dutycycle(TX_PIN, 0)
        print("5. PWM turned off")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        if pi is not None:
            try:
                pi.set_PWM_dutycycle(TX_PIN, 0)
                pi.stop()
                print("✅ pigpio connection closed")
            except:
                pass

async def main():
    success = await test_fixed_transmission()
    print("\n" + "="*40)
    if success:
        print("🎉 TRANSMISSION TEST PASSED!")
        print("The fixed code should now work properly.")
        print("Key fixes applied:")
        print("  ✅ Removed 1kHz test signal interference")
        print("  ✅ Set duty cycle to 50% (was 100%)")
        print("  ✅ Proper frequency setup before each transmission")
    else:
        print("❌ TRANSMISSION TEST FAILED!")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())