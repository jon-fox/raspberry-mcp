#!/usr/bin/env python3
"""
Debug script for the IR listener - helps identify why signals aren't being captured.
"""

import asyncio
import logging
import sys
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the mcp_server directory to the path
sys.path.append('/Users/foxj7/Developer_Workspace/raspberry-mcp')

try:
    from mcp_server.services.ir_listener_manager import IRListenerManager
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def debug_ir_listener():
    """Debug the IR listener step by step."""
    print("🔧 IR Listener Debug Tool")
    print("=" * 50)
    
    # Get the listener instance
    listener = IRListenerManager.get_instance()
    listener.enable_debug_logging()
    
    print(f"📍 GPIO Pin: {listener.PIN}")
    print(f"📊 Listening status: {listener.is_listening()}")
    
    # Start the listener
    print("\n1️⃣ Starting IR listener...")
    success, message = await listener.start_listening()
    print(f"   Result: {'✅' if success else '❌'} {message}")
    
    if not success:
        print("❌ Failed to start listener. Check pigpiod is running:")
        print("   sudo systemctl start pigpiod")
        return
    
    # Check status
    print("\n2️⃣ Checking listener status...")
    status = listener.get_listener_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Test GPIO monitoring
    print(f"\n3️⃣ Testing GPIO{listener.PIN} for 5 seconds...")
    print("   Press remote buttons NOW!")
    
    if hasattr(listener, 'test_gpio_monitoring'):
        changes = listener.test_gpio_monitoring(5)
        print(f"   Detected {changes} GPIO state changes")
    
    # Wait for IR signals
    print(f"\n4️⃣ Listening for IR signals for 10 seconds...")
    print("   Press remote buttons repeatedly!")
    
    initial_count = len(listener._ir_events)
    await asyncio.sleep(10)
    final_count = len(listener._ir_events)
    captured_signals = final_count - initial_count
    
    print(f"   Captured {captured_signals} IR signals")
    
    # Show recent events
    if captured_signals > 0:
        print("\n5️⃣ Recent IR events:")
        recent = listener.get_recent_events(15)
        for i, event in enumerate(recent[-5:], 1):  # Show last 5
            analysis = event.get('analysis', {})
            print(f"   Signal {i}: {analysis.get('protocol', 'Unknown')} - {analysis.get('code', 'No code')}")
            print(f"              {event.get('pulse_count', 0)} pulses, {event.get('total_duration_us', 0)}μs")
    else:
        print("\n❌ No IR signals captured!")
        print("\nTroubleshooting checklist:")
        print("1. Is pigpiod running? (sudo systemctl status pigpiod)")
        print("2. Is the IR receiver connected to GPIO27?")
        print("3. Is the IR receiver powered (3.3V or 5V)?")
        print("4. Is the remote working? (test with another device)")
        print("5. Are you close enough to the IR receiver?")
    
    # Stop the listener
    print(f"\n6️⃣ Stopping IR listener...")
    await listener.stop_listening()
    print("   Stopped successfully")

if __name__ == "__main__":
    try:
        asyncio.run(debug_ir_listener())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()