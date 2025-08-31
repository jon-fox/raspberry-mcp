"""Tool for turning on a fan."""

from typing import Dict, Any
from mcp_server.tools.fan_control.fan_model import FanOnRequest, FanOnResponse
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.utils.device_registry import load_device_mapping
from mcp_server.utils.ir_event_controls import ir_send

import asyncio


class FanOn(Tool):
    name = "FanOn"
    description = "Turns on a fan"
    input_model = FanOnRequest
    output_model = FanOnResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    def _create_error_response(self, message: str) -> ToolResponse:
        output = FanOnResponse(success=False, message=message)
        return ToolResponse.from_model(output)

    async def execute(self, input_data: FanOnRequest) -> ToolResponse:
        # 1) resolve device + code
        device_mapping = load_device_mapping(input_data.device_id)
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
        output = FanOnResponse(success=ok, message=msg)
        return ToolResponse.from_model(output)
