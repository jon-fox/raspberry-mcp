"""Tool for submitting IR mappings."""

from typing import Dict, Any
import logging

from mcp_server.tools.register_devices.register_models import (
    SubmitMappingsInput,
    SubmitMappingsOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager
from mcp_server.utils.device_registry import save_device_mapping

logger = logging.getLogger(__name__)


class SubmitMappings(Tool):
    """Tool that submits IR mappings for a single device."""

    name = "SubmitMappings"
    description = "Submits IR button mappings for a single device. Maps recently captured IR signals to device operations in chronological order. " \
    "Required operations (power_on, power_off) must always be provided. Optional operations can be added as needed. " \
    "The events and operations are matched in chronological order: " \
    "  - 1st captured event → 1st required operation " \
    "  - 2nd captured event → 2nd required operation " \
    "  - 3rd captured event → 1st optional operation " \
    "  - etc."
    input_model = SubmitMappingsInput
    output_model = SubmitMappingsOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SubmitMappingsInput) -> ToolResponse:
        """Execute the submit mappings tool.
        
        Maps the recently captured IR events to operations for a single device.
        Required operations must be provided first, followed by optional operations.
        The events and operations are matched in chronological order.

        Args:
            input_data: The validated input containing device_key, required/optional operations, and time horizon

        Returns:
            A response confirming the submitted mappings for the device
        """
        logger.info(f"Submitting mappings for device '{input_data.device_key}' with {len(input_data.required_operations)} required and {len(input_data.optional_operations)} optional operations")
        
        manager = IRListenerManager.get_instance()
        
        # Validate required operations
        if "power_on" not in input_data.required_operations or "power_off" not in input_data.required_operations:
            logger.warning(f"Missing required operations for device '{input_data.device_key}': power_on and power_off are mandatory")
            output = SubmitMappingsOutput(
                success=False,
                message="Required operations must include both 'power_on' and 'power_off'.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
            return ToolResponse.from_model(output)
        
        # Get recent IR events within the specified horizon
        recent_events = manager.get_recent_events(input_data.horizon_s)
        logger.info(f"Found {len(recent_events)} recent IR events within {input_data.horizon_s}s horizon")
        
        # Combine all operations in order (required first, then optional)
        all_operations = input_data.required_operations + input_data.optional_operations
        num_operations = len(all_operations)
        num_events = len(recent_events)
        
        if num_events < num_operations:
            logger.warning(f"Insufficient IR events: expected {num_operations}, found {num_events}")
            output = SubmitMappingsOutput(
                success=False,
                message=f"Not enough IR events captured. Expected {num_operations} but found {num_events}. "
                       f"Make sure to press the remote buttons for all operations before submitting mappings.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
        elif num_events > num_operations:
            logger.warning(f"Too many IR events: expected {num_operations}, found {num_events}")
            output = SubmitMappingsOutput(
                success=False,
                message=f"Too many IR events captured. Expected {num_operations} but found {num_events}. "
                       f"Use ClearIREvents to clear previous events and try again.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
        else:
            # Get the most recent events that match our operations count
            relevant_events = recent_events[-num_operations:]  # Take the last N events
            
            success = save_device_mapping(
                device_key=input_data.device_key,
                required_operations=input_data.required_operations,
                optional_operations=input_data.optional_operations,
                ir_events=relevant_events
            )
            
            if success:
                num_required = len(input_data.required_operations)
                num_optional = len(input_data.optional_operations)
                logger.info(f"Successfully saved device mapping for '{input_data.device_key}': {num_required} required, {num_optional} optional operations")
                output = SubmitMappingsOutput(
                    success=True,
                    message=f"Successfully mapped {num_operations} operations for device '{input_data.device_key}': "
                           f"{num_required} required, {num_optional} optional. Device configuration saved to Raspberry Pi.",
                    device_key=input_data.device_key,
                    mapped_required=input_data.required_operations,
                    mapped_optional=input_data.optional_operations,
                )
            else:
                logger.error(f"Failed to save device mapping for '{input_data.device_key}' - file system error")
                output = SubmitMappingsOutput(
                    success=False,
                    message=f"Failed to save device mapping for '{input_data.device_key}'. "
                           f"Check Raspberry Pi file system permissions.",
                    device_key=input_data.device_key,
                    mapped_required=[],
                    mapped_optional=[],
                )
        
        return ToolResponse.from_model(output)
