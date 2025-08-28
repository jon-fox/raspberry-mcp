"""Tool for stopping the IR listener."""

from typing import Dict, Any
from mcp_server.tools.register_devices.register_models import (
    SubmitMappingsInput,
    SubmitMappingsOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse


class SubmitMappings(Tool):
    """Tool that submits the IR mappings"""

    name = "SubmitMappings"
    description = "Submits the button mappings to the IR Codes Received"
    input_model = SubmitMappingsInput
    output_model = SubmitMappingsOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SubmitMappingsInput) -> ToolResponse:
        """Execute the submit mappings tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response confirming the submitted mappings
        """
        output = SubmitMappingsOutput(
            success=True,
            message="IR mappings submitted successfully.",
        )
        return ToolResponse.from_model(output)
