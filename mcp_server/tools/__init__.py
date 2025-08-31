"""Tool exports."""

# Legacy fan control tools (deprecated - use SendIRCommand instead)
from .fan_control import FanOff
from .fan_control import FanOn
from .fan_control import SetFanSpeed

# Device registration tools
from .register_devices import StartIRListener, StopIRListener, ClearIREvents, SubmitMappings

__all__ = [
    # Legacy tools
    "FanOff",
    "FanOn", 
    "SetFanSpeed",
    
    # Device registration
    "StartIRListener",
    "StopIRListener",
    "ClearIREvents", 
    "SubmitMappings",
]
