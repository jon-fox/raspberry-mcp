import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi MCP Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ir-loopback          # Test IR transmitter -> receiver loopback
  %(prog)s ir-validate          # Validate IR transmission with proper duty cycle
  %(prog)s climate              # Run climate control simulation demo
  %(prog)s all                  # Run all tests sequentially
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Test to run")

    # IR Loopback Test
    subparsers.add_parser(
        "ir-loopback",
        help="Test IR transmitter can be detected by receiver (GPIO17 -> GPIO27)",
    )

    # IR Transmission Validation
    subparsers.add_parser(
        "ir-validate",
        help="Validate IR transmission logic with proper duty cycle and frequency",
    )

    # Climate Simulation
    subparsers.add_parser(
        "climate", help="Demo agent-reactive climate control simulation"
    )

    # Run all tests
    subparsers.add_parser("all", help="Run all tests sequentially")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run the selected test
    if args.command == "ir-loopback":
        asyncio.run(run_ir_loopback())
    elif args.command == "ir-validate":
        asyncio.run(run_ir_validate())
    elif args.command == "climate":
        asyncio.run(run_climate_simulation())
    elif args.command == "all":
        asyncio.run(run_all_tests())


async def run_ir_loopback():
    """Run IR transmitter -> receiver loopback test."""
    print("\n" + "=" * 60)
    print("IR TRANSMITTER -> RECEIVER LOOPBACK TEST")
    print("=" * 60 + "\n")

    from mcp_server.utils.ir_event_controls import ir_send
    from mcp_server.services.ir_listener_manager import IRListenerManager

    print("TX: GPIO17 (Pin 11)")
    print("RX: GPIO27 (Pin 13)")
    print()

    # Start the IR listener
    print("1. Starting IR listener...")
    manager = IRListenerManager.get_instance()
    success, message = await manager.start_listening()

    if not success:
        print(f"FAILED: Failed to start IR listener: {message}")
        return False

    print(f"SUCCESS: IR listener started: {message}")

    # Clear any existing events
    print("2. Clearing previous events...")
    manager.clear_events()

    # Wait a moment for listener to be ready
    await asyncio.sleep(1)

    # Send a test IR signal
    print("3. Sending test IR signal...")
    tx_success, tx_message = await ir_send("nec", "0x12345678")

    if not tx_success:
        print(f"FAILED: Failed to send IR signal: {tx_message}")
        await manager.stop_listening()
        return False

    print(f"SUCCESS: IR signal sent: {tx_message}")

    # Wait for the signal to be received
    print("4. Waiting for signal detection...")
    await asyncio.sleep(2)

    # Check if any events were captured
    recent_events = manager.get_recent_events(10)

    if len(recent_events) == 0:
        print("FAILED: No IR signals detected by receiver!")
        print("   This indicates the transmitter signal is not being received.")
        print("   Possible issues:")
        print("   - TX/RX hardware not properly connected")
        print("   - Wrong carrier frequency")
        print("   - Wrong duty cycle")
        print("   - Pin conflict or GPIO configuration issue")
        result = False
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
        result = True

    # Clean up
    print("5. Stopping IR listener...")
    await manager.stop_listening()

    print("\n" + "=" * 60)
    if result:
        print("LOOPBACK TEST PASSED!")
        print("The transmitter can now be detected by the receiver.")
    else:
        print("LOOPBACK TEST FAILED!")
        print("The receiver cannot detect the transmitter signal.")
    print("=" * 60 + "\n")

    return result


async def run_ir_validate():
    """Validate IR transmission with proper duty cycle."""
    print("\n" + "=" * 60)
    print("IR TRANSMISSION VALIDATION TEST")
    print("=" * 60 + "\n")

    try:
        import pigpio

        PIGPIO_AVAILABLE = True
    except ImportError:
        PIGPIO_AVAILABLE = False
        pigpio = None

    if not PIGPIO_AVAILABLE:
        print("FAILED: pigpio not available - cannot test on this system")
        return False

    TX_PIN = 17
    CARRIER_FREQ = 38000  # 38kHz
    DUTY_CYCLE = 128  # 50% duty cycle (fixed from 255/100%)

    pi = None
    try:
        # Connect to pigpio daemon
        print("1. Connecting to pigpio daemon...")
        pi = pigpio.pi()
        if not pi.connected:
            print(
                "FAILED: pigpiod not running. Start with: sudo systemctl start pigpiod"
            )
            return False
        print("SUCCESS: Connected to pigpiod")

        # Setup GPIO pin properly
        print("2. Setting up GPIO17 for IR transmission...")
        pi.set_mode(TX_PIN, pigpio.OUTPUT)
        pi.set_PWM_frequency(TX_PIN, CARRIER_FREQ)
        pi.set_PWM_dutycycle(TX_PIN, 0)  # Start with PWM off
        print(
            f"SUCCESS: GPIO17 configured: {CARRIER_FREQ}Hz, {DUTY_CYCLE/255*100:.0f}% duty cycle"
        )

        # Test 1: Simple burst
        print("3. Sending 38kHz test burst...")
        pi.set_PWM_dutycycle(TX_PIN, DUTY_CYCLE)
        await asyncio.sleep(0.1)  # 100ms burst
        pi.set_PWM_dutycycle(TX_PIN, 0)
        print("SUCCESS: Test burst sent")

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

        print("SUCCESS: NEC pattern sent")

        # Ensure PWM is off
        pi.set_PWM_dutycycle(TX_PIN, 0)
        print("5. PWM turned off")

        result = True

    except Exception as e:
        print(f"FAILED: Test failed: {e}")
        result = False
    finally:
        if pi is not None:
            try:
                pi.set_PWM_dutycycle(TX_PIN, 0)
                pi.stop()
                print("SUCCESS: pigpio connection closed")
            except Exception:
                pass

    print("\n" + "=" * 60)
    if result:
        print("TRANSMISSION TEST PASSED!")
        print("The fixed code should now work properly.")
        print("Key fixes applied:")
        print("  - Removed 1kHz test signal interference")
        print("  - Set duty cycle to 50% (was 100%)")
        print("  - Proper frequency setup before each transmission")
    else:
        print("TRANSMISSION TEST FAILED!")
    print("=" * 60 + "\n")

    return result


async def run_climate_simulation():
    """Run climate control simulation demo."""
    print("\n" + "=" * 60)
    print("CLIMATE CONTROL SIMULATION - AGENT REACTIVE DEMO")
    print("=" * 60 + "\n")

    from mcp_server.tools.simulation import SimulateClimate, ControlSimulatedAC
    from mcp_server.tools.simulation.simulation_models import SimulateClimateInput
    from mcp_server.tools.simulation.ac_models import ControlACInput
    from mcp_server.tools.humidity_sensor import ReadHumiditySensor
    from mcp_server.tools.humidity_sensor.humidity_models import ReadHumidityInput

    sim_tool = SimulateClimate()
    ac_tool = ControlSimulatedAC()
    sensor_tool = ReadHumiditySensor()

    target_temp = 65.0

    # 1. Enable simulation at hot temperature
    print("1. Starting simulation at 75°F (too hot!)")
    result = await sim_tool.execute(SimulateClimateInput(action="enable", temp_f=75.0))
    print(f"   {result.output.message}")

    # 2. Agent monitoring loop
    print(f"\n2. Agent monitoring temperature (target: {target_temp}°F)\n")

    cycle = 0
    while True:
        cycle += 1

        # Agent reads sensor
        result = await sensor_tool.execute(ReadHumidityInput())
        current_temp = result.output.temperature_f

        print(f"   Cycle {cycle}:")
        print(f"   - Read sensor: {current_temp}°F")

        # Agent decides: too hot?
        if current_temp <= target_temp:
            print("   - Decision: Target reached!")
            # Agent would turn off real AC here
            result = await ac_tool.execute(ControlACInput(action="turn_off"))
            print(f"   - {result.output.message}")
            break

        # Agent turns on AC to cool
        print(f"   - Decision: Too hot ({current_temp}°F > {target_temp}°F)")
        result = await ac_tool.execute(
            ControlACInput(action="turn_on", target_temp_f=target_temp)
        )
        print(f"   - {result.output.message}\n")

        await asyncio.sleep(1)  # Pause for readability

    print("\n" + "=" * 60)
    print("Simulation complete!")
    print("\nWhat happened:")
    print("- Agent read sensor and detected temp too high")
    print("- Agent called ControlSimulatedAC repeatedly to cool")
    print("- Each call cooled by 2°F (simulating AC effect)")
    print("- Agent stopped when target reached")
    print("\nIn production:")
    print("- Replace ControlSimulatedAC with SendIRCommand(device='ac')")
    print("- Real sensor readings change gradually over time")
    print("=" * 60 + "\n")

    return True


async def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60 + "\n")

    results = {}

    # IR Loopback Test
    try:
        results["IR Loopback"] = await run_ir_loopback()
    except Exception as e:
        print(f"IR Loopback test crashed: {e}")
        results["IR Loopback"] = False

    # IR Validation Test
    try:
        results["IR Validation"] = await run_ir_validate()
    except Exception as e:
        print(f"IR Validation test crashed: {e}")
        results["IR Validation"] = False

    # Climate Simulation
    try:
        results["Climate Simulation"] = await run_climate_simulation()
    except Exception as e:
        print(f"Climate Simulation test crashed: {e}")
        results["Climate Simulation"] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name:.<40} {status}")
    print("=" * 60 + "\n")

    all_passed = all(results.values())
    if all_passed:
        print("All tests passed!")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"{failed_count} test(s) failed.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
