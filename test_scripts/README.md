# Test Scripts

Unified test suite for Raspberry Pi MCP hardware and functionality testing.

## Quick Start

Run the unified test CLI:

```bash
# Show all available tests
./test_cli.py --help

# Run individual tests
./test_cli.py ir-loopback       # Test IR TX -> RX loopback
./test_cli.py ir-validate       # Validate IR transmission
./test_cli.py climate           # Climate simulation demo

# Run all tests
./test_cli.py all
```

## Available Tests

### IR Loopback Test (`ir-loopback`)
Tests that the IR transmitter (GPIO17) can be detected by the IR receiver (GPIO27).

**What it does:**
- Starts the IR listener service
- Sends a test NEC IR signal
- Verifies the receiver detects the signal
- Reports pulse count and protocol analysis

**Use when:**
- Setting up new hardware
- Debugging IR transmission issues
- Verifying TX/RX wiring

**Source:** Consolidated from `tx_rx_loopback_test.py`

### IR Validation Test (`ir-validate`)
Validates the IR transmission logic with proper PWM duty cycle and frequency.

**What it does:**
- Connects directly to pigpio daemon
- Configures GPIO17 with 38kHz carrier, 50% duty cycle
- Sends test burst and NEC-style pattern
- Validates proper PWM cleanup

**Use when:**
- Debugging low-level IR transmission
- Validating duty cycle fixes
- Testing without the full MCP stack

**Source:** Consolidated from `validate_transmission_fix.py`

### Climate Simulation (`climate`)
Demonstrates agent-reactive climate control using simulated sensors and AC.

**What it does:**
- Enables climate simulation at 75°F
- Agent reads sensor and decides if AC is needed
- Simulates AC cooling effect (2°F per cycle)
- Continues until target temperature (65°F) reached

**Use when:**
- Testing AC automation logic
- Demonstrating agent decision-making
- Developing climate control features

**Source:** Consolidated from `test_climate_simulation.py`

## Individual Test Scripts

If you need to run tests individually (outside the CLI):

```bash
# IR loopback test
./tx_rx_loopback_test.py

# IR validation test
./validate_transmission_fix.py

# Climate simulation demo
python3 test_climate_simulation.py
```

## Removed Scripts

The following obsolete scripts were removed during consolidation:

- `loopback_test.py` - Basic pigpio loopback (superseded by tx_rx_loopback_test.py)
- `test_emitter.py` - Simple LED blink test (not IR-specific)
- `test_ir.py` - Basic IR receiver test (doesn't use MCP system)
- `test_ir_transmitter.py` - Tool class in wrong directory (redundant with TroubleshootIR)
- `full_decoder.txt` - Text file (not a script)

## Troubleshooting Tool

The IR troubleshooting tool has been moved to the proper location:

**Location:** `mcp_server/tools/ir_control/troubleshoot_ir.py`

This is an MCP tool (not a standalone script) that tests different power levels and carrier frequencies to diagnose IR device control issues.

## Requirements

- Raspberry Pi with GPIO access
- pigpio daemon running (`sudo systemctl start pigpiod`)
- IR transmitter on GPIO17
- IR receiver on GPIO27
- DHT22 sensor on GPIO17 (for climate tests)
- Proper Python dependencies installed (`uv sync`)
