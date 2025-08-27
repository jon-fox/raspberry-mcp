"""Tool for setting the speed of a fan."""

from typing import Dict, Any
from mcp_server.tools.discover_devices.discovery_model import (
    DiscoverInput,
    DiscoverOutput,
    Candidate,
)
from mcp_server.interfaces.tool import Tool, ToolResponse


class DiscoverDevices(Tool):
    """Tool that discovers devices."""

    name = "DiscoverDevices"
    description = "Discovers devices based on a query"
    input_model = DiscoverInput
    output_model = DiscoverOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: DiscoverInput) -> ToolResponse:
        """Execute the discover devices tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the discovered devices
        """
        output = DiscoverOutput(
            candidates=[
                Candidate(id="lg_55uk6300_nec1", brand="LG", model="55UK6300"),
                Candidate(id="samsung_qn90a_nec", brand="Samsung", model="QN90A"),
            ],
            message="Devices discovered successfully",
        )
        return ToolResponse.from_model(output)
