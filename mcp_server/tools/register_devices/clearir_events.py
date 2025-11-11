"""Tool for clearing IR events."""

from typing import Dict, Any
import logging

from mcp_server.tools.register_devices.register_models import (
    ClearIrEventsInput,
    ClearIrEventsOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager

logger = logging.getLogger(__name__)


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
        logger.info("Clearing IR events from listener manager")
        manager = IRListenerManager.get_instance()

        # Get count before clearing for logging
        events_before = len(
            manager.get_recent_events(3600)
        )  # Get last hour's events for count
        manager.clear_events()
        logger.info(f"Successfully cleared {events_before} IR events from memory")

        output = ClearIrEventsOutput(
            success=True,
            message="IR events cleared successfully.",
        )
        logger.info("IR events clear operation completed successfully")
        return ToolResponse.from_model(output)
