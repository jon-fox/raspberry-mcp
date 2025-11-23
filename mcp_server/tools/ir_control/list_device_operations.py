"""Tool for listing available operations for a registered device."""

import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.ir_control.ir_models import (
    ListDeviceOperationsRequest,
    ListDeviceOperationsResponse,
)
from mcp_server.utils.device_registry import load_device_mapping

logger = logging.getLogger(__name__)


class ListDeviceOperations(Tool):
    """Tool that lists all available operations for a registered device."""

    name = "ListDeviceOperations"
    description = (
        "Lists all available operations (required and optional) for a registered device"
    )
    input_model = ListDeviceOperationsRequest
    output_model = ListDeviceOperationsResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ListDeviceOperationsRequest) -> ToolResponse:
        """Execute the list operations tool."""
        logger.info(f"Listing operations for device '{input_data.device_id}'")

        device_mapping = load_device_mapping(input_data.device_id)

        if not device_mapping:
            logger.warning(f"Device '{input_data.device_id}' not found in registry")
            output = ListDeviceOperationsResponse(
                success=False,
                device_id=input_data.device_id,
                required_operations=[],
                optional_operations=[],
                message=f"Device '{input_data.device_id}' not found. Make sure the device is registered using SubmitMappings.",
            )
            return ToolResponse.from_model(output)

        required_operations = device_mapping.get("required_operations", [])
        optional_operations = device_mapping.get("optional_operations", [])

        if not required_operations and not optional_operations:
            all_codes = list(device_mapping.get("codes", {}).keys())
            required_operations = [
                op for op in all_codes if op in ["power_on", "power_off"]
            ]
            optional_operations = [
                op for op in all_codes if op not in required_operations
            ]

        num_required = len(required_operations)
        num_optional = len(optional_operations)
        total_ops = num_required + num_optional

        logger.info(
            f"Device '{input_data.device_id}' has {num_required} required and {num_optional} optional operations"
        )

        message = f"Device '{input_data.device_id}' has {num_required} required and {num_optional} optional operations"
        if total_ops == 0:
            message = f"Device '{input_data.device_id}' has no registered operations"
            logger.warning(
                f"Device '{input_data.device_id}' has no registered operations"
            )

        output = ListDeviceOperationsResponse(
            success=True,
            device_id=input_data.device_id,
            required_operations=required_operations,
            optional_operations=optional_operations,
            message=message,
        )
        return ToolResponse.from_model(output)
