"""Pydantic models for IR control tools."""

from mcp_server.interfaces.tool import BaseToolInput
from pydantic import Field, ConfigDict
from typing import List, Optional


class SendIRCommandRequest(BaseToolInput):
    """Request model for sending IR commands to devices."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_id": "living_room_fan", "operation": "power_on"},
                {"device_id": "bedroom_fan", "operation": "power_off"},
                {"device_id": "air_purifier", "operation": "speed_up"},
                {"device_id": "tv", "operation": "volume_down"},
            ]
        }
    )

    device_id: str = Field(
        description="The ID of the device to control",
        examples=["living_room_fan", "bedroom_fan", "air_purifier"],
    )

    operation: str = Field(
        description="The operation to perform on the device (e.g., power_on, power_off, speed_up, etc.)",
        examples=[
            "power_on",
            "power_off",
            "speed_up",
            "speed_down",
            "timer",
            "oscillate",
        ],
    )


class SendIRCommandResponse(BaseToolInput):
    """Response model for IR command execution."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Command 'power_on' sent successfully to 'living_room_fan'",
                },
                {"success": False, "message": "Device 'unknown_device' not found"},
                {
                    "success": False,
                    "message": "Operation 'invalid_op' not available for device 'fan1'",
                },
            ]
        }
    )

    success: bool = Field(
        description="Boolean indicating whether the IR command was sent successfully",
        examples=[True, False],
    )

    message: str = Field(
        description="Message providing details about the command execution",
        examples=[
            "Command 'power_on' sent successfully to 'living_room_fan'",
            "Device 'unknown_device' not found",
            "Operation 'invalid_op' not available for device 'fan1'",
        ],
    )

    device_id: Optional[str] = Field(
        default=None,
        description="The device that was controlled",
        examples=["living_room_fan"],
    )

    operation: Optional[str] = Field(
        default=None,
        description="The operation that was performed",
        examples=["power_on"],
    )


class ListDeviceOperationsRequest(BaseToolInput):
    """Request model for listing available operations for a device."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_id": "living_room_fan"},
                {"device_id": "air_purifier"},
            ]
        }
    )

    device_id: str = Field(
        description="The ID of the device to list operations for",
        examples=["living_room_fan", "air_purifier"],
    )


class ListDeviceOperationsResponse(BaseToolInput):
    """Response model for listing device operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "device_id": "living_room_fan",
                    "required_operations": ["power_on", "power_off"],
                    "optional_operations": ["speed_up", "speed_down", "oscillate"],
                    "message": "Device 'living_room_fan' has 2 required and 3 optional operations",
                }
            ]
        }
    )

    success: bool = Field(
        description="Boolean indicating whether the device was found",
        examples=[True, False],
    )

    device_id: str = Field(
        description="The device that was queried",
        examples=["living_room_fan"],
    )

    required_operations: List[str] = Field(
        default_factory=list,
        description="List of required operations available for this device",
        examples=[["power_on", "power_off"]],
    )

    optional_operations: List[str] = Field(
        default_factory=list,
        description="List of optional operations available for this device",
        examples=[["speed_up", "speed_down", "oscillate", "timer"]],
    )

    message: str = Field(
        description="Message providing details about the available operations",
        examples=["Device 'living_room_fan' has 2 required and 3 optional operations"],
    )


class TestIRTransmitterRequest(BaseToolInput):
    """Request model for testing IR transmitter."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"duration_minutes": 2, "interval_seconds": 2},
                {"duration_minutes": 5, "interval_seconds": 1},
                {},  # Use defaults
            ]
        }
    )

    duration_minutes: float = Field(
        default=2.0,
        description="How long to run the test in minutes (max 10 minutes)",
        ge=0.1,
        le=10.0,
    )
    interval_seconds: float = Field(
        default=2.0,
        description="Interval between transmissions in seconds",
        ge=0.5,
        le=30.0,
    )


class TestIRTransmitterResponse(BaseToolInput):
    """Response model for IR transmitter test."""

    success: bool = Field(description="Whether IR transmissions completed successfully")
    message: str = Field(description="Test result details")
    transmissions_sent: int = Field(description="Number of test signals transmitted")
    duration_seconds: float = Field(
        description="Actual duration of the test in seconds"
    )
