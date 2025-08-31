"""Utility for managing device mappings on Raspberry Pi."""

import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_DIR = Path("/home/pi/.raspberry-mcp")
DEVICES_FILE = CONFIG_DIR / "devices.json"

def _ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def _load_devices() -> Dict[str, Any]:
    """Load all devices from storage.
    
    Returns:
        Dictionary of all device mappings
    """
    if not DEVICES_FILE.exists():
        return {}
    
    try:
        with open(DEVICES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_device_mapping(
    device_key: str, 
    required_operations: List[str], 
    optional_operations: List[str],
    ir_events: List[Dict[str, Any]]
) -> bool:
    """Save device mapping to persistent storage.
    
    Args:
        device_key: Unique identifier for the device
        required_operations: List of required operation names (power_on, power_off)
        optional_operations: List of optional operation names (speed controls, volume controls, etc.)
        ir_events: List of IR events captured for these operations
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        _ensure_config_dir()
        
        # Load existing devices or create new structure
        devices = _load_devices()
        
        # Combine operations in order (required first, then optional)
        all_operations = required_operations + optional_operations
        
        # Create device mapping with new structure
        device_mapping = {
            "device_key": device_key,
            "required_operations": required_operations,
            "optional_operations": optional_operations,
            "codes": {},  # This will store operation_name -> IR code mapping
            "protocol": None,  # Will be set from first IR event
            "tx_device": None,  # Will be set from first IR event
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Extract protocol and tx_device from first event (should be consistent)
        if ir_events:
            first_event = ir_events[0]
            device_mapping["protocol"] = first_event.get("protocol", "unknown")
            device_mapping["tx_device"] = first_event.get("tx_device", "unknown")
        
        # Map each operation to its corresponding IR event
        for i, (operation, event) in enumerate(zip(all_operations, ir_events)):
            # Store the IR code directly for easy lookup
            device_mapping["codes"][operation] = event.get("code", event.get("hex_code", ""))
        
        # Update or add device
        devices[device_key] = device_mapping
        
        # Save to file
        with open(DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error saving device mapping: {e}")
        return False

def load_device_mapping(device_key: str) -> Dict[str, Any] | None:
    """Load a specific device mapping.
    
    Args:
        device_key: Device identifier to load
        
    Returns:
        Device mapping dictionary or None if not found
    """
    try:
        devices = _load_devices()
        return devices.get(device_key)
    except Exception as e:
        print(f"Error loading device mapping: {e}")
        return {}

def list_devices() -> List[str]:
    """List all registered device keys.
    
    Returns:
        List of device identifiers
    """
    try:
        devices = _load_devices()
        return list(devices.keys())
    except Exception as e:
        print(f"Error listing devices: {e}")
        return []

def delete_device(device_key: str) -> bool:
    """Delete a device mapping.
    
    Args:
        device_key: Device identifier to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        _ensure_config_dir()
        devices = _load_devices()
        if device_key in devices:
            del devices[device_key]
            with open(DEVICES_FILE, 'w') as f:
                json.dump(devices, f, indent=2)
            return True
        return False
    except Exception as e:
        print(f"Error deleting device: {e}")
        return False
