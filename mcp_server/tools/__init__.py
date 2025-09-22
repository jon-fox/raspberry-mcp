"""Tool exports."""

# Legacy fan control tools (deprecated - use SendIRCommand instead)  
from .ir_control import SendIRCommand
from .ir_control import ListDeviceOperations
from .ir_control import GetMappingGuidance
try:
    from .ir_control import TestIRTransmitter
    _TEST_IR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TestIRTransmitter import failed: {e}")
    _TEST_IR_AVAILABLE = False

# Device registration tools
from .register_devices import StartIRListener, StopIRListener, ClearIREvents, SubmitMappings, GetListenerStatus

__all__ = [
    "SendIRCommand",
    "ListDeviceOperations", 
    "GetMappingGuidance",
    # Device registration
    "StartIRListener",
    "StopIRListener",
    "ClearIREvents", 
    "SubmitMappings",
    "GetListenerStatus",
]

if _TEST_IR_AVAILABLE:
    __all__.append("TestIRTransmitter")
