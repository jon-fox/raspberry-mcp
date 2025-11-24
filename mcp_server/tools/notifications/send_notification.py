import logging
from typing import Dict, Any

import requests

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.notifications.notification_models import (
    SendNotificationInput,
    SendNotificationOutput,
)

logger = logging.getLogger(__name__)


class SendNotification(Tool):
    """Tool that sends notifications to ntfy.sh endpoint."""

    name = "SendNotification"
    description = "Sends a notification message to the end user containing the humidity and photo sensor data collected"
    input_model = SendNotificationInput
    output_model = SendNotificationOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SendNotificationInput) -> ToolResponse:
        """Execute the send notification tool."""
        logger.info("Sending notification to ntfy.sh")

        try:
            response = requests.post(
                "https://ntfy.sh/pi-agent", data=input_data.message.encode()
            )
            response.raise_for_status()

            logger.info(f"Notification sent (status {response.status_code})")
            output = SendNotificationOutput(
                success=True, message="Notification sent successfully."
            )

        except ImportError as e:
            logger.error(f"Requests library not available: {e}")
            output = SendNotificationOutput(
                success=False,
                message=f"Requests library not installed: {str(e)}. Install 'requests' package.",
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
            output = SendNotificationOutput(
                success=False, message=f"Failed to send notification: {str(e)}"
            )

        return ToolResponse.from_model(output)
