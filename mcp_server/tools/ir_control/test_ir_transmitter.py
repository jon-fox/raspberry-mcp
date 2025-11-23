"""Test IR transmitter tool for verifying hardware functionality."""

import asyncio
import logging
import time
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.ir_control.ir_models import (
    TestIRTransmitterRequest,
    TestIRTransmitterResponse,
)
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
        errors = []

        logger.info(f"Starting IR transmitter test: {input_data.duration_minutes} min, {interval_seconds}s intervals")

        test_patterns = [
            ("nec", "0x00FF12ED"),
            ("nec", "0x00FFAA55"),
            ("sony", "0x12345678"),
        ]

        try:
            while True:
                elapsed = time.time() - start_time
                if elapsed >= duration_seconds:
                    break

                transmissions_sent += 1
                pattern_index = (transmissions_sent - 1) % len(test_patterns)
                protocol, hex_code = test_patterns[pattern_index]

                signal_success, signal_message = ir_send(protocol, hex_code)

                if not signal_success:
                    errors.append(f"#{transmissions_sent}: {signal_message}")

                next_time = start_time + (transmissions_sent * interval_seconds)
                current_time = time.time()

                if next_time > current_time and (next_time - start_time) < duration_seconds:
                    await asyncio.sleep(next_time - current_time)

        except asyncio.CancelledError:
            logger.info(f"Test cancelled after {transmissions_sent} transmissions")
            raise
        except Exception as e:
            logger.error(f"Test error: {e}")
            errors.append(f"Test error: {str(e)}")

        actual_duration = time.time() - start_time
        success = len(errors) == 0

        if success:
            message = f"Test completed. Sent {transmissions_sent} IR signals over {actual_duration:.1f}s."
        else:
            message = f"Test completed with {len(errors)} errors. Sent {transmissions_sent} signals. Errors: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                message += f" (and {len(errors) - 3} more)"

        output = TestIRTransmitterResponse(
            success=success,
            message=message,
            transmissions_sent=transmissions_sent,
            duration_seconds=actual_duration,
        )

        return ToolResponse.from_model(output)
