from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


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
