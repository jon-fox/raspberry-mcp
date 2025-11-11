"""Pydantic models for realistic climate control tool."""

from mcp_server.interfaces.tool import BaseToolInput
from pydantic import Field, ConfigDict
from typing import Optional


class ControlRealACInput(BaseToolInput):
    """Request model for controlling real AC with Shelly plug."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"action": "set_target", "target_temp_f": 72.0},
                {"action": "turn_on"},
                {"action": "turn_off"},
                {"action": "status"},
                {"action": "stop_auto"},
            ]
        }
    )

    action: str = Field(
        description=(
            "Action to perform: "
            "'set_target' to enable automatic control with target temperature, "
            "'turn_on' to manually turn on AC (requires simulation enabled), "
            "'turn_off' to manually turn off AC, "
            "'status' to get current state, "
            "'stop_auto' to disable automatic control"
        ),
        examples=["set_target", "turn_on", "turn_off", "status", "stop_auto"],
    )
    
    target_temp_f: Optional[float] = Field(
        default=None,
        description="Target temperature in Fahrenheit (required for 'set_target' action)",
        examples=[70.0, 72.0, 75.0],
        ge=60.0,
        le=85.0,
    )


class ControlRealACOutput(BaseToolInput):
    """Response model for real AC control."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Automatic control enabled, target: 72.0°F",
                    "ac_running": True,
                    "current_temp": 78.5,
                    "target_temp": 72.0,
                    "auto_control_enabled": True,
                }
            ]
        }
    )

    success: bool = Field(
        description="Whether the operation succeeded",
        examples=[True, False],
    )
    
    message: str = Field(
        description="Description of the result",
        examples=["AC turned ON", "Target reached: 72.0°F"],
    )
    
    ac_running: bool = Field(
        default=False,
        description="Current AC state (Shelly plug on/off)",
    )
    
    current_temp: Optional[float] = Field(
        default=None,
        description="Current temperature in Fahrenheit",
        examples=[72.5, 75.0],
    )
    
    target_temp: Optional[float] = Field(
        default=None,
        description="Target temperature in Fahrenheit",
        examples=[72.0, 75.0],
    )
    
    auto_control_enabled: bool = Field(
        default=False,
        description="Whether automatic temperature control is active",
    )
