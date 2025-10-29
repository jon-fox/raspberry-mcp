"""Dummy AC control tool - simulates AC cooling by adjusting temperature."""

from typing import Dict, Any
import logging

from mcp_server.tools.simulation.ac_models import (
    ControlACInput,
    ControlACOutput,
)
from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.utils.simulated_environment import SimulatedEnvironment

logger = logging.getLogger(__name__)


class ControlSimulatedAC(Tool):
    """Dummy AC control that simulates cooling by adjusting temperature when called."""

    name = "ControlSimulatedAC"
    description = (
        "Dummy AC control for testing. 'turn_on' cools by 2°F immediately. "
        "'turn_off' does nothing (just returns status). 'status' shows current temp. "
        "Call turn_on repeatedly to simulate continuous cooling. "
        "This is a dummy tool - in production use SendIRCommand for real AC."
    )
    input_model = ControlACInput
    output_model = ControlACOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ControlACInput) -> ToolResponse:
        """Execute AC control command."""
        logger.info(f"=== AC Control: {input_data.action} ===")
        
        try:
            env = SimulatedEnvironment.get_instance()
            
            if not env.is_simulation_enabled():
                return ToolResponse.from_model(ControlACOutput(
                    success=False,
                    message="Simulation not enabled. Use SimulateClimate to enable first.",
                    ac_running=False
                ))
            
            # Get current temperature
            success, _, temp_f, _, _ = env.read_sensor()
            if not success:
                return ToolResponse.from_model(ControlACOutput(
                    success=False,
                    message="Failed to read sensor",
                    ac_running=False
                ))
            
            if input_data.action == "turn_on":
                if input_data.target_temp_f is None:
                    return ToolResponse.from_model(ControlACOutput(
                        success=False,
                        message="target_temp_f required for turn_on",
                        ac_running=False
                    ))
                
                # Check if already at or below target
                if temp_f <= input_data.target_temp_f:
                    logger.info(f"Already at target: {temp_f:.1f}°F ≤ {input_data.target_temp_f}°F")
                    return ToolResponse.from_model(ControlACOutput(
                        success=True,
                        message=f"Target reached! Current {temp_f:.1f}°F ≤ target {input_data.target_temp_f}°F. AC not needed.",
                        ac_running=False,
                        target_temp=input_data.target_temp_f,
                        current_temp=temp_f
                    ))
                
                # Cool by 2 degrees immediately
                env.adjust_temperature(-2.0)
                new_temp = temp_f - 2.0
                
                logger.info(f"AC cooling: {temp_f:.1f}°F → {new_temp:.1f}°F (target: {input_data.target_temp_f}°F)")
                return ToolResponse.from_model(ControlACOutput(
                    success=True,
                    message=f"AC cooled from {temp_f:.1f}°F to {new_temp:.1f}°F (target: {input_data.target_temp_f}°F)",
                    ac_running=True,
                    target_temp=input_data.target_temp_f,
                    current_temp=new_temp
                ))
            
            elif input_data.action == "turn_off":
                logger.info(f"AC turned OFF at {temp_f:.1f}°F")
                return ToolResponse.from_model(ControlACOutput(
                    success=True,
                    message=f"AC turned OFF (current temp: {temp_f:.1f}°F)",
                    ac_running=False,
                    current_temp=temp_f
                ))
            
            elif input_data.action == "status":
                return ToolResponse.from_model(ControlACOutput(
                    success=True,
                    message=f"Current temperature: {temp_f:.1f}°F",
                    ac_running=False,
                    current_temp=temp_f
                ))
            
            else:
                return ToolResponse.from_model(ControlACOutput(
                    success=False,
                    message=f"Unknown action: {input_data.action}",
                    ac_running=False
                ))
            
        except Exception as e:
            logger.error(f"AC control failed: {e}", exc_info=True)
            return ToolResponse.from_model(ControlACOutput(
                success=False,
                message=f"Failed: {str(e)}",
                ac_running=False
            ))
