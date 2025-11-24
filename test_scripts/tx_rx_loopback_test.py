#!/usr/bin/env python3
"""
Test script to verify IR transmitter can be detected by receiver.
This replaces the broken loopback test with a direct approach.

GPIO17 = Transmitter (TX)
GPIO27 = Receiver (RX)

Run this to verify the fix works.
"""
import sys
import asyncio
import logging

# Add the parent directory to Python path
sys.path.append("/Users/foxj7/Developer_Workspace/raspberry-mcp")

from mcp_server.utils.ir_event_controls import ir_send
from mcp_server.services.ir_listener_manager import IRListenerManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_transmitter_receiver_loopback():
    """Test that the transmitter can be detected by the receiver."""

    print("=== IR Transmitter -> Receiver Loopback Test ===")
    print("TX: GPIO17 (Pin 11)")
    print("RX: GPIO27 (Pin 13)")
    print()

    print("1. Starting IR listener...")
    manager = IRListenerManager.get_instance()
    success, message = await manager.start_listening()

    if not success:
        print(f"FAILED: Failed to start IR listener: {message}")
        return False

    print(f"SUCCESS: IR listener started: {message}")

    print("2. Clearing previous events...")
    manager.clear_events()

    await asyncio.sleep(1)

    print("3. Sending test IR signal...")
    tx_success, tx_message = await ir_send("nec", "0x12345678")

    if not tx_success:
        print(f"FAILED: Failed to send IR signal: {tx_message}")
        await manager.stop_listening()
        return False

    print(f"SUCCESS: IR signal sent: {tx_message}")

    print("4. Waiting for signal detection...")
    await asyncio.sleep(2)

    recent_events = manager.get_recent_events(10)

    if len(recent_events) == 0:
        print("FAILED: No IR signals detected by receiver!")
        print("   This indicates the transmitter signal is not being received.")
        print("   Possible issues:")
        print("   - TX/RX hardware not properly connected")
        print("   - Wrong carrier frequency")
        print("   - Wrong duty cycle")
        print("   - Pin conflict or GPIO configuration issue")
    else:
        print(f"SUCCESS! Detected {len(recent_events)} IR signal(s)")
        for i, event in enumerate(recent_events):
            analysis = event.get("analysis", {})
            protocol = analysis.get("protocol", "Unknown")
            code = analysis.get("code", "N/A")
            pulse_count = event.get("pulse_count", 0)
            print(
                f"   Signal {i+1}: {protocol} protocol, Code: {code}, {pulse_count} pulses"
            )

    print("5. Stopping IR listener...")
    await manager.stop_listening()

    return len(recent_events) > 0


async def main():
    """Run the loopback test."""
    try:
        success = await test_transmitter_receiver_loopback()

        print("\n" + "=" * 50)
        if success:
            print("LOOPBACK TEST PASSED!")
            print("The transmitter can now be detected by the receiver.")
        else:
            print("LOOPBACK TEST FAILED!")
            print("The receiver cannot detect the transmitter signal.")
        print("=" * 50)

        return success

    except Exception as e:
        print(f"FAILED: Test failed with error: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
