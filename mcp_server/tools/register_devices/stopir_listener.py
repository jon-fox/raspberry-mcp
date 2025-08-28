"""Tool for stopping the IR listener."""

from typing import Dict, Any
from mcp_server.tools.register_devices.register_models import (
    StopIrListenerInput,
    StopIrListenerOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse


class StopIRListener(Tool):
    """Tool that stops the IR listener."""

    name = "StopIRListener"
    description = "Stops the IR listener to capture remote control signals"
    input_model = StopIrListenerInput
    output_model = StopIrListenerOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: StopIrListenerInput) -> ToolResponse:
        """Execute the stop IR listener tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response confirming the stop IR listener
        """
        output = StopIrListenerOutput(
            success=True,
            message="IR listener stopped successfully.",
        )
        return ToolResponse.from_model(output)
