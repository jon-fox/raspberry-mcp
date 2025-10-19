"""Tool for reading humidity and temperature from DHT22 sensor."""

from typing import Dict, Any
import logging
import time

from mcp_server.tools.humidity_sensor.humidity_models import (
    ReadHumidityInput,
    ReadHumidityOutput,
)
from mcp_server.constants.gpio_pins import GPIO_PIN_17
from mcp_server.interfaces.tool import Tool, ToolResponse
from pigpio_dht import DHT22

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
            logger.debug("Importing pigpio_dht library")
            
            # Create sensor instance and read
            # Assumes 10kΩ pull-up resistor is installed between DATA (GPIO 17) and VCC (3.3V)
            logger.info(f"Initializing DHT22 sensor on GPIO {GPIO_PIN_17}")
            sensor = DHT22(GPIO_PIN_17)
            
            # Increase timeout for more reliable reading
            sensor.timeout_secs = 2.0
            logger.debug(f"Sensor timeout set to {sensor.timeout_secs} seconds")
            
            try:
                logger.info("Attempting to read sensor data...")
                result = sensor.read()
                logger.debug(f"Raw sensor result: {result}")
                
                if result['valid']:
                    temperature_c = result['temp_c']
                    humidity = result['humidity']
                    temperature_f = temperature_c * 9.0 / 5.0 + 32.0
                    
                    logger.info(f"✓ Successfully read sensor: {temperature_c:.1f}°C ({temperature_f:.1f}°F), {humidity:.1f}% humidity")
                    output = ReadHumidityOutput(
                        success=True,
                        temperature_c=round(temperature_c, 1),
                        temperature_f=round(temperature_f, 1),
                        humidity=round(humidity, 1),
                        message=f"Successfully read sensor data: {temperature_c:.1f}°C ({temperature_f:.1f}°F), {humidity:.1f}% humidity",
                    )
                else:
                    logger.warning(f"✗ Sensor reading invalid - bad checksum or data. Result: {result}")
                    logger.info("Invalid data (all zeros) suggests: 1) Missing pull-up resistor (10kΩ), 2) Wrong data pin connected, or 3) Sensor initialization issue")
                    logger.info("Troubleshooting: Ensure DATA pin connected to GPIO 17, VCC to 3.3V, GND to GND, and 10kΩ resistor between DATA and VCC")
                    output = ReadHumidityOutput(
                        success=False,
                        message=f"Sensor read failed (invalid data/checksum). Raw data: temp={result.get('temp_c', 0)}°C, humidity={result.get('humidity', 0)}%. Check: 1) 10kΩ pull-up resistor between DATA and VCC, 2) Correct wiring (DATA→GPIO17, VCC→3.3V, GND→GND), 3) Retry reading.",
                    )
            except TimeoutError as e:
                logger.warning(f"✗ DHT22 sensor timeout after {sensor.timeout_secs}s: {e}")
                logger.info("Timeout suggests: 1) Sensor not connected to GPIO 17, 2) Power issue, or 3) Faulty sensor")
                output = ReadHumidityOutput(
                    success=False,
                    message=f"Sensor timeout: {str(e)}. Check sensor connection or try again.",
                )
            
        except ImportError as e:
            logger.error(f"✗ Required libraries not available: {e}")
            output = ReadHumidityOutput(
                success=False,
                message=f"DHT library not installed: {str(e)}. Install 'pigpio-dht' package.",
            )
        except Exception as e:
            logger.error(f"✗ Unexpected error reading DHT sensor: {e}", exc_info=True)
            output = ReadHumidityOutput(
                success=False,
                message=f"Unexpected error reading sensor: {str(e)}",
            )
        
        logger.info(f"=== DHT22 sensor read complete. Success: {output.success} ===")
        return ToolResponse.from_model(output)
