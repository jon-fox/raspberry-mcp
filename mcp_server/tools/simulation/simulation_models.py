"""Simple simulation control tool."""

from typing import Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class SimulateClimateInput(BaseToolInput):
    """Input for climate simulation control."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"action": "enable", "temp_f": 75.0},
                {"action": "adjust_temp", "delta_f": -2.0},
                {"action": "disable"}
            ]
        }
    )
    
    action: str = Field(
        ...,
        description="Action: 'enable' (start simulation), 'adjust_temp' (change temperature), or 'disable' (stop)",
        pattern="^(enable|adjust_temp|disable)$",
        examples=["enable", "adjust_temp", "disable"]
    )
    temp_f: Optional[float] = Field(
        None,
        description="Starting temperature in Fahrenheit (for 'enable' action)",
        ge=32.0,
        le=120.0
    )
    humidity: Optional[float] = Field(
        None,
        description="Starting humidity percentage (for 'enable' action)",
        ge=0.0,
        le=100.0
    )
    delta_f: Optional[float] = Field(
        None,
        description="Temperature change in degrees F (for 'adjust_temp' action, can be negative)",
        ge=-20.0,
        le=20.0
    )


class SimulateClimateOutput(BaseToolInput):
    """Output from simulation control."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "success": True,
                "message": "Simulation enabled at 75°F",
                "current_temp_f": 75.0,
                "current_humidity": 50.0
            }]
        }
    )
    
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Status message")
    current_temp_f: Optional[float] = Field(None, description="Current temperature in Fahrenheit")
    current_humidity: Optional[float] = Field(None, description="Current humidity percentage")
