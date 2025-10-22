"""Tool for reading light level from photo sensor."""

from typing import Dict, Any
import logging

from mcp_server.tools.photo_sensor.photo_sensor_models import (
    ReadPhotoSensorInput,
    ReadPhotoSensorOutput,
)
from mcp_server.constants.gpio_pins import GPIO_PIN_27
from mcp_server.interfaces.tool import Tool, ToolResponse

logger = logging.getLogger(__name__)


class ReadPhotoSensor(Tool):
    """Tool that reads light level from a photo sensor (LM393 + photoresistor)."""

    name = "ReadPhotoSensor"
    description = "Reads light level (bright/dark) from a photo sensor connected to a GPIO pin"
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
        """Execute the read photo sensor tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response with light level (bright/dark)
        """
        logger.info(f"=== Starting photo sensor read on GPIO pin {GPIO_PIN_27} ===")
        
        try:
            import gpiod
            import os
            
            logger.debug("Imported gpiod library")
            
            # Check for available GPIO chips
            gpiochip_paths = ['/dev/gpiochip0', '/dev/gpiochip1', '/dev/gpiochip2']
            available_chips = [path for path in gpiochip_paths if os.path.exists(path)]
            
            if not available_chips:
                logger.error("No GPIO chips found. Available devices: " + str(os.listdir('/dev')))
                raise FileNotFoundError(
                    "No GPIO chip devices found. Container may not have --device /dev/gpiochip0 mapped. "
                    "Available /dev devices: " + ', '.join(os.listdir('/dev'))
                )
            
            logger.info(f"Available GPIO chips: {available_chips}")
            
            # Open the first available GPIO chip
            chip_path = available_chips[0]
            logger.info(f"Opening GPIO chip: {chip_path}")
            
            # Use gpiod v2 API
            chip = gpiod.Chip(chip_path)
            
            try:
                # Request the GPIO line as input (gpiod v2 API)
                line_settings = gpiod.LineSettings(direction=gpiod.line.Direction.INPUT)
                line_request = chip.request_lines(
                    config={GPIO_PIN_27: line_settings},
                    consumer="photo_sensor"
                )
                
                # Read sensor state
                # LM393 photo sensor module outputs LOW (0) when bright, HIGH (1) when dark
                sensor_state = line_request.get_value(GPIO_PIN_27)
                is_bright = not bool(sensor_state)  # Invert: 0=bright, 1=dark
                
                light_level = "Bright" if is_bright else "Dark"
                logger.info(f"✓ Photo sensor reading: {light_level} (GPIO {GPIO_PIN_27} = {sensor_state})")
                
                output = ReadPhotoSensorOutput(
                    success=True,
                    is_bright=is_bright,
                    message=f"Light detected: {light_level}",
                )
            finally:
                # Release the line request
                if 'line_request' in locals():
                    line_request.release()
                chip.close()
            
        except ImportError as e:
            logger.error(f"✗ Required libraries not available: {e}")
            output = ReadPhotoSensorOutput(
                success=False,
                is_bright=False,
                message=f"GPIO library not installed: {str(e)}. Install 'gpiod' package.",
            )
        except Exception as e:
            logger.error(f"✗ Unexpected error reading photo sensor: {e}", exc_info=True)
            output = ReadPhotoSensorOutput(
                success=False,
                is_bright=False,
                message=f"Unexpected error reading sensor: {str(e)}",
            )
        
        logger.info(f"=== Photo sensor read complete. Success: {output.success} ===")
        return ToolResponse.from_model(output)
