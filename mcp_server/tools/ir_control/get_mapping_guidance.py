"""Tool for providing guidance on IR device mapping."""

import logging
from typing import Dict, Any, List

from pydantic import Field, ConfigDict

from mcp_server.interfaces.tool import Tool, ToolResponse, BaseToolInput

logger = logging.getLogger(__name__)


class GetMappingGuidanceRequest(BaseToolInput):
    """Request model for getting device mapping guidance."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_type": "fan"},
                {"device_type": "air_purifier"},
                {"device_type": "tv"},
                {},  # No device type specified
            ]
        }
    )

    device_type: str = Field(
        default="generic",
        description="Type of device you're mapping (fan, air_purifier, tv, climate, generic)",
        examples=["fan", "air_purifier", "tv", "climate", "generic"],
    )


class GetMappingGuidanceResponse(BaseToolInput):
    """Response model for device mapping guidance."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_type": "fan",
                    "required_operations": ["power_on", "power_off"],
                    "suggested_optional_operations": [
                        "speed_up",
                        "speed_down",
                        "oscillate",
                        "timer",
                    ],
                    "guidance": "For fans, power control is essential. Speed controls and oscillation are common optional features.",
                    "example_mapping_order": [
                        "power_on",
                        "power_off",
                        "speed_up",
                        "speed_down",
                        "oscillate",
                    ],
                }
            ]
        }
    )

    device_type: str = Field(
        description="The device type this guidance is for",
        examples=["fan"],
    )

    required_operations: List[str] = Field(
        description="Operations that must be mapped for all devices",
        examples=[["power_on", "power_off"]],
    )

    suggested_optional_operations: List[str] = Field(
        description="Commonly useful operations for this device type",
        examples=[["speed_up", "speed_down", "oscillate", "timer"]],
    )

    guidance: str = Field(
        description="Human-readable guidance for mapping this device type",
        examples=[
            "For fans, power control is essential. Speed controls and oscillation are common optional features."
        ],
    )

    example_mapping_order: List[str] = Field(
        description="Example order to press buttons during mapping",
        examples=[["power_on", "power_off", "speed_up", "speed_down", "oscillate"]],
    )


class GetMappingGuidance(Tool):
    """Tool that provides guidance on how to map different types of IR devices."""

    name = "GetMappingGuidance"
    description = "Provides guidance on how to map IR devices, including suggested operations for different device types"
    input_model = GetMappingGuidanceRequest
    output_model = GetMappingGuidanceResponse

    # Device-specific operation suggestions
    DEVICE_SUGGESTIONS = {
        "fan": {
            "suggested_optional": [
                "speed_up",
                "speed_down",
                "speed_1",
                "speed_2",
                "speed_3",
                "oscillate",
                "timer",
                "sleep_mode",
            ],
            "guidance": "For fans, power control is essential. Speed controls (up/down or specific levels), oscillation, and timer functions are common. Some fans also have sleep modes for quieter operation.",
            "example_order": [
                "power_on",
                "power_off",
                "speed_up",
                "speed_down",
                "oscillate",
                "timer",
            ],
        },
        "air_purifier": {
            "suggested_optional": [
                "speed_up",
                "speed_down",
                "auto_mode",
                "sleep_mode",
                "filter_reset",
                "ionizer",
                "night_light",
            ],
            "guidance": "Air purifiers typically need power and speed controls. Auto mode adjusts speed based on air quality. Sleep mode reduces noise. Some have ionizers and filter reset functions.",
            "example_order": [
                "power_on",
                "power_off",
                "auto_mode",
                "speed_up",
                "speed_down",
                "sleep_mode",
            ],
        },
        "tv": {
            "suggested_optional": [
                "volume_up",
                "volume_down",
                "channel_up",
                "channel_down",
                "mute",
                "input",
                "menu",
            ],
            "guidance": "TVs need power control and typically benefit from volume, channel, and input controls. Mute and menu access are commonly used functions.",
            "example_order": [
                "power_on",
                "power_off",
                "volume_up",
                "volume_down",
                "mute",
                "input",
            ],
        },
        "climate": {
            "suggested_optional": [
                "temp_up",
                "temp_down",
                "mode_cool",
                "mode_heat",
                "mode_auto",
                "fan_auto",
                "timer",
            ],
            "guidance": "Climate devices (AC/heater) need power and temperature controls. Different modes (cool/heat/auto) and fan settings are essential for proper operation.",
            "example_order": [
                "power_on",
                "power_off",
                "temp_up",
                "temp_down",
                "mode_cool",
                "mode_heat",
            ],
        },
        "generic": {
            "suggested_optional": [
                "speed_up",
                "speed_down",
                "mode_1",
                "mode_2",
                "timer",
                "settings",
            ],
            "guidance": "For unknown device types, start with power controls (required) and add common functions like speed/mode controls, timers, and settings access as needed.",
            "example_order": ["power_on", "power_off", "mode_1", "mode_2", "timer"],
        },
    }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: GetMappingGuidanceRequest) -> ToolResponse:
        """Execute the mapping guidance tool."""
        device_type = input_data.device_type.lower()

        suggestions = self.DEVICE_SUGGESTIONS.get(
            device_type, self.DEVICE_SUGGESTIONS["generic"]
        )

        if device_type not in self.DEVICE_SUGGESTIONS:
            device_type = "generic"

        required_operations = ["power_on", "power_off"]

        output = GetMappingGuidanceResponse(
            device_type=device_type,
            required_operations=required_operations,
            suggested_optional_operations=suggestions["suggested_optional"],
            guidance=suggestions["guidance"],
            example_mapping_order=suggestions["example_order"],
        )

        return ToolResponse.from_model(output)
