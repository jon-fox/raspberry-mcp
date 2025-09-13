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
        logger.debug(f"Getting schema for {self.name} tool")
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
        logger.info(f"=== Starting submit mappings operation ===")
        logger.info(f"Device key: '{input_data.device_key}'")
        logger.info(f"Required operations: {input_data.required_operations}")
        logger.info(f"Optional operations: {input_data.optional_operations}")
        logger.info(f"Time horizon: {input_data.horizon_s}s")
        
        logger.info(f"Submitting mappings for device '{input_data.device_key}' with {len(input_data.required_operations)} required and {len(input_data.optional_operations)} optional operations")
        
        logger.debug("Getting IRListenerManager instance")
        manager = IRListenerManager.get_instance()
        
        # Validate required operations
        logger.debug("Validating required operations")
        if "power_on" not in input_data.required_operations or "power_off" not in input_data.required_operations:
            logger.warning(f"Missing required operations for device '{input_data.device_key}': power_on and power_off are mandatory")
            logger.warning(f"Provided required operations: {input_data.required_operations}")
            output = SubmitMappingsOutput(
                success=False,
                message="Required operations must include both 'power_on' and 'power_off'.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
            logger.info("Returning failure response due to missing required operations")
            return ToolResponse.from_model(output)
        
        logger.debug("Required operations validation passed")
        
        # Get recent IR events within the specified horizon
        logger.debug(f"Retrieving recent IR events within {input_data.horizon_s}s horizon")
        recent_events = manager.get_recent_events(input_data.horizon_s)
        logger.info(f"Found {len(recent_events)} recent IR events within {input_data.horizon_s}s horizon")
        
        if recent_events:
            logger.debug("Recent IR events details:")
            for i, event in enumerate(recent_events):
                logger.debug(f"  Event {i+1}: {event}")
                
                # Log decoded IR codes and analysis if available
                analysis = event.get('analysis', {})
                if analysis:
                    protocol = analysis.get('protocol', 'Unknown')
                    code = analysis.get('code', 'N/A')
                    logger.info(f"  Event {i+1} IR Code: Protocol={protocol}, Code={code}")
                    
                    if protocol != 'Unknown':
                        address = analysis.get('address')
                        command = analysis.get('command')
                        if address is not None and command is not None:
                            logger.info(f"    Address: 0x{address:02X}, Command: 0x{command:02X}")
                        
                        # Log verification status for protocols that support it
                        if analysis.get('verified'):
                            logger.info(f"    ✓ Protocol verification passed")
                        elif 'verified' in analysis and not analysis['verified']:
                            logger.warning(f"    ✗ Protocol verification failed")
                    
                    # Log signal fingerprint for pattern matching
                    pulse_count = event.get('pulse_count', 0)
                    total_duration = event.get('total_duration_us', 0)
                    logger.debug(f"    Signal characteristics: {pulse_count} pulses, {total_duration}μs duration")
                else:
                    logger.warning(f"  Event {i+1}: No IR code analysis available (older format)")
        else:
            logger.warning("No recent IR events found")
        
        # Combine all operations in order (required first, then optional)
        all_operations = input_data.required_operations + input_data.optional_operations
        num_operations = len(all_operations)
        num_events = len(recent_events)
        
        logger.info(f"Operation mapping summary:")
        logger.info(f"  Total operations to map: {num_operations}")
        logger.info(f"  Available IR events: {num_events}")
        logger.info(f"  Combined operations order: {all_operations}")
        
        if num_events < num_operations:
            logger.error(f"Insufficient IR events: expected {num_operations}, found {num_events}")
            logger.error(f"Missing {num_operations - num_events} IR events")
            output = SubmitMappingsOutput(
                success=False,
                message=f"Not enough IR events captured. Expected {num_operations} but found {num_events}. "
                       f"Make sure to press the remote buttons for all operations before submitting mappings.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
            logger.info("Returning failure response due to insufficient IR events")
        elif num_events > num_operations:
            logger.error(f"Too many IR events: expected {num_operations}, found {num_events}")
            logger.error(f"Extra {num_events - num_operations} IR events found")
            output = SubmitMappingsOutput(
                success=False,
                message=f"Too many IR events captured. Expected {num_operations} but found {num_events}. "
                       f"Use ClearIREvents to clear previous events and try again.",
                device_key=input_data.device_key,
                mapped_required=[],
                mapped_optional=[],
            )
            logger.info("Returning failure response due to too many IR events")
        else:
            logger.info("Perfect match: number of events equals number of operations")
            # Get the most recent events that match our operations count
            relevant_events = recent_events[-num_operations:]  # Take the last N events
            logger.debug(f"Selected {len(relevant_events)} most recent events for mapping")
            
            logger.info("=== IR Code to Operation Mapping ===")
            for i, (operation, event) in enumerate(zip(all_operations, relevant_events)):
                analysis = event.get('analysis', {})
                protocol = analysis.get('protocol', 'Unknown')
                code = analysis.get('code', 'N/A')
                signal_num = event.get('signal_number', i+1)
                
                logger.info(f"  {i+1}. Operation '{operation}' mapped to:")
                logger.info(f"      Signal #{signal_num}: {protocol} protocol, Code: {code}")
                
                if protocol != 'Unknown':
                    address = analysis.get('address')
                    command = analysis.get('command')
                    if address is not None and command is not None:
                        logger.info(f"      Address: 0x{address:02X}, Command: 0x{command:02X}")
                    
                    if analysis.get('verified'):
                        logger.info(f"      ✓ Verified {protocol} protocol")
                else:
                    logger.warning(f"      ⚠ Unknown protocol - mapped by timing pattern only")
                
                logger.debug(f"  Full event data: {event}")
            logger.info("=== End IR Code Mapping ===")
            
            logger.info("Saving device mapping to file system")
            success = save_device_mapping(
                device_key=input_data.device_key,
                required_operations=input_data.required_operations,
                optional_operations=input_data.optional_operations,
                ir_events=relevant_events
            )
            
            if success:
                num_required = len(input_data.required_operations)
                num_optional = len(input_data.optional_operations)
                logger.info(f"✓ Successfully saved device mapping for '{input_data.device_key}'")
                logger.info(f"  Required operations mapped: {num_required}")
                logger.info(f"  Optional operations mapped: {num_optional}")
                logger.info(f"  Total mappings created: {num_operations}")
                
                # Log summary of mapped IR codes
                logger.info(f"=== Mapped IR Codes Summary for '{input_data.device_key}' ===")
                protocols_used = set()
                for i, (operation, event) in enumerate(zip(all_operations, relevant_events)):
                    analysis = event.get('analysis', {})
                    protocol = analysis.get('protocol', 'Unknown')
                    code = analysis.get('code', 'N/A')
                    protocols_used.add(protocol)
                    logger.info(f"  {operation}: {protocol} {code}")
                
                logger.info(f"Protocols detected: {', '.join(sorted(protocols_used))}")
                logger.info(f"=== End Mapping Summary ===")
                
                output = SubmitMappingsOutput(
                    success=True,
                    message=f"Successfully mapped {num_operations} operations for device '{input_data.device_key}': "
                           f"{num_required} required, {num_optional} optional. Device configuration saved to Raspberry Pi.",
                    device_key=input_data.device_key,
                    mapped_required=input_data.required_operations,
                    mapped_optional=input_data.optional_operations,
                )
                logger.info("Returning success response")
            else:
                logger.error(f"✗ Failed to save device mapping for '{input_data.device_key}' - file system error")
                logger.error("This could be due to:")
                logger.error("  - Insufficient file system permissions")
                logger.error("  - Disk space issues")
                logger.error("  - Invalid file path")
                logger.error("  - Device registry corruption")
                output = SubmitMappingsOutput(
                    success=False,
                    message=f"Failed to save device mapping for '{input_data.device_key}'. "
                           f"Check Raspberry Pi file system permissions.",
                    device_key=input_data.device_key,
                    mapped_required=[],
                    mapped_optional=[],
                )
                logger.info("Returning failure response due to file system error")
        
        logger.info(f"=== Submit mappings operation completed ===")
        return ToolResponse.from_model(output)
