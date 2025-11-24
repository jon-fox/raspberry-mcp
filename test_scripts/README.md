# Test Scripts

Unified test suite for Raspberry Pi MCP hardware testing.

## Usage

```bash
./test_cli.py --help              # Show help
./test_cli.py ir-loopback         # Test IR TX->RX loopback
./test_cli.py ir-validate         # Validate IR transmission
./test_cli.py climate             # Climate control demo
./test_cli.py all                 # Run all tests
```

## Tests

**ir-loopback** - Verifies IR transmitter (GPIO17) can be detected by receiver (GPIO27)
- Starts IR listener, sends NEC signal, verifies reception
- Use for: hardware setup, debugging TX/RX wiring

**ir-validate** - Validates low-level IR transmission with proper PWM settings
- Tests 38kHz carrier, 50% duty cycle, NEC pattern
- Use for: debugging transmission issues, testing without MCP stack

**climate** - Agent-reactive climate control simulation
- Simulates temperature sensor and AC cooling cycles
- Use for: testing automation logic, demonstrating agent decisions

## Requirements

- Raspberry Pi with GPIO access
- `pigpiod` running: `sudo systemctl start pigpiod`
- IR transmitter on GPIO17, receiver on GPIO27
- DHT22 sensor on GPIO17 (climate test only)
- Dependencies: `uv sync`
