from typing import Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class ClimateSimulationInput(BaseToolInput):
    """Input for climate simulation control."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"action": "enable", "temp_f": 75.0, "humidity": 50.0},
                {"action": "cool_ac", "target_temp_f": 68.0},
                {"action": "adjust_temp", "delta_f": -2.0},
                {"action": "status"},
                {"action": "disable"},
            ]
        }
    )

    action: str = Field(
        ...,
        description="Action: 'enable' (start simulation), 'disable' (stop), 'cool_ac' (AC cools by 2°F), 'adjust_temp' (manual temp change), 'status' (get current state)",
        pattern="^(enable|disable|cool_ac|adjust_temp|status)$",
        examples=["enable", "disable", "cool_ac", "adjust_temp", "status"],
    )
    temp_f: Optional[float] = Field(
        None,
        description="Starting temperature in Fahrenheit (for 'enable' action)",
        ge=32.0,
        le=120.0,
    )
    humidity: Optional[float] = Field(
        None,
        description="Starting humidity percentage (for 'enable' action)",
        ge=0.0,
        le=100.0,
    )
    delta_f: Optional[float] = Field(
        None,
        description="Temperature change in degrees F (for 'adjust_temp' action, can be negative)",
        ge=-20.0,
        le=20.0,
    )
    target_temp_f: Optional[float] = Field(
        None,
        description="Target temperature in Fahrenheit (for 'cool_ac' action)",
        ge=60.0,
        le=85.0,
    )


class ClimateSimulationOutput(BaseToolInput):
    """Output from climate simulation control."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Simulation enabled at 75°F, 50% humidity",
                    "current_temp_f": 75.0,
                    "current_humidity": 50.0,
                }
            ]
        }
    )

    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Status message")
    current_temp_f: Optional[float] = Field(None, description="Current temperature in Fahrenheit")
    current_humidity: Optional[float] = Field(None, description="Current humidity percentage")
    ac_running: Optional[bool] = Field(None, description="Whether AC is running (for cool_ac action)")
    target_temp: Optional[float] = Field(None, description="Target temperature (for cool_ac action)")
