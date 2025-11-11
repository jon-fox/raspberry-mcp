from pydantic import ConfigDict, Field
from typing import Optional
from mcp_server.interfaces.tool import BaseToolInput


class ReadPhotoSensorInput(BaseToolInput):
    """Input for reading light level from photo sensor."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class ReadPhotoSensorOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "is_bright": True,
                    "raw_value": 0,
                    "gpio_pin": 27,
                    "timestamp": "2025-10-22T10:30:45.123456",
                    "message": "Light detected: Bright",
                    "sensor_info": "LM393 digital photo sensor (binary output only)",
                }
            ]
        }
    )

    success: bool = Field(
        ..., description="Whether the sensor read was successful.", examples=[True]
    )
    is_bright: bool = Field(
        ...,
        description="True if light is detected (bright), False if dark.",
        examples=[True, False],
    )
    raw_value: Optional[int] = Field(
        None,
        description="Raw GPIO value (0 or 1). For LM393: 0=bright, 1=dark.",
        examples=[0, 1],
    )
    gpio_pin: Optional[int] = Field(
        None,
        description="GPIO pin number used for reading the sensor.",
        examples=[27, 17],
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when the reading was taken.",
        examples=["2025-10-22T10:30:45.123456"],
    )
    message: str = Field(
        ...,
        description="Status message describing the light level.",
        examples=["Light detected: Bright", "Light detected: Dark"],
    )
    sensor_info: Optional[str] = Field(
        None,
        description="Information about the sensor type and capabilities.",
        examples=["LM393 digital photo sensor (binary output only)"],
    )
