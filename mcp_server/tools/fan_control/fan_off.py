"""Tool for adding two numbers."""

from typing import Dict, Any
from mcp_server.tools.fan_control.fan_model import FanOffRequest, FanOffResponse
from mcp_server.interfaces.tool import Tool, ToolResponse


class FanOff(Tool):
    """Tool that turns off a fan."""

    name = "FanOff"
    description = "Turns off a fan"
    input_model = FanOffRequest
    output_model = FanOffResponse

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: FanOffRequest) -> ToolResponse:
        """Execute the fan off tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the sum
        """
        output = FanOffResponse(success=True, message="Fan turned off successfully")
        return ToolResponse.from_model(output)
