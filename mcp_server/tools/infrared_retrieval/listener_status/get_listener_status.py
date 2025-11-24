import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager
from mcp_server.tools.infrared_retrieval.listener_status.status_models import (
    GetListenerStatusInput,
    GetListenerStatusOutput,
)

logger = logging.getLogger(__name__)


class GetListenerStatus(Tool):
    """Tool that provides detailed status information about the IR listener."""

    name = "GetListenerStatus"
    description = "Gets detailed status and diagnostic information about the IR listener including activity, event counts, and recent signal detection"
    input_model = GetListenerStatusInput
    output_model = GetListenerStatusOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: GetListenerStatusInput) -> ToolResponse:
        """Execute the get listener status tool."""
        manager = IRListenerManager.get_instance()
        status = manager.get_listener_status()

        recent_events_1min = manager.get_recent_events(60)
        recent_events_5min = manager.get_recent_events(300)

        if status["is_listening"]:
            if status["total_events"] > 0:
                status_msg = f"IR listener is ACTIVE and working! Captured {status['total_events']} signals total. Recent activity: {len(recent_events_1min)} signals in last minute, {len(recent_events_5min)} in last 5 minutes."
            else:
                status_msg = f"IR listener is running but no signals detected yet. Make sure IR transmitter is working and pointed at GPIO pin {status['gpio_pin']}."
        else:
            status_msg = "IR listener is not currently running. Use StartIRListener to begin capturing signals."

        if "latest_event_time" in status:
            status_msg += f" Latest signal captured at {status['latest_event_time']}."

        output = GetListenerStatusOutput(
            success=True,
            is_listening=status["is_listening"],
            gpio_pin=status["gpio_pin"],
            total_events=status["total_events"],
            recent_events_1min=len(recent_events_1min),
            recent_events_5min=len(recent_events_5min),
            listener_task_active=status["listener_task_active"],
            latest_event_time=status.get("latest_event_time"),
            message=status_msg,
        )

        return ToolResponse.from_model(output)
