import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager
from mcp_server.tools.register_devices.register_models import (
    StopIrListenerInput,
    StopIrListenerOutput,
)

logger = logging.getLogger(__name__)


class StopIRListener(Tool):
    """Tool that stops the IR listener."""

    name = "StopIRListener"
    description = (
        "Stops the IR listener that captures remote control signals on GPIO pin 27"
    )
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
        """Execute the stop IR listener tool."""
        manager = IRListenerManager.get_instance()
        success, message = await manager.stop_listening()

        if success:
            logger.info(f"IR listener stopped: {message}")
        else:
            logger.error(f"Failed to stop IR listener: {message}")

        output = StopIrListenerOutput(
            success=success,
            message=message,
        )
        return ToolResponse.from_model(output)
