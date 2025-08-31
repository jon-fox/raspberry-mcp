"""example-mcp-server MCP Server HTTP Stream Transport."""

from typing import List
import argparse

import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastmcp import FastMCP

from mcp_server.services.tool_service import ToolService
from mcp_server.services.resource_service import ResourceService
from mcp_server.interfaces.tool import Tool
from mcp_server.interfaces.resource import Resource
from mcp_server.tools import (
    # Device registration tools
    StartIRListener,
    StopIRListener,
    ClearIREvents,
    SubmitMappings,
)


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    return [
        # Device registration tools
        StartIRListener(),
        StopIRListener(),
        ClearIREvents(),
        SubmitMappings(),
    ]


def get_available_resources() -> List[Resource]:
    """Get list of all available resources."""
    return []


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP("example-mcp-server")
    tool_service = ToolService()
    resource_service = ResourceService()

    # Register all tools and their MCP handlers
    tool_service.register_tools(get_available_tools())
    tool_service.register_mcp_handlers(mcp)

    # Register all resources and their MCP handlers
    resource_service.register_resources(get_available_resources())
    resource_service.register_mcp_handlers(mcp)

    return mcp


def create_http_app():
    """Create a FastMCP HTTP app with CORS middleware."""
    mcp_server = create_mcp_server()

    app = mcp_server.http_app()  # type: ignore[attr-defined]

    # Apply CORS middleware manually
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    return app


def main():
    """Entry point for the HTTP Stream Transport server."""
    parser = argparse.ArgumentParser(description="Run MCP HTTP Stream server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    args = parser.parse_args()

    app = create_http_app()
    print(f"MCP HTTP Stream Server starting on {args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
