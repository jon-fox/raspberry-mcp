from typing import List, Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


# ── Listener control ──────────────────────────────────────────────────────────
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


# ── Mapping recent presses to operations (no codes exposed) ───────────────────
class SubmitMappingsInput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_key": "levoit_core300s",
                    "operations": ["power_on", "speed_up", "sleep"],
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
    operations: List[str] = Field(
        ...,
        description="Action names in the same order the buttons were pressed.",
        examples=[["power_on", "speed_up", "sleep"]],
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
                    "message": "Mapped 3 operations for 'levoit_core300s'.",
                    "device_key": "levoit_core300s",
                    "mapped_operations": ["power_on", "speed_up", "sleep"],
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
        examples=["Mapped 3 operations for 'levoit_core300s'."],
    )
    device_key: Optional[str] = Field(
        None,
        description="Device profile that was updated.",
        examples=["levoit_core300s"],
    )
    mapped_operations: List[str] = Field(
        default_factory=list,
        description="Operations that were successfully bound.",
        examples=[["power_on", "speed_up", "sleep"]],
    )
