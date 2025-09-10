"""Generic tool for sending IR commands to any registered device."""

from typing import Dict, Any
from mcp_server.tools.ir_control.ir_models import SendIRCommandRequest, SendIRCommandResponse
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.utils.device_registry import load_device_mapping
from mcp_server.utils.ir_event_controls import ir_send


class SendIRCommand(Tool):
    """Generic tool that sends IR commands to any registered device."""

    name = "SendIRCommand"
    description = "Sends an IR command to a registered device. Can perform any operation that was mapped during device registration (power_on, power_off, speed_up, etc.)"
    input_model = SendIRCommandRequest
    output_model = SendIRCommandResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    def _create_error_response(self, message: str, device_id: str = None, operation: str = None) -> ToolResponse:
        output = SendIRCommandResponse(
            success=False, 
            message=message,
            device_id=device_id,
            operation=operation
        )
        return ToolResponse.from_model(output)

    async def execute(self, input_data: SendIRCommandRequest) -> ToolResponse:
        """Execute the IR command sending.

        Args:
            input_data: The validated input containing device_id and operation

        Returns:
            A response indicating success or failure of the IR command
        """
        # Load device mapping
        device_mapping = load_device_mapping(input_data.device_id)

        if not device_mapping:
            return self._create_error_response(
                f"Device '{input_data.device_id}' not found. Make sure the device is registered using SubmitMappings.",
                device_id=input_data.device_id,
                operation=input_data.operation
            )

        # Check if the operation is available for this device
        if "codes" not in device_mapping or input_data.operation not in device_mapping["codes"]:
            available_ops = list(device_mapping.get("codes", {}).keys())
            return self._create_error_response(
                f"Operation '{input_data.operation}' not available for device '{input_data.device_id}'. "
                f"Available operations: {available_ops}",
                device_id=input_data.device_id,
                operation=input_data.operation
            )

        try:
            protocol = device_mapping["protocol"]
            hex_code = device_mapping["codes"][input_data.operation]
            # tx_device is no longer needed since we use GPIO17 directly
        except KeyError as e:
            return self._create_error_response(
                f"Configuration error for device '{input_data.device_id}': missing {e}",
                device_id=input_data.device_id,
                operation=input_data.operation
            )

        # Send IR command using GPIO17 directly
        ok, detail = await ir_send(protocol, hex_code)

        # Create response
        if ok:
            message = f"Command '{input_data.operation}' sent successfully to '{input_data.device_id}'"
        else:
            message = f"IR send failed for '{input_data.operation}' on '{input_data.device_id}': {detail}"

        output = SendIRCommandResponse(
            success=ok,
            message=message,
            device_id=input_data.device_id,
            operation=input_data.operation
        )
        return ToolResponse.from_model(output)
