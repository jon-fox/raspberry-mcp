from pydantic import Field, ConfigDict
from mcp_server.interfaces.tool import BaseToolInput


class TroubleshootIRRequest(BaseToolInput):
    """Request model for IR troubleshooting."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_id": "living_room_tv", "operation": "power_on"},
            ]
        }
    )

    device_id: str = Field(
        description="The ID of the device to troubleshoot",
        examples=["living_room_tv"],
    )

    operation: str = Field(
        description="The operation to test with different power/frequency settings",
        examples=["power_on", "power_off"],
    )


class TroubleshootIRResponse(BaseToolInput):
    """Response model for IR troubleshooting."""

    success: bool = Field(description="Whether troubleshooting completed")
    message: str = Field(description="Troubleshooting results and recommendations")
    tests_performed: int = Field(description="Number of test transmissions sent")
