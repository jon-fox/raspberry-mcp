"""Simple tool for controlling climate simulation - replaces real sensor for testing."""

from typing import Dict, Any
import logging

from mcp_server.tools.simulation.simulation_models import (
    SimulateClimateInput,
    SimulateClimateOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.utils.simulated_environment import SimulatedEnvironment

logger = logging.getLogger(__name__)


class SimulateClimate(Tool):
    """Simple tool to control simulated climate for testing AC reactions."""

    name = "SimulateClimate"
    description = (
        "Controls climate simulation for testing. Actions: "
        "'enable' to start simulation (optionally set temp_f and humidity), "
        "'adjust_temp' to change temperature by delta_f degrees, "
        "'disable' to stop simulation and use real sensors. "
        "Example: Set temp to 75°F, then use adjust_temp with delta_f=-2.0 multiple times to simulate AC cooling."
    )
    input_model = SimulateClimateInput
    output_model = SimulateClimateOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SimulateClimateInput) -> ToolResponse:
        """Execute simulation control."""
        logger.info(f"=== Simulation Control: {input_data.action} ===")
        
        try:
            env = SimulatedEnvironment.get_instance()
            
            if input_data.action == "enable":
                temp = input_data.temp_f or 70.0
                humidity = input_data.humidity or 50.0
                env.enable_simulation(temp, humidity)
                status = env.get_status()
                output = SimulateClimateOutput(
                    success=True,
                    message=f"Simulation enabled at {temp}°F, {humidity}% humidity",
                    current_temp_f=status['temp_f'],
                    current_humidity=status['humidity']
                )
                
            elif input_data.action == "adjust_temp":
                if input_data.delta_f is None:
                    return ToolResponse.from_model(SimulateClimateOutput(
                        success=False,
                        message="delta_f required for adjust_temp action"
                    ))
                
                if not env.is_simulation_enabled():
                    return ToolResponse.from_model(SimulateClimateOutput(
                        success=False,
                        message="Simulation not enabled. Use action='enable' first."
                    ))
                
                env.adjust_temperature(input_data.delta_f)
                status = env.get_status()
                output = SimulateClimateOutput(
                    success=True,
                    message=f"Temperature adjusted by {input_data.delta_f:+.1f}°F to {status['temp_f']}°F",
                    current_temp_f=status['temp_f'],
                    current_humidity=status['humidity']
                )
                
            elif input_data.action == "disable":
                env.disable_simulation()
                output = SimulateClimateOutput(
                    success=True,
                    message="Simulation disabled, using real sensors"
                )
            
            else:
                output = SimulateClimateOutput(
                    success=False,
                    message=f"Unknown action: {input_data.action}"
                )
            
            logger.info(f"Result: {output.message}")
            return ToolResponse.from_model(output)
            
        except Exception as e:
            logger.error(f"Simulation control failed: {e}", exc_info=True)
            return ToolResponse.from_model(SimulateClimateOutput(
                success=False,
                message=f"Failed: {str(e)}"
            ))
