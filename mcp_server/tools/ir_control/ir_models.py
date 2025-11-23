"""Pydantic models for IR control tools."""

from typing import Optional

from pydantic import Field, ConfigDict

from mcp_server.interfaces.tool import BaseToolInput


class SendIRCommandRequest(BaseToolInput):
    """Request model for sending IR commands to devices."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_id": "living_room_fan", "operation": "power_on"},
                {"device_id": "bedroom_fan", "operation": "power_off"},
                {"device_id": "air_purifier", "operation": "speed_up"},
            ]
        }
    )

    device_id: str = Field(
        description="The ID of the device to control",
        examples=["living_room_fan", "bedroom_fan", "air_purifier"],
    )

    operation: str = Field(
        description="The operation to perform on the device",
        examples=["power_on", "power_off", "speed_up", "speed_down"],
    )


class SendIRCommandResponse(BaseToolInput):
    """Response model for IR command execution."""

    success: bool = Field(description="Whether the IR command was sent successfully")
    message: str = Field(description="Details about the command execution")
    device_id: Optional[str] = Field(default=None, description="The device that was controlled")
    operation: Optional[str] = Field(default=None, description="The operation that was performed")
