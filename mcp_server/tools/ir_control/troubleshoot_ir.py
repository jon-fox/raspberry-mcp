"""Tool for troubleshooting IR device control issues."""

import asyncio
from typing import Dict, Any
import logging

from mcp_server.interfaces.tool import Tool, ToolResponse, BaseToolInput
from mcp_server.utils.device_registry import load_device_mapping, get_device_operation_details
from mcp_server.utils.ir_event_controls import ir_send
from pydantic import Field, ConfigDict

logger = logging.getLogger(__name__)


class TroubleshootIRRequest(BaseToolInput):
    """Request model for IR troubleshooting."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"device_id": "living_room_tv", "operation": "power_on"},
            ]
        }
    )

    device_id: str = Field(
        description="The ID of the device to troubleshoot",
        examples=["living_room_tv"],
    )
    
    operation: str = Field(
        description="The operation to test with different power/frequency settings",
        examples=["power_on", "power_off"],
    )


class TroubleshootIRResponse(BaseToolInput):
    """Response model for IR troubleshooting."""
    
    success: bool = Field(description="Whether troubleshooting completed")
    message: str = Field(description="Troubleshooting results and recommendations")
    tests_performed: int = Field(description="Number of test transmissions sent")


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
        logger.info(f"=== Troubleshooting IR Device ===")
        logger.info(f"Device: '{input_data.device_id}', Operation: '{input_data.operation}'")
        
        # Load device mapping
        device_mapping = load_device_mapping(input_data.device_id)
        if not device_mapping:
            output = TroubleshootIRResponse(
                success=False,
                message=f"Device '{input_data.device_id}' not found in registry",
                tests_performed=0
            )
            return ToolResponse.from_model(output)

        # Check if operation exists
        if input_data.operation not in device_mapping.get("codes", {}):
            available_ops = list(device_mapping.get("codes", {}).keys())
            output = TroubleshootIRResponse(
                success=False,
                message=f"Operation '{input_data.operation}' not available. Available: {available_ops}",
                tests_performed=0
            )
            return ToolResponse.from_model(output)

        protocol = device_mapping["protocol"]
        hex_code = device_mapping["codes"][input_data.operation]
        operation_details = get_device_operation_details(input_data.device_id, input_data.operation)
        raw_timing_data = None
        
        if protocol.lower() == 'generic' and operation_details:
            raw_timing_data = operation_details.get("raw_timing_data")

        logger.info(f"Testing {protocol} protocol, code: {hex_code}")
        
        # Test configurations: (power_boost, carrier_freq, description)
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
                carrier_freq=carrier_freq
            )
            
            if success:
                results.append(f"✓ {description}: {message}")
                logger.info(f"Test {tests_performed} successful: {message}")
            else:
                results.append(f"✗ {description}: {message}")
                logger.error(f"Test {tests_performed} failed: {message}")
            
            # Wait between tests to avoid interference
            await asyncio.sleep(2)
        
        # Generate recommendations
        recommendations = []
        recommendations.append("TROUBLESHOOTING COMPLETE - Try these solutions:")
        recommendations.append("")
        recommendations.append("1. HARDWARE CHECK:")
        recommendations.append("   - Verify IR LED is connected to GPIO17 with proper current-limiting resistor")
        recommendations.append("   - Check LED polarity (longer leg = positive/anode)")
        recommendations.append("   - Ensure LED is pointing at device (5-10 foot range)")
        recommendations.append("   - Test with visible LED first to verify circuit")
        recommendations.append("")
        recommendations.append("2. DEVICE-SPECIFIC:")
        recommendations.append("   - Some devices need to be in specific mode to receive commands")
        recommendations.append("   - Try different operations (volume, channel) that might be more responsive")
        recommendations.append("   - Check if device has IR learning mode that needs different timing")
        recommendations.append("")
        recommendations.append("3. IF TESTS SHOWED TRANSMISSION BUT NO DEVICE RESPONSE:")
        recommendations.append("   - Try the high-power configurations (100% duty cycle)")
        recommendations.append("   - Test different carrier frequencies (36kHz, 40kHz)")
        recommendations.append("   - Move IR LED closer to device")
        recommendations.append("   - Check device manual for specific IR requirements")
        
        final_message = "\n".join(results + [""] + recommendations)
        
        output = TroubleshootIRResponse(
            success=True,
            message=final_message,
            tests_performed=tests_performed
        )
        
        logger.info(f"Troubleshooting completed: {tests_performed} tests performed")
        return ToolResponse.from_model(output)