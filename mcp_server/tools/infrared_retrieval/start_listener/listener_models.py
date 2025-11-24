from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


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
                    "message": "IR listener started successfully on GPIO pin 27. Press remote buttons to capture signals.",
                }
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether the listener started successfully.", examples=[True]
    )
    message: str = Field(
        ...,
        description="Instructions for the user including which GPIO pin is being used.",
        examples=[
            "IR listener started successfully on GPIO pin 27. Press remote buttons to capture signals."
        ],
    )
