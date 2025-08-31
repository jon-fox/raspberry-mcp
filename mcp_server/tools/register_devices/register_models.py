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
                    "message": "Listening started. Press the buttons you want to capture now.",
                }
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether the listener started successfully.", examples=[True]
    )
    message: str = Field(
        ...,
        description="Instructions for the user.",
        examples=["Listening started. Press the buttons you want to capture now."],
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
