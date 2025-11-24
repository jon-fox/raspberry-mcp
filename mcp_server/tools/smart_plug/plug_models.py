from pydantic import BaseModel, Field


class ControlPlugRequest(BaseModel):
    action: str = Field(
        ...,
        description="Action to perform: 'on', 'off', 'toggle', or 'status'",
    )
    ip: str | None = Field(
        None,
        description="Optional: IP address of the smart plug. If not provided, uses auto-discovery.",
    )


class ControlPlugResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable result message")
    is_on: bool | None = Field(None, description="Current state of the plug (if available)")
    ip: str | None = Field(None, description="IP address of the controlled plug")
