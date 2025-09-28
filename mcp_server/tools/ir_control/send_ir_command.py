"""Generic tool for sending IR commands to any registered device."""

from typing import Dict, Any
import logging

from mcp_server.tools.ir_control.ir_models import SendIRCommandRequest, SendIRCommandResponse
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.utils.device_registry import load_device_mapping, get_device_operation_details
from mcp_server.utils.ir_event_controls import ir_send

logger = logging.getLogger(__name__)


class SendIRCommand(Tool):
    """Generic tool that sends IR commands to any registered device."""

    name = "SendIRCommand"
    description = "Sends an IR command to a registered device using ~78% duty cycle and 5x repeat transmission for strong signal that can actually control devices. Can perform any operation that was mapped during device registration (power_on, power_off, speed_up, etc.)."
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
        logger.info(f"=== Sending IR Command ===")
        logger.info(f"Device: '{input_data.device_id}', Operation: '{input_data.operation}'")
        
        # Load device mapping
        device_mapping = load_device_mapping(input_data.device_id)

        if not device_mapping:
            logger.warning(f"Device '{input_data.device_id}' not found in registry")
            return self._create_error_response(
                f"Device '{input_data.device_id}' not found. Make sure the device is registered using SubmitMappings.",
                device_id=input_data.device_id,
                operation=input_data.operation
            )

        # Check if the operation is available for this device
        if "codes" not in device_mapping or input_data.operation not in device_mapping["codes"]:
            available_ops = list(device_mapping.get("codes", {}).keys())
            logger.warning(f"Operation '{input_data.operation}' not available for device '{input_data.device_id}'. Available: {available_ops}")
            return self._create_error_response(
                f"Operation '{input_data.operation}' not available for device '{input_data.device_id}'. "
                f"Available operations: {available_ops}",
                device_id=input_data.device_id,
                operation=input_data.operation
            )

        # Get detailed IR information for enhanced logging and transmission
        operation_details = get_device_operation_details(input_data.device_id, input_data.operation)
        
        try:
            protocol = device_mapping["protocol"]
            hex_code = device_mapping["codes"][input_data.operation]
            
            # Enhanced logging with analysis data
            logger.info(f"IR Command Details:")
            logger.info(f"  Protocol: {protocol}")
            logger.info(f"  IR Code: {hex_code}")
            
            if operation_details:
                address = operation_details.get("address")
                command = operation_details.get("command")
                verified = operation_details.get("verified", False)
                pulse_count = operation_details.get("pulse_count", 0)
                
                if address is not None and command is not None:
                    logger.info(f"  Address: 0x{address:02X}, Command: 0x{command:02X}")
                
                if verified:
                    logger.info(f"  ✓ Verified {protocol} protocol from capture")
                else:
                    logger.info(f"  ⚠ Unverified protocol - using pattern matching")
                
                logger.info(f"  Signal characteristics: {pulse_count} pulses captured")
                logger.debug(f"  Full operation details: {operation_details}")
            else:
                logger.warning(f"  No detailed analysis available - using basic code only")
            
        except KeyError as e:
            logger.error(f"Configuration error for device '{input_data.device_id}': missing {e}")
            return self._create_error_response(
                f"Configuration error for device '{input_data.device_id}': missing {e}",
                device_id=input_data.device_id,
                operation=input_data.operation
            )

        # Send IR command using GPIO17 directly with optimal settings
        logger.info(f"Transmitting IR signal via GPIO17 at 38kHz with ~78% duty cycle (5x repeats for device control)...")
        
        # Get raw timing data for Generic protocols
        raw_timing_data = None
        if protocol.lower() == 'generic' and operation_details:
            raw_timing_data = operation_details.get("raw_timing_data")
            logger.info(f"Using raw timing data for Generic protocol: {len(raw_timing_data) if raw_timing_data else 0} pulses")
        
        ok, detail = ir_send(protocol, hex_code, raw_timing_data=raw_timing_data)

        # Create response with enhanced messaging
        if ok:
            if operation_details and operation_details.get("verified"):
                message = f"✓ Verified {protocol} command '{input_data.operation}' sent successfully to '{input_data.device_id}' (Code: {hex_code})"
            else:
                message = f"Command '{input_data.operation}' sent to '{input_data.device_id}' using {protocol} protocol (Code: {hex_code})"
            logger.info(f"IR transmission successful: {detail}")
        else:
            message = f"IR transmission failed for '{input_data.operation}' on '{input_data.device_id}': {detail}"
            logger.error(f"IR transmission failed: {message}")

        logger.info(f"=== IR Command Complete ===")
        
        output = SendIRCommandResponse(
            success=ok,
            message=message,
            device_id=input_data.device_id,
            operation=input_data.operation
        )
        return ToolResponse.from_model(output)
