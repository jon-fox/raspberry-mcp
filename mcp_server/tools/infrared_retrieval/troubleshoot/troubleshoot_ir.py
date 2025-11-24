import asyncio
import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.infrared_retrieval.troubleshoot.troubleshoot_models import (
    TroubleshootIRRequest,
    TroubleshootIRResponse,
)
from mcp_server.utils.device_registry import (
    load_device_mapping,
    get_device_operation_details,
)
from mcp_server.utils.ir_event_controls import ir_send

logger = logging.getLogger(__name__)


class TroubleshootIR(Tool):
    """Tool that tests different IR transmission settings to help diagnose device control issues."""

    name = "TroubleshootIR"
    description = "Tests different power levels and carrier frequencies to help diagnose why IR devices aren't responding"
    input_model = TroubleshootIRRequest
    output_model = TroubleshootIRResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: TroubleshootIRRequest) -> ToolResponse:
        """Execute IR troubleshooting with different settings."""
        logger.info("=== Troubleshooting IR Device ===")
        logger.info(
            f"Device: '{input_data.device_id}', Operation: '{input_data.operation}'"
        )

        device_mapping = load_device_mapping(input_data.device_id)
        if not device_mapping:
            output = TroubleshootIRResponse(
                success=False,
                message=f"Device '{input_data.device_id}' not found in registry",
                tests_performed=0,
            )
            return ToolResponse.from_model(output)

        if input_data.operation not in device_mapping.get("codes", {}):
            available_ops = list(device_mapping.get("codes", {}).keys())
            output = TroubleshootIRResponse(
                success=False,
                message=f"Operation '{input_data.operation}' not available. Available: {available_ops}",
                tests_performed=0,
            )
            return ToolResponse.from_model(output)

        protocol = device_mapping["protocol"]
        hex_code = device_mapping["codes"][input_data.operation]
        operation_details = get_device_operation_details(
            input_data.device_id, input_data.operation
        )
        raw_timing_data = None

        if protocol.lower() == "generic" and operation_details:
            raw_timing_data = operation_details.get("raw_timing_data")

        logger.info(f"Testing {protocol} protocol, code: {hex_code}")

        test_configs = [
            (False, 38000, "Standard: ~78% duty cycle, 38kHz"),
            (True, 38000, "High Power: 100% duty cycle, 38kHz"),
            (False, 36000, "Standard: ~78% duty cycle, 36kHz"),
            (True, 36000, "High Power: 100% duty cycle, 36kHz"),
            (False, 40000, "Standard: ~78% duty cycle, 40kHz"),
            (True, 40000, "High Power: 100% duty cycle, 40kHz"),
        ]

        results = []
        tests_performed = 0

        for power_boost, carrier_freq, description in test_configs:
            tests_performed += 1
            logger.info(f"Test {tests_performed}: {description}")

            success, message = await ir_send(
                protocol,
                hex_code,
                raw_timing_data=raw_timing_data,
                power_boost=power_boost,
                carrier_freq=carrier_freq,
            )

            if success:
                results.append(f"SUCCESS {description}: {message}")
                logger.info(f"Test {tests_performed} successful: {message}")
            else:
                results.append(f"FAILED {description}: {message}")
                logger.error(f"Test {tests_performed} failed: {message}")

            await asyncio.sleep(2)

        recommendations = [
            "",
            "TROUBLESHOOTING:",
            "- Verify IR LED connected to GPIO17 with current-limiting resistor",
            "- Check LED polarity and pointing at device (5-10 ft range)",
            "- Try high-power configs (100% duty cycle) or different frequencies (36kHz, 40kHz)",
            "- Ensure device is in correct mode to receive IR commands",
        ]

        final_message = "\n".join(results + recommendations)

        output = TroubleshootIRResponse(
            success=True, message=final_message, tests_performed=tests_performed
        )

        logger.info(f"Troubleshooting completed: {tests_performed} tests performed")
        return ToolResponse.from_model(output)
