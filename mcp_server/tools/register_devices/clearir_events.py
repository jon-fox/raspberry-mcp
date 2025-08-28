"""Tool for stopping the IR listener."""

from typing import Dict, Any
from mcp_server.tools.register_devices.register_models import (
    ClearIrEventsInput,
    ClearIrEventsOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse


class ClearIREvents(Tool):
    """Tool that clears the IR events"""

    name = "ClearIREvents"
    description = "Clears the IR events sent to the receiver"
    input_model = ClearIrEventsInput
    output_model = ClearIrEventsOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ClearIrEventsInput) -> ToolResponse:
        """Execute the clear IR events tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response confirming the cleared IR events
        """
        output = ClearIrEventsOutput(
            success=True,
            message="IR events cleared successfully.",
        )
        return ToolResponse.from_model(output)
