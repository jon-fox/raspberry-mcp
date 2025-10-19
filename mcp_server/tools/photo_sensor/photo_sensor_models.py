from pydantic import ConfigDict, Field
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
                    "message": "Light detected: Bright",
                }
            ]
        }
    )
    
    success: bool = Field(
        ..., 
        description="Whether the sensor read was successful.", 
        examples=[True]
    )
    is_bright: bool = Field(
        ...,
        description="True if light is detected (bright), False if dark.",
        examples=[True, False],
    )
    message: str = Field(
        ...,
        description="Status message describing the light level.",
        examples=["Light detected: Bright", "Light detected: Dark"],
    )
