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
    operations: List[str], 
    ir_events: List[Dict[str, Any]]
) -> bool:
    """Save device mapping to persistent storage.
    
    Args:
        device_key: Unique identifier for the device
        operations: List of operation names in order
        ir_events: List of IR events captured for these operations
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        _ensure_config_dir()
        
        # Load existing devices or create new structure
        devices = _load_devices()
        
        # Create device mapping
        device_mapping = {
            "device_key": device_key,
            "operations": operations,
            "ir_signals": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Map each operation to its corresponding IR event
        for i, (operation, event) in enumerate(zip(operations, ir_events)):
            signal_data = {
                "operation": operation,
                "timestamp": event["timestamp"].isoformat() if hasattr(event["timestamp"], "isoformat") else str(event["timestamp"]),
                "signal_type": event.get("type", "button_press"),
                "sequence_order": i
            }
            device_mapping["ir_signals"].append(signal_data)
        
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
