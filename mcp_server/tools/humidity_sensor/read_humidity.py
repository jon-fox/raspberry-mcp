import logging
import time
from datetime import datetime
from typing import Dict, Any

from mcp_server.constants.gpio_pins import GPIO_PIN_17
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.humidity_sensor.humidity_models import (
    ReadHumidityInput,
    ReadHumidityOutput,
)
from mcp_server.utils.simulated_environment import SimulatedEnvironment

# these libraries can be problematic outside of raspberry pi device
import board
import adafruit_dht

logger = logging.getLogger(__name__)


class ReadHumiditySensor(Tool):
    """Tool that reads temperature and humidity from a DHT22 sensor or simulation."""

    name = "ReadHumiditySensor"
    description = (
        "Reads temperature and humidity data from a DHT22 sensor connected to a GPIO pin. "
        "If climate simulation is enabled, reads from simulated environment instead. "
        "Returns temperature in both Celsius and Fahrenheit, plus relative humidity percentage."
    )
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
        """Execute the read humidity sensor tool."""
        env = SimulatedEnvironment.get_instance()
        if env.is_simulation_enabled():
            success, temp_c, temp_f, humidity, message = env.read_sensor()

            if success:
                timestamp = datetime.utcnow().isoformat()
                logger.info(
                    f"Simulated sensor: {temp_c:.1f}°C ({temp_f:.1f}°F), {humidity:.1f}%"
                )
                output = ReadHumidityOutput(
                    success=True,
                    temperature_c=round(temp_c, 1),
                    temperature_f=round(temp_f, 1),
                    humidity=round(humidity, 1),
                    timestamp=timestamp,
                    message=message,
                )
            else:
                logger.error(f"Simulated sensor failed: {message}")
                output = ReadHumidityOutput(
                    success=False,
                    message=message,
                )

            return ToolResponse.from_model(output)

        logger.info(f"Reading DHT22 sensor on GPIO {GPIO_PIN_17}")

        try:

            board_pin = board.D17
            dht = adafruit_dht.DHT22(board_pin, use_pulseio=False)

            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    temperature_c = dht.temperature
                    humidity = dht.humidity

                    if temperature_c is not None and humidity is not None:
                        temperature_f = temperature_c * 9.0 / 5.0 + 32.0
                        timestamp = datetime.utcnow().isoformat()

                        logger.info(
                            f"DHT22 read (attempt {attempt}): {temperature_c:.1f}°C ({temperature_f:.1f}°F), {humidity:.1f}%"
                        )
                        output = ReadHumidityOutput(
                            success=True,
                            temperature_c=round(temperature_c, 1),
                            temperature_f=round(temperature_f, 1),
                            humidity=round(humidity, 1),
                            timestamp=timestamp,
                            message=f"Successfully read sensor data: {temperature_c:.1f}°C ({temperature_f:.1f}°F), {humidity:.1f}% humidity",
                        )
                        break
                    else:
                        if attempt < max_retries:
                            time.sleep(2)
                        else:
                            logger.error(
                                f"Sensor returned None after {max_retries} attempts"
                            )
                            output = ReadHumidityOutput(
                                success=False,
                                message=f"Sensor read failed after {max_retries} attempts (returned None). Check: 1) Sensor connections, 2) Power supply (3.3V), 3) Try a different DHT22 sensor.",
                            )
                except RuntimeError as e:
                    if attempt < max_retries:
                        time.sleep(2)
                    else:
                        logger.error(f"RuntimeError after {max_retries} attempts: {e}")
                        output = ReadHumidityOutput(
                            success=False,
                            message=f"Sensor read failed after {max_retries} attempts: {str(e)}. DHT sensors are sensitive - try again.",
                        )

            dht.exit()

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            output = ReadHumidityOutput(
                success=False,
                message=f"Unexpected error reading sensor: {str(e)}",
            )

        return ToolResponse.from_model(output)
