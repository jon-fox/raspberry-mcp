import logging
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.simulation.climate_models import (
    ClimateSimulationInput,
    ClimateSimulationOutput,
)
from mcp_server.utils.simulated_environment import SimulatedEnvironment

logger = logging.getLogger(__name__)


class ClimateSimulation(Tool):
    """Unified tool for controlling climate simulation and simulated AC."""

    name = "ClimateSimulation"
    description = (
        "Controls climate simulation for testing. "
        "'enable' starts simulation with optional temp/humidity. "
        "'cool_ac' simulates AC cooling by 2°F (checks target temp). "
        "'adjust_temp' manually adjusts temperature by delta. "
        "'status' shows current state. "
        "'disable' stops simulation and uses real sensors."
    )
    input_model = ClimateSimulationInput
    output_model = ClimateSimulationOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ClimateSimulationInput) -> ToolResponse:
        logger.info(f"Climate simulation action: {input_data.action}")

        try:
            env = SimulatedEnvironment.get_instance()

            if input_data.action == "enable":
                temp = input_data.temp_f or 70.0
                humidity = input_data.humidity or 50.0
                env.enable_simulation(temp, humidity)
                status = env.get_status()
                output = ClimateSimulationOutput(
                    success=True,
                    message=f"Simulation enabled at {temp}°F, {humidity}% humidity",
                    current_temp_f=status["temp_f"],
                    current_humidity=status["humidity"],
                )

            elif input_data.action == "disable":
                env.disable_simulation()
                output = ClimateSimulationOutput(
                    success=True,
                    message="Simulation disabled, using real sensors",
                )

            elif input_data.action == "adjust_temp":
                if input_data.delta_f is None:
                    return ToolResponse.from_model(
                        ClimateSimulationOutput(
                            success=False,
                            message="delta_f required for adjust_temp action",
                        )
                    )

                if not env.is_simulation_enabled():
                    return ToolResponse.from_model(
                        ClimateSimulationOutput(
                            success=False,
                            message="Simulation not enabled. Use action='enable' first.",
                        )
                    )

                env.adjust_temperature(input_data.delta_f)
                status = env.get_status()
                output = ClimateSimulationOutput(
                    success=True,
                    message=f"Temperature adjusted by {input_data.delta_f:+.1f}°F to {status['temp_f']}°F",
                    current_temp_f=status["temp_f"],
                    current_humidity=status["humidity"],
                )

            elif input_data.action == "cool_ac":
                if not env.is_simulation_enabled():
                    return ToolResponse.from_model(
                        ClimateSimulationOutput(
                            success=False,
                            message="Simulation not enabled. Use action='enable' first.",
                        )
                    )

                if input_data.target_temp_f is None:
                    return ToolResponse.from_model(
                        ClimateSimulationOutput(
                            success=False,
                            message="target_temp_f required for cool_ac action",
                        )
                    )

                success, _, temp_f, _, _ = env.read_sensor()
                if not success:
                    return ToolResponse.from_model(
                        ClimateSimulationOutput(
                            success=False,
                            message="Failed to read sensor",
                        )
                    )

                if temp_f <= input_data.target_temp_f:
                    logger.info(f"Already at target: {temp_f:.1f}°F ≤ {input_data.target_temp_f}°F")
                    output = ClimateSimulationOutput(
                        success=True,
                        message=f"Target reached! Current {temp_f:.1f}°F ≤ target {input_data.target_temp_f}°F. AC not needed.",
                        current_temp_f=temp_f,
                        ac_running=False,
                        target_temp=input_data.target_temp_f,
                    )
                else:
                    env.adjust_temperature(-2.0)
                    new_temp = temp_f - 2.0
                    logger.info(f"AC cooling: {temp_f:.1f}°F → {new_temp:.1f}°F (target: {input_data.target_temp_f}°F)")
                    output = ClimateSimulationOutput(
                        success=True,
                        message=f"AC cooled from {temp_f:.1f}°F to {new_temp:.1f}°F (target: {input_data.target_temp_f}°F)",
                        current_temp_f=new_temp,
                        ac_running=True,
                        target_temp=input_data.target_temp_f,
                    )

            elif input_data.action == "status":
                if not env.is_simulation_enabled():
                    output = ClimateSimulationOutput(
                        success=True,
                        message="Simulation disabled, using real sensors",
                    )
                else:
                    status = env.get_status()
                    output = ClimateSimulationOutput(
                        success=True,
                        message=f"Simulation active: {status['temp_f']}°F, {status['humidity']}% humidity",
                        current_temp_f=status["temp_f"],
                        current_humidity=status["humidity"],
                    )

            else:
                output = ClimateSimulationOutput(
                    success=False,
                    message=f"Unknown action: {input_data.action}",
                )

            return ToolResponse.from_model(output)

        except Exception as e:
            logger.error(f"Climate simulation failed: {e}", exc_info=True)
            return ToolResponse.from_model(
                ClimateSimulationOutput(success=False, message=f"Failed: {str(e)}")
            )
