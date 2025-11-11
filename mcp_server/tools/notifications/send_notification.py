"""Tool for sending notifications to ntfy.sh."""

from typing import Dict, Any
import logging

from mcp_server.tools.notifications.notification_models import (
    SendNotificationInput,
    SendNotificationOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
import requests

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
        """Execute the send notification tool.

        Args:
            input_data: The validated input containing the message to send

        Returns:
            A response indicating success or failure
        """
        logger.info(f"=== Sending notification to ntfy.sh ===")
        logger.debug(f"Message: {input_data.message}")

        try:

            logger.info("Posting notification to https://ntfy.sh/pi-agent")
            response = requests.post(
                "https://ntfy.sh/pi-agent", data=input_data.message.encode()
            )
            response.raise_for_status()

            logger.info(
                f"✓ Notification sent successfully (status code: {response.status_code})"
            )
            output = SendNotificationOutput(
                success=True, message="Notification sent successfully."
            )

        except ImportError as e:
            logger.error(f"✗ Required library not available: {e}")
            output = SendNotificationOutput(
                success=False,
                message=f"Requests library not installed: {str(e)}. Install 'requests' package.",
            )
        except Exception as e:
            logger.error(f"✗ Failed to send notification: {e}", exc_info=True)
            output = SendNotificationOutput(
                success=False, message=f"Failed to send notification: {str(e)}"
            )

        logger.info(f"=== Notification send complete. Success: {output.success} ===")
        return ToolResponse.from_model(output)
