"""Tool for adding two numbers."""

from typing import Dict, Any
from mcp_server.tools.fan_control.fan_model import FanOnRequest, FanOnResponse
from mcp_server.interfaces.tool import Tool, ToolResponse


class FanOn(Tool):
    """Tool that turns on a fan."""

    name = "FanOn"
    description = "Turns on a fan"
    input_model = FanOnRequest
    output_model = FanOnResponse

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: FanOnRequest) -> ToolResponse:
        """Execute the fan on tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the sum
        """
        output = FanOnResponse(success=True, message="Fan turned on successfully")
        return ToolResponse.from_model(output)
