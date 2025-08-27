from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput

class ConfirmInput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "lg_55uk6300_nec1",
                },
                {
                    "id": "samsung_qn90a_nec",
                },
            ]
        }
    )

    id: str = Field(
        ...,
        description="The ID of the device to confirm",
        examples=["lg_55uk6300_nec1", "samsung_qn90a_nec"],
    )


class ConfirmOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "device_key": "lg_55uk6300_nec1",
                    "message": "Device confirmed",
                },
                {
                    "success": False,
                    "device_key": "samsung_qn90a_nec",
                    "message": "Device not found",
                },
            ]
        }
    )

    success: bool = Field(
        ...,
        description="Indicates if the confirmation was successful",
        examples=[True, False],
    )
    device_key: str = Field(
        ...,
        description="The unique key of the confirmed device",
        examples=["lg_55uk6300_nec1", "samsung_qn90a_nec"],
    )
    message: str = Field(
        ...,
        description="Additional information about the confirmation process",
        examples=["Device confirmed", "Device not found"],
    )
