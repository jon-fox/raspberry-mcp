# Raspberry Pi MCP Server Setup Guide

## Prerequisites

- Raspberry Pi 4 (arm64)
- IR receiver connected to GPIO 27
- IR LED transmitter connected to GPIO 17
- Raspberry Pi OS installed with SSH enabled

## Initial Setup

### 1. Configure Raspberry Pi

```bash
# Enable Avahi for .local hostname resolution
sudo apt install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Install and start pigpio daemon (required for IR timing)
sudo apt install -y pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### 2. Development Environment Setup

```bash
# On your local machine
pipx install uv
uv python pin 3.12
uv sync --python 3.12
```

## Deployment Options

### Option A: Docker Deployment (Recommended)

Build and deploy the containerized server:

```bash
# Set your Pi password
export PI_PASSWORD='your_password'

# Deploy using the provided script
./deploy.sh
```

The deployment script handles:
- Building ARM64 Docker image
- Transferring to Raspberry Pi
- Starting container with privileged access for GPIO

### Option B: Direct Installation

```bash
# SSH into Raspberry Pi
ssh user@mcppi.local

# Clone repository and install
git clone <repository>
cd raspberry-mcp
uv sync --python 3.12

# Start server
uv run -m mcp_server.server --host 0.0.0.0 --port 8000
```

## Device Registration Workflow

Interact with the MCP server using natural language through your MCP client (e.g., Claude Desktop). The server exposes tools that can be called conversationally.

### 1. Plan Device Operations

Ask the MCP to get mapping guidance for your device type. This calls the `GetMappingGuidance` tool:

"What operations should I map for a fan?"

Returns suggested operations like `speed_up`, `speed_down`, `oscillate`, etc.

### 2. Start IR Listener

Tell the MCP to start listening for IR signals. This calls the `StartIRListener` tool:

"Start the IR listener"

The listener automatically monitors GPIO 27 and captures signal timing data.

### 3. Capture IR Signals

Press buttons on your remote in this order:
1. Required operations first: `power_on`, `power_off`
2. Optional operations next: `speed_up`, `speed_down`, etc.

Wait 1-2 seconds between button presses.

### 4. Register Device Mappings

Instruct the MCP to register your device with the captured signals. This calls the `SubmitMappings` tool:

"Register the living room fan with power_on and power_off as required operations, and speed_up, speed_down, and oscillate as optional operations. Use the signals captured in the last 20 seconds."

The tool matches captured signals to operations in chronological order. Device configuration is saved to `/home/pi/.raspberry-mcp/devices.json`.

## Device Control

Once devices are registered, control them through natural language commands to the MCP.

### Send Commands

Tell the MCP to control your device. This calls the `SendIRCommand` tool:

"Turn on the living room fan"

Transmits IR signal via GPIO 17 at 38kHz with 78% duty cycle, repeated 5x for reliability.

### List Available Operations

Ask the MCP what operations are available. This calls the `ListDeviceOperations` tool:

"What can I do with the living room fan?"

### Troubleshoot IR Issues

Request troubleshooting if commands aren't working. This calls the `TroubleshootIR` tool:

"Troubleshoot the power_on command for the living room fan"

Tests different power levels and frequencies to identify transmission issues.

## Architecture Overview

### Core Components

- `IRListenerManager`: Singleton service handling IR signal capture using pigpio callbacks with hardware-precise timing
- `ir_event_controls.py`: IR transmission functions supporting NEC, Sony, and generic protocols
- `device_registry.py`: Device configuration persistence

### Signal Processing

1. GPIO callback captures pulse timing data
2. Signal completion detected after 200ms timeout
3. Protocol detection (NEC/Sony) or generic hash-based encoding
4. Storage with normalized timing patterns for replay

### MCP Integration

- `server.py`: FastMCP server with HTTP transport
- `ToolService`: Automatic tool registration and schema generation
- CORS enabled for cross-origin access

## Verification

Ask the MCP to check the listener status to verify signal capture:

"What's the status of the IR listener?"

Request a transmitter test to verify hardware functionality:

"Test the IR transmitter"

## Notes

- All IR timing uses pigpio for microsecond precision
- Docker container requires `--privileged` flag for GPIO access
- Device mappings persist across restarts
- Pattern matching temporarily disabled to prevent false positives
