import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.smart_plug.plug_models import (
    ControlPlugRequest,
    ControlPlugResponse,
)
from mcp_server.utils.smart_plug import (
    PLUG_IP,
    turn_on,
    turn_off,
    toggle_plug,
    get_ac_state,
)

logger = logging.getLogger(__name__)


class ControlPlug(Tool):
    """Control a Shelly smart plug."""

    name = "ControlPlug"
    description = "Control a Shelly smart plug: turn on, turn off, toggle, or get status. Auto-discovers plug on local network if no IP provided."
    input_model = ControlPlugRequest
    output_model = ControlPlugResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ControlPlugRequest) -> ToolResponse:
        ip = input_data.ip or PLUG_IP
        action = input_data.action.lower()

        logger.info(f"Controlling plug at {ip}: {action}")

        try:
            if action == "on":
                success = turn_on(ip)
                message = "Turned on successfully" if success else "Failed to turn on"
                is_on = success

            elif action == "off":
                success = turn_off(ip)
                message = "Turned off successfully" if success else "Failed to turn off"
                is_on = not success

            elif action == "toggle":
                success = toggle_plug(ip)
                message = "Toggled successfully" if success else "Failed to toggle"
                _, is_on = get_ac_state(ip) if success else (False, None)

            elif action == "status":
                success, is_on = get_ac_state(ip)
                if success:
                    state = "on" if is_on else "off"
                    message = f"Plug is {state}"
                else:
                    message = "Failed to get status"

            else:
                success = False
                is_on = None
                message = f"Invalid action '{action}'. Use 'on', 'off', 'toggle', or 'status'"

            output = ControlPlugResponse(
                success=success,
                message=message,
                is_on=is_on,
                ip=ip,
            )
            return ToolResponse.from_model(output)

        except Exception as e:
            logger.error(f"Error controlling plug: {e}")
            output = ControlPlugResponse(
                success=False,
                message=f"Error: {str(e)}",
                is_on=None,
                ip=ip,
            )
            return ToolResponse.from_model(output)
