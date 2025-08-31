"""Tool for turning off a fan."""

from typing import Dict, Any
from mcp_server.tools.fan_control.fan_model import FanOffRequest, FanOffResponse
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.utils.ir_event_controls import ir_send
from mcp_server.utils.device_registry import load_device_mapping


class FanOff(Tool):
    """Tool that turns off a fan."""

    name = "FanOff"
    description = "Turns off a fan"
    input_model = FanOffRequest
    output_model = FanOffResponse

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    def _create_error_response(self, message: str) -> ToolResponse:
        output = FanOffResponse(success=False, message=message)
        return ToolResponse.from_model(output)


    async def execute(self, input_data: FanOffRequest) -> ToolResponse:
        """Execute the fan off tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the FanOffResponse
        """

        device_mapping = load_device_mapping(input_data.device_id)

        if not device_mapping:
            return self._create_error_response("Device not found")

        try:
            protocol = device_mapping["protocol"]
            tx_device = device_mapping["tx_device"]
            hex_code = device_mapping["codes"]["power_on"]
        except Exception as e:
            return self._create_error_response(f"Config error: {e}")

        # 2) send IR
        ok, detail = await ir_send(protocol, hex_code, tx_device)

        # 3) respond
        msg = "Fan turned on successfully" if ok else f"IR send failed: {detail}"

        output = FanOffResponse(success=True, message="Fan turned off successfully")
        return ToolResponse.from_model(output)
