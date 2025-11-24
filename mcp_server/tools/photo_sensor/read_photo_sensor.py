"""Tool for reading light level from photo sensor."""

import logging
from datetime import datetime
from typing import Dict, Any

from mcp_server.constants.gpio_pins import GPIO_PIN_27
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.photo_sensor.photo_sensor_models import (
    ReadPhotoSensorInput,
    ReadPhotoSensorOutput,
)

import gpiod
import os

logger = logging.getLogger(__name__)


class ReadPhotoSensor(Tool):
    """Tool that reads light level from a photo sensor (LM393 + photoresistor)."""

    name = "ReadPhotoSensor"
    description = (
        "Reads light level (bright/dark) from a photo sensor connected to a GPIO pin"
    )
    input_model = ReadPhotoSensorInput
    output_model = ReadPhotoSensorOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ReadPhotoSensorInput) -> ToolResponse:
        """Execute the read photo sensor tool."""
        logger.info(f"Reading photo sensor on GPIO {GPIO_PIN_27}")

        try:

            gpiochip_paths = ["/dev/gpiochip0", "/dev/gpiochip1", "/dev/gpiochip2"]
            available_chips = [path for path in gpiochip_paths if os.path.exists(path)]

            if not available_chips:
                logger.error("No GPIO chips found")
                raise FileNotFoundError(
                    "No GPIO chip devices found. Container may not have --device /dev/gpiochip0 mapped. "
                    "Available /dev devices: " + ", ".join(os.listdir("/dev"))
                )

            chip_path = available_chips[0]

            chip = gpiod.Chip(chip_path)

            try:
                line_settings = gpiod.LineSettings(direction=gpiod.line.Direction.INPUT)
                line_request = chip.request_lines(
                    config={GPIO_PIN_27: line_settings}, consumer="photo_sensor"
                )

                sensor_state = line_request.get_value(GPIO_PIN_27)
                is_bright = not bool(sensor_state)

                timestamp = datetime.utcnow().isoformat()

                light_level = "Bright" if is_bright else "Dark"
                logger.info(f"Photo sensor: {light_level}")

                output = ReadPhotoSensorOutput(
                    success=True,
                    is_bright=is_bright,
                    raw_value=sensor_state,
                    gpio_pin=GPIO_PIN_27,
                    timestamp=timestamp,
                    message=f"Light detected: {light_level}",
                    sensor_info="LM393 digital photo sensor (binary output only)",
                )
            finally:
                if "line_request" in locals():
                    line_request.release()
                chip.close()

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            output = ReadPhotoSensorOutput(
                success=False,
                is_bright=False,
                message=f"Unexpected error reading sensor: {str(e)}",
            )

        return ToolResponse.from_model(output)
