# Raspberry Pi MCP Server

Control infrared devices via Raspberry Pi using the Model Context Protocol.

Mainly intended to be used with Claude or Chatgpt (when they finally make mcps easier to use)

## Setup

```bash
# Install dependencies
pipx install uv
uv python pin 3.12
uv sync --python 3.12

# On Raspberry Pi
sudo apt install -y avahi-daemon

# Connect via SSH
ssh user@mcppi.local
```

## Usage

### Register a Device

1. **Get button suggestions**: `GetMappingGuidance` with `device_type`
2. **Start capture**: `StartIrListener`
3. **Press buttons** on your remote (power on/off first, then others)
4. **Register device**: `SubmitMappings` with device name and operations

### Control Devices

```json
{
  "tool": "SendIRCommand",
  "device_id": "living_room_fan",
  "operation": "power_on"
}
```

### Available Operations

**Required**: `power_on`, `power_off`

**Common**: `speed_up`, `speed_down`, `oscillate`, `volume_up`, `volume_down`, `temp_up`, `temp_down`, `auto_mode`

Use `ListDeviceOperations` to see what's available for each device.

## Tools

- `GetMappingGuidance` - Get button suggestions for device types
- `StartIrListener` / `StopIrListener` - Capture IR signals  
- `SubmitMappings` - Register device with operations
- `SendIRCommand` - Control any registered device
- `ListDeviceOperations` - Show available operations

