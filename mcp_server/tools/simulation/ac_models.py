from typing import Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class ControlACInput(BaseToolInput):
    """Input for controlling the simulated AC."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"action": "turn_on", "target_temp_f": 65.0},
                {"action": "turn_off"},
                {"action": "status"},
            ]
        }
    )

    action: str = Field(
        ...,
        description="Action: 'turn_on' (with target_temp_f), 'turn_off', or 'status'",
        pattern="^(turn_on|turn_off|status)$",
        examples=["turn_on", "turn_off", "status"],
    )
    target_temp_f: Optional[float] = Field(
        None,
        description="Target temperature in Fahrenheit (required for turn_on)",
        ge=60.0,
        le=85.0,
    )


class ControlACOutput(BaseToolInput):
    """Output from AC control."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "AC turned ON, will cool to 65.0°F",
                    "ac_running": True,
                    "target_temp": 65.0,
                    "current_temp": 70.0,
                }
            ]
        }
    )

    success: bool = Field(..., description="Whether the command was successful")
    message: str = Field(..., description="Status message")
    ac_running: bool = Field(..., description="Whether AC is currently running")
    target_temp: Optional[float] = Field(None, description="Target temperature")
    current_temp: Optional[float] = Field(None, description="Current temperature")
