"""Tool for reading light level from photo sensor."""

from typing import Dict, Any
import logging
import RPi.GPIO as GPIO

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
        logger.info(f"Reading photo sensor on GPIO pin {GPIO_PIN_27}")
        
        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(GPIO_PIN_27, GPIO.IN)
            
            try:
                # Read sensor state
                sensor_state = GPIO.input(GPIO_PIN_27)
                is_bright = bool(sensor_state)
                
                light_level = "Bright" if is_bright else "Dark"
                logger.info(f"Photo sensor reading: {light_level}")
                
                output = ReadPhotoSensorOutput(
                    success=True,
                    is_bright=is_bright,
                    message=f"Light detected: {light_level}",
                )
            finally:
                # Clean up GPIO
                GPIO.cleanup()
            
        except ImportError as e:
            logger.error(f"Required libraries not available: {e}")
            output = ReadPhotoSensorOutput(
                success=False,
                is_bright=False,
                message=f"GPIO library not installed: {str(e)}. Install 'RPi.GPIO' package.",
            )
        except Exception as e:
            logger.error(f"Unexpected error reading photo sensor: {e}", exc_info=True)
            output = ReadPhotoSensorOutput(
                success=False,
                is_bright=False,
                message=f"Unexpected error reading sensor: {str(e)}",
            )
        
        return ToolResponse.from_model(output)
