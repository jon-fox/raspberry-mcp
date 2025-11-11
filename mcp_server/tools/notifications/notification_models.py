from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class SendNotificationInput(BaseToolInput):
    """Input for sending a notification to ntfy.sh."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"message": "Humidity: 75%"},
                {"message": "Temperature alert: 85°F"},
                {"message": "Light detected: Bright"},
                {"message": "Photo sensor: Room is dark"},
            ]
        }
    )

    message: str = Field(
        ...,
        description="The message to send as a notification.",
        examples=[
            "Humidity: 75%",
            "Temperature alert: 85°F",
            "Light detected: Bright",
            "Photo sensor: Room is dark",
        ],
    )


class SendNotificationOutput(BaseToolInput):
    """Output for send notification operation."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Notification sent successfully.",
                }
            ]
        }
    )

    success: bool = Field(
        ...,
        description="Whether the notification was sent successfully.",
        examples=[True],
    )
    message: str = Field(
        ...,
        description="Status message or error description.",
        examples=[
            "Notification sent successfully.",
            "Failed to send notification: Connection timeout",
        ],
    )
