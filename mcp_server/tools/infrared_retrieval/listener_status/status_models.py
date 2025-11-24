from typing import Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class GetListenerStatusInput(BaseToolInput):
    """Gets detailed status information about the IR listener."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class GetListenerStatusOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "is_listening": True,
                    "gpio_pin": 27,
                    "total_events": 15,
                    "recent_events_1min": 3,
                    "recent_events_5min": 8,
                    "listener_task_active": True,
                    "latest_event_time": "2025-09-10T14:30:25.123456",
                    "message": "IR listener is ACTIVE and working! Captured 15 signals total. Recent activity: 3 signals in last minute, 8 in last 5 minutes.",
                }
            ]
        }
    )
    success: bool = Field(
        ..., description="Whether status retrieval succeeded.", examples=[True]
    )
    is_listening: bool = Field(
        ..., description="Whether the IR listener is currently active.", examples=[True]
    )
    gpio_pin: int = Field(
        ..., description="GPIO pin number being monitored.", examples=[27]
    )
    total_events: int = Field(
        ...,
        description="Total number of IR signals captured since listener started.",
        examples=[15],
    )
    recent_events_1min: int = Field(
        ...,
        description="Number of IR signals captured in the last minute.",
        examples=[3],
    )
    recent_events_5min: int = Field(
        ...,
        description="Number of IR signals captured in the last 5 minutes.",
        examples=[8],
    )
    listener_task_active: bool = Field(
        ...,
        description="Whether the background listener task is running.",
        examples=[True],
    )
    latest_event_time: Optional[str] = Field(
        None,
        description="ISO timestamp of the most recent IR signal captured.",
        examples=["2025-09-10T14:30:25.123456"],
    )
    message: str = Field(
        ...,
        description="Detailed status message with diagnostics and recommendations.",
        examples=[
            "IR listener is ACTIVE and working! Captured 15 signals total. Recent activity: 3 signals in last minute, 8 in last 5 minutes."
        ],
    )
