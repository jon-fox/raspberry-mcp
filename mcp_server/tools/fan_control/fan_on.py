"""Tool for turning on a fan."""

from typing import Dict, Any
from mcp_server.tools.fan_control.fan_model import FanOnRequest, FanOnResponse
from mcp_server.interfaces.tool import Tool, ToolResponse

import asyncio, tomllib
from pathlib import Path

_CODES = None


# storing codes locally for accessing
def _load_codes():
    global _CODES
    if _CODES is None:
        with open(Path(__file__).parent / "codes.toml", "rb") as f:
            _CODES = tomllib.load(f)
    return _CODES


async def _ir_send(protocol: str, hex_code: str, device_path: str) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        "ir-ctl",
        "--device",
        device_path,
        "-S",
        f"{protocol}:{hex_code}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    ok = proc.returncode == 0
    return ok, (
        out.decode().strip() if ok else err.decode().strip() or out.decode().strip()
    )


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
        cfg = _load_codes()
        try:
            dev = cfg["devices"][input_data.device_id]
            protocol = dev["protocol"]
            tx_device = dev["tx_device"]
            hex_code = dev["codes"]["power_on"]
        except Exception as e:
            return self._create_error_response(f"Config error: {e}")

        # 2) send IR
        ok, detail = await _ir_send(protocol, hex_code, tx_device)

        # 3) respond
        msg = "Fan turned on successfully" if ok else f"IR send failed: {detail}"
        output = FanOnResponse(success=ok, message=msg)
        return ToolResponse.from_model(output)
