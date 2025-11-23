"""Service layer for managing tools."""

from typing import Dict, List, Any
from fastmcp import FastMCP
from mcp_server.interfaces.tool import Tool, ToolResponse, ToolContent


class ToolService:
    """Service for managing and executing tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def register_tools(self, tools: List[Tool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, tool_name: str) -> Tool:
        """Get a tool by name."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")
        return self._tools[tool_name]

    async def execute_tool(
        self, tool_name: str, input_data: Dict[str, Any]
    ) -> ToolResponse:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(tool_name)
        input_model = tool.input_model.model_validate(input_data)
        return await tool.execute(input_model)

    def _process_tool_content(self, content: ToolContent) -> Any:
        """Process a ToolContent object based on its type."""
        if content.type == "text":
            return content.text
        elif content.type == "json" and content.json_data is not None:
            return content.json_data
        else:
            return content.text or content.json_data or {}

    def _serialize_response(self, response: ToolResponse) -> Any:
        """Serialize a ToolResponse to return to the client."""
        if not response.content:
            return {}

        if len(response.content) == 1:
            return self._process_tool_content(response.content[0])

        return [self._process_tool_content(content) for content in response.content]

    def register_mcp_handlers(self, mcp: FastMCP) -> None:
        """Register all tools as MCP handlers."""
        for tool in self._tools.values():
            def create_handler(tool_instance):
                async def handler(input_data: tool_instance.input_model):
                    f'"""{tool_instance.description}"""'
                    result = await self.execute_tool(
                        tool_instance.name, input_data.model_dump()
                    )
                    return self._serialize_response(result)

                return handler

            handler = create_handler(tool)
            mcp.tool(name=tool.name, description=tool.description)(handler)
