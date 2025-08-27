"""Tool for setting the speed of a fan."""

from typing import Dict, Any
from mcp_server.tools.register_devices.register_models import (
    ConfirmInput,
    ConfirmOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse


class RegisterDevices(Tool):
    """Tool that registers devices."""

    name = "RegisterDevices"
    description = "Registers devices based on a query"
    input_model = ConfirmInput
    output_model = ConfirmOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ConfirmInput) -> ToolResponse:
        """Execute the register devices tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response confirming the registered devices
        """
        output = ConfirmOutput(
            success=True,
            device_key="device_key",
            message="Devices registered successfully",
        )
        return ToolResponse.from_model(output)
