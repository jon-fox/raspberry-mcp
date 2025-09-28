"""example-mcp-server MCP Server HTTP Stream Transport."""

from typing import List
import argparse
import logging

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
    GetListenerStatus,
    SendIRCommand,
    ListDeviceOperations,
    GetMappingGuidance,
    TestIRTransmitter,
    TroubleshootIR,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    logger.info("Initializing available tools")
    tools = [
        # Device registration tools
        StartIRListener(),
        StopIRListener(),
        ClearIREvents(),
        SubmitMappings(),
        GetListenerStatus(),
        SendIRCommand(),
        ListDeviceOperations(),
        GetMappingGuidance(),
        TestIRTransmitter(),
        TroubleshootIR(),
    ]
    logger.info(f"Successfully initialized {len(tools)} tools")
    return tools


def get_available_resources() -> List[Resource]:
    """Get list of all available resources."""
    return []


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server."""
    logger.info("Creating MCP server instance")
    mcp = FastMCP("example-mcp-server")
    tool_service = ToolService()
    resource_service = ResourceService()

    # Register all tools and their MCP handlers
    logger.info("Registering tools and MCP handlers")
    tool_service.register_tools(get_available_tools())
    tool_service.register_mcp_handlers(mcp)

    # Register all resources and their MCP handlers
    logger.info("Registering resources and MCP handlers")
    resource_service.register_resources(get_available_resources())
    resource_service.register_mcp_handlers(mcp)

    logger.info("MCP server configuration completed successfully")
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

    logger.info(f"Starting MCP HTTP Stream Server on {args.host}:{args.port}")
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
