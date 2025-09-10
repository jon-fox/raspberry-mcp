"""Tool exports."""

# Legacy fan control tools (deprecated - use SendIRCommand instead)
from .ir_control import SendIRCommand
from .ir_control import ListDeviceOperations
from .ir_control import GetMappingGuidance

# Device registration tools
from .register_devices import StartIRListener, StopIRListener, ClearIREvents, SubmitMappings

__all__ = [
    "SendIRCommand",
    "ListDeviceOperations",
    "GetMappingGuidance",
    # Device registration
    "StartIRListener",
    "StopIRListener",
    "ClearIREvents", 
    "SubmitMappings",
]
