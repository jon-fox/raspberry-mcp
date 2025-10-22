"""Tool for reading humidity and temperature from DHT22 sensor."""

from typing import Dict, Any
from datetime import datetime
import logging
import time

from mcp_server.tools.humidity_sensor.humidity_models import (
    ReadHumidityInput,
    ReadHumidityOutput,
)
from mcp_server.constants.gpio_pins import GPIO_PIN_17
from mcp_server.interfaces.tool import Tool, ToolResponse

logger = logging.getLogger(__name__)


class ReadHumiditySensor(Tool):
    """Tool that reads temperature and humidity from a DHT22 sensor."""

    name = "ReadHumiditySensor"
    description = "Reads temperature and humidity data from a DHT22 sensor connected to a GPIO pin"
    input_model = ReadHumidityInput
    output_model = ReadHumidityOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ReadHumidityInput) -> ToolResponse:
        """Execute the read humidity sensor tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response with temperature and humidity readings
        """
        logger.info(f"=== Starting DHT22 sensor read on GPIO pin {GPIO_PIN_17} ===")
        
        try:
            import board
            import adafruit_dht
            logger.debug("Imported adafruit_dht library")
            
            # Map GPIO pin to board pin (GPIO 17 = D17)
            board_pin = board.D17
            
            # Create DHT22 sensor instance
            logger.info(f"Initializing DHT22 sensor on GPIO {GPIO_PIN_17}")
            dht = adafruit_dht.DHT22(board_pin, use_pulseio=False)
            
            # DHT22 sensors often need multiple read attempts
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Attempting to read sensor data (attempt {attempt}/{max_retries})...")
                    
                    temperature_c = dht.temperature
                    humidity = dht.humidity
                    
                    if temperature_c is not None and humidity is not None:
                        temperature_f = temperature_c * 9.0 / 5.0 + 32.0
                        timestamp = datetime.utcnow().isoformat()
                        
                        logger.info(f"✓ Successfully read sensor on attempt {attempt}: {temperature_c:.1f}°C ({temperature_f:.1f}°F), {humidity:.1f}% humidity")
                        output = ReadHumidityOutput(
                            success=True,
                            temperature_c=round(temperature_c, 1),
                            temperature_f=round(temperature_f, 1),
                            humidity=round(humidity, 1),
                            timestamp=timestamp,
                            message=f"Successfully read sensor data: {temperature_c:.1f}°C ({temperature_f:.1f}°F), {humidity:.1f}% humidity",
                        )
                        break  # Success, exit retry loop
                    else:
                        logger.warning(f"✗ Sensor returned None values on attempt {attempt}")
                        if attempt < max_retries:
                            logger.info(f"Waiting 2 seconds before retry...")
                            time.sleep(2)
                        else:
                            logger.error("All retry attempts returned None")
                            output = ReadHumidityOutput(
                                success=False,
                                message=f"Sensor read failed after {max_retries} attempts (returned None). Check: 1) Sensor connections, 2) Power supply (3.3V), 3) Try a different DHT22 sensor.",
                            )
                except RuntimeError as e:
                    logger.warning(f"✗ DHT22 sensor RuntimeError on attempt {attempt}: {e}")
                    if attempt < max_retries:
                        logger.info(f"Waiting 2 seconds before retry...")
                        time.sleep(2)
                    else:
                        logger.error("All retry attempts failed with RuntimeError")
                        output = ReadHumidityOutput(
                            success=False,
                            message=f"Sensor read failed after {max_retries} attempts: {str(e)}. DHT sensors are sensitive - try again.",
                        )
            
            # Clean up
            dht.exit()
            
        except ImportError as e:
            logger.error(f"✗ Required libraries not available: {e}")
            output = ReadHumidityOutput(
                success=False,
                message=f"DHT library not installed: {str(e)}. Install 'adafruit-circuitpython-dht' package.",
            )
        except Exception as e:
            logger.error(f"✗ Unexpected error reading DHT sensor: {e}", exc_info=True)
            output = ReadHumidityOutput(
                success=False,
                message=f"Unexpected error reading sensor: {str(e)}",
            )
        
        logger.info(f"=== DHT22 sensor read complete. Success: {output.success} ===")
        return ToolResponse.from_model(output)
