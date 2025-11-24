import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager
from mcp_server.tools.infrared_retrieval.clear_events.events_models import (
    ClearIrEventsInput,
    ClearIrEventsOutput,
)

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
        """Execute the clear IR events tool."""
        manager = IRListenerManager.get_instance()
        events_before = len(manager.get_recent_events(3600))
        manager.clear_events()
        logger.info(f"Cleared {events_before} IR events")

        output = ClearIrEventsOutput(
            success=True,
            message="IR events cleared successfully.",
        )
        return ToolResponse.from_model(output)
