"""Tool exports."""

# Legacy fan control tools (deprecated - use SendIRCommand instead)
from .ir_control import SendIRCommand
from .ir_control import ListDeviceOperations
from .ir_control import GetMappingGuidance
from .ir_control import TroubleshootIR

try:
    from .ir_control import TestIRTransmitter

    _TEST_IR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TestIRTransmitter import failed: {e}")
    _TEST_IR_AVAILABLE = False

# Device registration tools
from .register_devices import (
    StartIRListener,
    StopIRListener,
    ClearIREvents,
    SubmitMappings,
    GetListenerStatus,
)

# Sensor tools
from .humidity_sensor import ReadHumiditySensor
from .photo_sensor import ReadPhotoSensor

# Notification tools
from .notifications import SendNotification

# Simulation tools
from .simulation import SimulateClimate, ControlSimulatedAC, ControlRealAC

__all__ = [
    "SendIRCommand",
    "ListDeviceOperations",
    "GetMappingGuidance",
    "TroubleshootIR",
    # Device registration
    "StartIRListener",
    "StopIRListener",
    "ClearIREvents",
    "SubmitMappings",
    "GetListenerStatus",
    # Sensors
    "ReadHumiditySensor",
    "ReadPhotoSensor",
    # Notifications
    "SendNotification",
    # Simulation
    "SimulateClimate",
    "ControlSimulatedAC",
    "ControlRealAC",
]

if _TEST_IR_AVAILABLE:
    __all__.append("TestIRTransmitter")
