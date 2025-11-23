"""Service layer for managing resources."""

from typing import Dict, List
import re
from fastmcp import FastMCP
from mcp_server.interfaces.resource import Resource, ResourceResponse


class ResourceService:
    """Service for managing and executing resources."""

    def __init__(self):
        self._resources: Dict[str, Resource] = {}
        self._uri_patterns: Dict[str, Resource] = {}

    def register_resource(self, resource: Resource) -> None:
        """Register a new resource."""
        self._uri_patterns[resource.uri] = resource

        if "{" not in resource.uri:
            self._resources[resource.uri] = resource

    def register_resources(self, resources: List[Resource]) -> None:
        """Register multiple resources."""
        for resource in resources:
            self.register_resource(resource)

    def get_resource_by_pattern(self, uri_pattern: str) -> Resource:
        """Get a resource by its URI pattern."""
        if uri_pattern not in self._uri_patterns:
            raise ValueError(f"Resource not found for pattern: {uri_pattern}")
        return self._uri_patterns[uri_pattern]

    def get_resource(self, uri: str) -> Resource:
        """Get a resource by exact URI."""
        if uri in self._resources:
            return self._resources[uri]

        for pattern, resource in self._uri_patterns.items():
            regex_pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
            regex_pattern = f"^{regex_pattern}$"

            match = re.match(regex_pattern, uri)
            if match:
                self._resources[uri] = resource
                return resource

        raise ValueError(f"Resource not found: {uri}")

    def extract_params_from_uri(self, pattern: str, uri: str) -> Dict[str, str]:
        """Extract parameters from a URI based on a pattern."""
        regex_pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
        regex_pattern = f"^{regex_pattern}$"

        match = re.match(regex_pattern, uri)
        if match:
            return match.groupdict()
        return {}

    def create_handler(self, resource: Resource, uri_pattern: str):
        """Create a handler function for a resource with the correct parameters."""
        uri_params = set(re.findall(r"\{([^}]+)\}", uri_pattern))

        if not uri_params:
            async def static_handler() -> ResourceResponse:
                """Handle static resource request."""
                return await resource.read()

            static_handler.__name__ = resource.name
            static_handler.__doc__ = resource.description
            return static_handler
        else:
            params_str = ", ".join(uri_params)
            func_def = f"async def param_handler({params_str}) -> ResourceResponse:\n"
            func_def += f'    """{resource.description}"""\n'
            func_def += f"    return await resource.read({params_str})"

            namespace = {"resource": resource, "ResourceResponse": ResourceResponse}
            exec(func_def, namespace)

            handler = namespace["param_handler"]
            handler.__name__ = resource.name
            return handler

    def register_mcp_handlers(self, mcp: FastMCP) -> None:
        """Register all resources as MCP handlers."""
        for uri_pattern, resource in self._uri_patterns.items():
            handler = self.create_handler(resource, uri_pattern)

            wrapped_handler = mcp.resource(
                uri=uri_pattern,
                name=resource.name,
                description=resource.description,
                mime_type=resource.mime_type,
            )(handler)

            wrapped_handler.__name__ = resource.name
            wrapped_handler.__doc__ = resource.description
