from typing import List, Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


# Start IR Listener
class StartIrListenerInput(BaseToolInput):
    """No input needed; the server auto-detects the IR receiver."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class StartIrListenerOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "IR listener started successfully on GPIO pin 27. Press remote buttons to capture signals.",
                }
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether the listener started successfully.", examples=[True]
    )
    message: str = Field(
        ...,
        description="Instructions for the user including which GPIO pin is being used.",
        examples=["IR listener started successfully on GPIO pin 27. Press remote buttons to capture signals."],
    )

# Stop IR Listener
class StopIrListenerInput(BaseToolInput):
    """Stops the background IR listener."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class StopIrListenerOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "message": "IR listener stopped successfully."}
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether the listener stopped successfully.", examples=[True]
    )
    message: str = Field(
        ...,
        description="Confirmation message.",
        examples=["IR listener stopped successfully."],
    )


### Clear IR Events
class ClearIrEventsInput(BaseToolInput):
    """Clears recent captured presses so the next mapping is unambiguous."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class ClearIrEventsOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"success": True, "message": "IR events cleared."}]
        }
    )
    success: bool = Field(
        ..., description="Whether events were cleared successfully.", examples=[True]
    )
    message: str = Field(
        ..., description="Confirmation message.", examples=["IR events cleared."]
    )


# Submit Mappings
class SubmitMappingsInput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_key": "levoit_core300s",
                    "required_operations": ["power_on", "power_off"],
                    "optional_operations": ["speed_up", "speed_down", "timer"],
                    "horizon_s": 20,
                }
            ]
        }
    )
    device_key: str = Field(
        ...,
        description="Unique name for this device profile.",
        examples=["levoit_core300s"],
    )
    required_operations: List[str] = Field(
        ...,
        description="Required operations that must be mapped (power_on and power_off are mandatory). Buttons must be pressed in this exact order.",
        examples=[["power_on", "power_off"]],
    )
    optional_operations: List[str] = Field(
        default_factory=list,
        description="Optional operations to map (e.g., speed controls, timers, modes). Press buttons in this order after required operations.",
        examples=[["speed_up", "speed_down", "timer", "oscillate", "night_mode"]],
    )
    horizon_s: int = Field(
        20, description="How far back to look for presses (seconds).", examples=[20]
    )


class SubmitMappingsOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Mapped 5 operations for 'levoit_core300s': 2 required, 3 optional.",
                    "device_key": "levoit_core300s",
                    "mapped_required": ["power_on", "power_off"],
                    "mapped_optional": ["speed_up", "speed_down", "timer"],
                }
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether mapping succeeded.", examples=[True]
    )
    message: str = Field(
        ...,
        description="Status or error message.",
        examples=["Mapped 5 operations for 'levoit_core300s': 2 required, 3 optional."],
    )
    device_key: Optional[str] = Field(
        None,
        description="Device profile that was updated.",
        examples=["levoit_core300s"],
    )
    mapped_required: List[str] = Field(
        default_factory=list,
        description="Required operations that were successfully bound.",
        examples=[["power_on", "power_off"]],
    )
    mapped_optional: List[str] = Field(
        default_factory=list,
        description="Optional operations that were successfully bound.",
        examples=[["speed_up", "speed_down", "timer"]],
    )


# Get Listener Status
class GetListenerStatusInput(BaseToolInput):
    """Gets detailed status information about the IR listener."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class GetListenerStatusOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "is_listening": True,
                    "gpio_pin": 27,
                    "total_events": 15,
                    "recent_events_1min": 3,
                    "recent_events_5min": 8,
                    "listener_task_active": True,
                    "latest_event_time": "2025-09-10T14:30:25.123456",
                    "message": "IR listener is ACTIVE and working! Captured 15 signals total. Recent activity: 3 signals in last minute, 8 in last 5 minutes."
                }
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether status retrieval succeeded.", examples=[True]
    )
    is_listening: bool = Field(
        ..., description="Whether the IR listener is currently active.", examples=[True]
    )
    gpio_pin: int = Field(
        ..., description="GPIO pin number being monitored.", examples=[27]
    )
    total_events: int = Field(
        ..., description="Total number of IR signals captured since listener started.", examples=[15]
    )
    recent_events_1min: int = Field(
        ..., description="Number of IR signals captured in the last minute.", examples=[3]
    )
    recent_events_5min: int = Field(
        ..., description="Number of IR signals captured in the last 5 minutes.", examples=[8]
    )
    listener_task_active: bool = Field(
        ..., description="Whether the background listener task is running.", examples=[True]
    )
    latest_event_time: Optional[str] = Field(
        None, description="ISO timestamp of the most recent IR signal captured.", examples=["2025-09-10T14:30:25.123456"]
    )
    message: str = Field(
        ...,
        description="Detailed status message with diagnostics and recommendations.",
        examples=["IR listener is ACTIVE and working! Captured 15 signals total. Recent activity: 3 signals in last minute, 8 in last 5 minutes."],
    )
