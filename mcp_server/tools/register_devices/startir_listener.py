"""Tool for starting the IR listener."""

from typing import Dict, Any
from mcp_server.tools.register_devices.register_models import (
    StartIrListenerInput,
    StartIrListenerOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager

class StartIRListener(Tool):
    """Tool that starts the IR listener."""

    name = "StartIRListener"
    description = "Starts the IR listener to capture remote control signals"
    input_model = StartIrListenerInput
    output_model = StartIrListenerOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: StartIrListenerInput) -> ToolResponse:
        """Execute the start IR listener tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response confirming the start IR listener
        """
        manager = IRListenerManager.get_instance()
        success, message = await manager.start_listening()
        
        output = StartIrListenerOutput(
            success=success,
            message=message,
        )
        return ToolResponse.from_model(output)
