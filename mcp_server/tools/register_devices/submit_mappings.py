import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.services.ir_listener_manager import IRListenerManager
from mcp_server.tools.register_devices.register_models import (
    SubmitMappingsInput,
    SubmitMappingsOutput,
)
from mcp_server.utils.device_registry import save_device_mapping

logger = logging.getLogger(__name__)


class SubmitMappings(Tool):
    """Tool that submits IR mappings for a single device."""

    name = "SubmitMappings"
    description = (
        "Submits IR button mappings for a single device. Maps recently captured IR signals to device operations in chronological order. "
        "Required operations (power_on, power_off) must always be provided. Optional operations can be added as needed. "
        "The events and operations are matched in chronological order: "
        "  - 1st captured event → 1st required operation "
        "  - 2nd captured event → 2nd required operation "
        "  - 3rd captured event → 1st optional operation "
        "  - etc."
    )
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
        """Execute the submit mappings tool."""
        logger.info(
            f"Submitting mappings for '{input_data.device_key}': {len(input_data.required_operations)} required, {len(input_data.optional_operations)} optional operations"
        )

        manager = IRListenerManager.get_instance()

        if (
            "power_on" not in input_data.required_operations
            or "power_off" not in input_data.required_operations
        ):
            logger.warning(
                f"Missing required operations: {input_data.required_operations}"
            )
            output = SubmitMappingsOutput(
                success=False,
                message="Required operations must include both 'power_on' and 'power_off'.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
            return ToolResponse.from_model(output)

        recent_events = manager.get_recent_events(input_data.horizon_s)
        all_operations = input_data.required_operations + input_data.optional_operations
        num_operations = len(all_operations)
        num_events = len(recent_events)

        logger.info(f"Found {num_events} IR events, need {num_operations} operations")

        if num_events < num_operations:
            logger.error(f"Insufficient events: {num_events} < {num_operations}")
            output = SubmitMappingsOutput(
                success=False,
                message=f"Not enough IR events captured. Expected {num_operations} but found {num_events}. "
                f"Make sure to press the remote buttons for all operations before submitting mappings.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
        elif num_events > num_operations:
            logger.error(f"Too many events: {num_events} > {num_operations}")
            output = SubmitMappingsOutput(
                success=False,
                message=f"Too many IR events captured. Expected {num_operations} but found {num_events}. "
                f"Use ClearIREvents to clear previous events and try again.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
        else:
            relevant_events = recent_events[-num_operations:]

            logger.info("Mapping operations to IR codes:")
            for i, (operation, event) in enumerate(
                zip(all_operations, relevant_events)
            ):
                analysis = event.get("analysis", {})
                protocol = analysis.get("protocol", "Unknown")
                code = analysis.get("code", "N/A")
                logger.info(f"  {operation}: {protocol} {code}")

            success = save_device_mapping(
                device_key=input_data.device_key,
                required_operations=input_data.required_operations,
                optional_operations=input_data.optional_operations,
                ir_events=relevant_events,
            )

            if success:
                num_required = len(input_data.required_operations)
                num_optional = len(input_data.optional_operations)
                logger.info(
                    f"Saved mapping for '{input_data.device_key}': {num_operations} operations"
                )

                output = SubmitMappingsOutput(
                    success=True,
                    message=f"Successfully mapped {num_operations} operations for device '{input_data.device_key}': "
                    f"{num_required} required, {num_optional} optional. Device configuration saved to Raspberry Pi.",
                    device_key=input_data.device_key,
                    mapped_required=input_data.required_operations,
                    mapped_optional=input_data.optional_operations,
                )
            else:
                logger.error(f"Failed to save mapping for '{input_data.device_key}'")
                output = SubmitMappingsOutput(
                    success=False,
                    message=f"Failed to save device mapping for '{input_data.device_key}'. "
                    f"Check Raspberry Pi file system permissions.",
                    device_key=input_data.device_key,
                    mapped_required=[],
                    mapped_optional=[],
                )

        return ToolResponse.from_model(output)
