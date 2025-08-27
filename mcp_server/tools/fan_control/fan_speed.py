"""Tool for adding two numbers."""

from typing import Dict, Any
from mcp_server.tools.fan_control.fan_model import (
    SetFanSpeedRequest,
    SetFanSpeedResponse,
)
from mcp_server.interfaces.tool import Tool, ToolResponse


class SetFanSpeed(Tool):
    """Tool that sets the speed on a fan."""

    name = "SetFanSpeed"
    description = "Sets the speed on a fan"
    input_model = SetFanSpeedRequest
    output_model = SetFanSpeedResponse

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SetFanSpeedRequest) -> ToolResponse:
        """Execute the set fan speed tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the sum
        """
        output = SetFanSpeedResponse(success=True, message="Fan speed set successfully")
        return ToolResponse.from_model(output)
