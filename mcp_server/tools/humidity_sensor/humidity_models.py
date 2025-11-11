from typing import Optional
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class ReadHumidityInput(BaseToolInput):
    """Input for reading humidity and temperature from DHT22 sensor."""

    model_config = ConfigDict(json_schema_extra={"examples": [{}]})

    pass


class ReadHumidityOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "temperature_c": 22.5,
                    "temperature_f": 72.5,
                    "humidity": 45.2,
                    "timestamp": "2025-10-22T10:30:45.123456",
                    "message": "Successfully read sensor data.",
                }
            ]
        }
    )

    success: bool = Field(
        ..., description="Whether the sensor read was successful.", examples=[True]
    )
    temperature_c: Optional[float] = Field(
        None,
        description="Temperature in Celsius.",
        examples=[22.5],
    )
    temperature_f: Optional[float] = Field(
        None,
        description="Temperature in Fahrenheit.",
        examples=[72.5],
    )
    humidity: Optional[float] = Field(
        None,
        description="Relative humidity as a percentage.",
        examples=[45.2],
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when the reading was taken.",
        examples=["2025-10-22T10:30:45.123456"],
    )
    message: str = Field(
        ...,
        description="Status message or error description.",
        examples=["Successfully read sensor data.", "Sensor read failed, retrying..."],
    )
