"""Test IR transmitter tool for verifying hardware functionality."""

import asyncio
import time
from typing import Dict, Any
import logging

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.ir_control.ir_models import TestIRTransmitterRequest, TestIRTransmitterResponse
from mcp_server.utils.ir_event_controls import ir_send

logger = logging.getLogger(__name__)


class TestIRTransmitter(Tool):
    """Send repeated IR test signals to verify transmitter is working."""

    name = "TestIRTransmitter"
    description = "Send repeated IR test signals on GPIO17 to verify the transmitter is working. Sends signals every 2 seconds for a specified duration."
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
        """Send repeated test IR signals."""
        start_time = time.time()
        transmissions_sent = 0
        
        duration_seconds = input_data.duration_minutes * 60
        interval_seconds = input_data.interval_seconds
        
        logger.info(f"Starting IR transmitter test: {input_data.duration_minutes} minutes, {interval_seconds}s intervals")
        logger.info(f"Will send test signals on GPIO17 at 38kHz every {interval_seconds} seconds")
        
        success = True
        errors = []
        
        try:
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Check if we've exceeded the duration
                if elapsed >= duration_seconds:
                    logger.info(f"Test duration reached ({input_data.duration_minutes} minutes), stopping")
                    break
                
                # Send test signal
                transmissions_sent += 1
                logger.info(f"Sending test transmission #{transmissions_sent} (elapsed: {elapsed:.1f}s)")
                
                signal_success, signal_message = await ir_send("test", "0x12345678")
                
                if signal_success:
                    logger.info(f"Transmission #{transmissions_sent} successful: {signal_message}")
                else:
                    logger.error(f"Transmission #{transmissions_sent} failed: {signal_message}")
                    errors.append(f"Transmission #{transmissions_sent}: {signal_message}")
                    # Continue sending even if some fail
                
                # Wait for the interval (unless we're at the end)
                next_time = start_time + (transmissions_sent * interval_seconds)
                current_time = time.time()
                
                if next_time > current_time and (next_time - start_time) < duration_seconds:
                    sleep_time = next_time - current_time
                    logger.debug(f"Waiting {sleep_time:.1f}s until next transmission")
                    await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            logger.info(f"IR transmitter test cancelled after {transmissions_sent} transmissions")
            raise
        except Exception as e:
            logger.error(f"IR transmitter test error: {e}")
            success = False
            errors.append(f"Test error: {str(e)}")
        
        final_time = time.time()
        actual_duration = final_time - start_time
        
        # Generate result message
        if success and not errors:
            message = f"IR transmitter test completed successfully. Sent {transmissions_sent} test signals over {actual_duration:.1f} seconds."
        elif errors:
            message = f"IR transmitter test completed with {len(errors)} errors. Sent {transmissions_sent} signals. Errors: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                message += f" (and {len(errors) - 3} more)"
        else:
            message = f"IR transmitter test failed after {transmissions_sent} transmissions."
        
        logger.info(f"IR transmitter test finished: {transmissions_sent} transmissions in {actual_duration:.1f}s")
        
        output = TestIRTransmitterResponse(
            success=success and len(errors) == 0,
            message=message,
            transmissions_sent=transmissions_sent,
            duration_seconds=actual_duration
        )
        
        return ToolResponse.from_model(output)