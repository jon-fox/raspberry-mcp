"""Tool for submitting IR mappings."""

from typing import Dict, Any
from mcp_server.tools.register_devices.register_models import (
    SubmitMappingsInput,
    SubmitMappingsOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager
from mcp_server.utils.device_registry import save_device_mapping


class SubmitMappings(Tool):
    """Tool that submits IR mappings for a single device."""

    name = "SubmitMappings"
    description = "Submits IR button mappings for a single device. Maps recently captured IR signals to device operations in chronological order." \
    "  The events and operations are matched in chronological order: " \
    "  - 1st captured event → 1st operation in the list " \
    "  - 2nd captured event → 2nd operation in the list " \
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
        The events and operations are matched in chronological order:
        - 1st captured event → 1st operation in the list
        - 2nd captured event → 2nd operation in the list
        - etc.

        Args:
            input_data: The validated input containing device_key, operations list, and time horizon

        Returns:
            A response confirming the submitted mappings for the device
        """
        manager = IRListenerManager.get_instance()
        
        # Get recent IR events within the specified horizon
        recent_events = manager.get_recent_events(input_data.horizon_s)
        
        # Validate that we have enough events for the operations
        num_operations = len(input_data.operations)
        num_events = len(recent_events)
        
        if num_events < num_operations:
            output = SubmitMappingsOutput(
                success=False,
                message=f"Not enough IR events captured. Expected {num_operations} but found {num_events}. "
                       f"Make sure to press the remote buttons before submitting mappings.",
                device_key=input_data.device_key,
                mapped_operations=[],
            )
        elif num_events > num_operations:
            output = SubmitMappingsOutput(
                success=False,
                message=f"Too many IR events captured. Expected {num_operations} but found {num_events}. "
                       f"Use ClearIREvents to clear previous events and try again.",
                device_key=input_data.device_key,
                mapped_operations=[],
            )
        else:
            # Get the most recent events that match our operations count
            relevant_events = recent_events[-num_operations:]  # Take the last N events
            
            success = save_device_mapping(
                device_key=input_data.device_key,
                operations=input_data.operations,
                ir_events=relevant_events
            )
            
            if success:
                output = SubmitMappingsOutput(
                    success=True,
                    message=f"Successfully mapped {num_operations} operations for device '{input_data.device_key}'. "
                           f"Device configuration saved to Raspberry Pi.",
                    device_key=input_data.device_key,
                    mapped_operations=input_data.operations,
                )
            else:
                output = SubmitMappingsOutput(
                    success=False,
                    message=f"Failed to save device mapping for '{input_data.device_key}'. "
                           f"Check Raspberry Pi file system permissions.",
                    device_key=input_data.device_key,
                    mapped_operations=[],
                )
        
        return ToolResponse.from_model(output)
