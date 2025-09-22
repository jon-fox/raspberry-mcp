"""Test IR transmitter tool for verifying hardware functionality."""

from typing import Dict, Any
import logging

from mcp_server.interfaces.tool import Tool, ToolResponse, BaseToolInput
from mcp_server.utils.ir_event_controls import ir_send
from pydantic import Field

logger = logging.getLogger(__name__)


class TestIRTransmitterRequest(BaseToolInput):
    """Request model for testing IR transmitter."""
    pass


class TestIRTransmitterResponse(BaseToolInput):
    """Response model for IR transmitter test."""
    
    success: bool = Field(description="Whether IR was transmitted")
    message: str = Field(description="Test result details")


class TestIRTransmitter(Tool):
    """Send a simple IR test signal to verify transmitter is working."""

    name = "TestIRTransmitter"
    description = "Send a simple IR test signal on GPIO17 to verify the transmitter is working."
    input_model = TestIRTransmitterRequest
    output_model = TestIRTransmitterResponse

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: TestIRTransmitterRequest) -> ToolResponse:
        """Send test IR signal."""
        logger.info("Starting IR transmitter test")
        logger.info("Sending test signal on GPIO17 at 38kHz")
        
        success, message = await ir_send("test", "0x00")
        
        if success:
            logger.info("IR transmitter test completed successfully")
        else:
            logger.error(f"IR transmitter test failed: {message}")
        
        output = TestIRTransmitterResponse(
            success=success,
            message=message
        )
        
        return ToolResponse.from_model(output)