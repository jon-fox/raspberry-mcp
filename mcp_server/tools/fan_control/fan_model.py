from mcp_server.interfaces.tool import BaseToolInput
from pydantic import Field, ConfigDict


class FanOnRequest(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"device_id": "living_room_fan"}, {"device_id": "bedroom_fan"}]
        }
    )

    device_id: str = Field(
        description="The ID of the fan device to turn on",
        examples=["living_room_fan", "bedroom_fan"],
    )


class FanOnResponse(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "message": "Fan turned on successfully"},
                {"success": False, "message": "Fan is already on"},
            ]
        }
    )

    success: bool = Field(
        description="Boolean indicating turning the Fan On was successful/unsuccessful",
        examples=[True, False],
    )
    message: str | None = Field(
        description="Optional message providing additional information about the Fan On request",
        examples=["Fan turned on successfully", "Fan is already on"],
    )


class FanOffRequest(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"device_id": "living_room_fan"}, {"device_id": "bedroom_fan"}]
        }
    )

    device_id: str = Field(
        description="The ID of the fan device to turn off",
        examples=["living_room_fan", "bedroom_fan"],
    )


class FanOffResponse(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "message": "Fan turned off successfully"},
                {"success": False, "message": "Fan is already off"},
            ]
        }
    )

    success: bool = Field(
        description="Boolean indicating turning the Fan Off was successful/unsuccessful",
        examples=[True, False],
    )
    message: str | None = Field(
        description="Optional message providing additional information about the Fan Off request",
        examples=["Fan turned off successfully", "Fan is already off"],
    )


class SetFanSpeedRequest(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_id": "living_room_fan", "speed": 3},
                {"device_id": "bedroom_fan", "speed": 1},
            ]
        }
    )

    device_id: str = Field(
        description="The ID of the fan device to set the speed for",
        examples=["living_room_fan", "bedroom_fan"],
    )
    speed: int = Field(
        description="The speed level to set the fan to", examples=[1, 2, 3, 4, 5]
    )


class SetFanSpeedResponse(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "message": "Fan speed set successfully"},
                {"success": False, "message": "Invalid speed level"},
            ]
        }
    )

    success: bool = Field(
        description="Boolean indicating setting the Fan speed was successful/unsuccessful",
        examples=[True, False],
    )
    message: str | None = Field(
        description="Optional message providing additional information about the Set Fan Speed request",
        examples=["Fan speed set successfully", "Invalid speed level"],
    )
