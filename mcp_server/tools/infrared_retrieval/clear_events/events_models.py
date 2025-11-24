from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class ClearIrEventsInput(BaseToolInput):
    """Clears recent captured presses so the next mapping is unambiguous."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class ClearIrEventsOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"success": True, "message": "IR events cleared."}]
        }
    )
    success: bool = Field(
        ..., description="Whether events were cleared successfully.", examples=[True]
    )
    message: str = Field(
        ..., description="Confirmation message.", examples=["IR events cleared."]
    )
