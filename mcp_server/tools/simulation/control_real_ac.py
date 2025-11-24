import logging
import threading
import time
from typing import Dict, Any

from mcp_server.interfaces.tool import Tool, ToolResponse
from mcp_server.tools.simulation.climate_models import (
    ControlRealACInput,
    ControlRealACOutput,
)
from mcp_server.utils.simulated_environment import SimulatedEnvironment
from mcp_server.utils.smart_plug import turn_on, turn_off, get_ac_state

logger = logging.getLogger(__name__)


class ClimateController:
    """Manages automatic climate control with hysteresis."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the controller."""
        self._auto_control_enabled = False
        self._control_thread = None
        self._stop_control = False
        self._hysteresis_high = 1.0  # Turn on when temp > target + this
        self._hysteresis_low = 1.0  # Turn off when temp <= target - this
        self._check_interval = 10  # Check every 10 seconds

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        return cls()

    def start_automatic_control(self, target_temp_f: float):
        """Start automatic temperature control."""
        with self._lock:
            env = SimulatedEnvironment.get_instance()

            if not env.is_simulation_enabled():
                return (
                    False,
                    "Simulation not enabled. Enable with SimulateClimate first.",
                )

            env.set_target_temperature(target_temp_f)

            if self._control_thread and self._control_thread.is_alive():
                self._stop_control = True
                self._control_thread.join(timeout=2)

            self._stop_control = False
            self._auto_control_enabled = True
            self._control_thread = threading.Thread(
                target=self._control_loop, daemon=True
            )
            self._control_thread.start()

            logger.info(f"Automatic control started, target: {target_temp_f}°F")
            return True, f"Automatic control enabled, target: {target_temp_f}°F"

    def stop_automatic_control(self):
        """Stop automatic temperature control."""
        with self._lock:
            self._auto_control_enabled = False
            self._stop_control = True

            env = SimulatedEnvironment.get_instance()
            self._set_ac_state(False, env)

            logger.info("Automatic control stopped")
            return True, "Automatic control disabled, AC turned off"

    def is_auto_control_enabled(self) -> bool:
        """Check if automatic control is enabled."""
        with self._lock:
            return self._auto_control_enabled

    def _control_loop(self):
        """Background thread that monitors temperature and controls AC."""
        logger.info("Climate control loop started")

        while not self._stop_control:
            try:
                time.sleep(self._check_interval)

                if not self._auto_control_enabled:
                    break

                self._check_and_adjust_temperature()

            except Exception as e:
                logger.error(f"Error in climate control loop: {e}", exc_info=True)

        logger.info("Climate control loop stopped")

    def _check_and_adjust_temperature(self):
        """Check temperature and adjust AC state if needed."""
        env = SimulatedEnvironment.get_instance()

        if not env.is_simulation_enabled():
            logger.warning("Simulation disabled, stopping control")
            with self._lock:
                self._auto_control_enabled = False
            return

        success, _, temp_f, _, _ = env.read_sensor()
        if not success or temp_f is None:
            logger.warning("Failed to read sensor")
            return

        target_temp = env.get_target_temperature()
        if target_temp is None:
            logger.warning("No target temperature set")
            return

        ac_running = env.get_ac_running()

        should_turn_on = temp_f > (target_temp + self._hysteresis_high)
        should_turn_off = temp_f <= (target_temp - self._hysteresis_low)

        if not ac_running and should_turn_on:
            logger.info(
                f"Turning ON AC: {temp_f:.1f}°F > {target_temp + self._hysteresis_high:.1f}°F"
            )
            self._set_ac_state(True, env)

        elif ac_running and should_turn_off:
            logger.info(
                f"Turning OFF AC: {temp_f:.1f}°F <= {target_temp - self._hysteresis_low:.1f}°F"
            )
            self._set_ac_state(False, env)

    def _set_ac_state(self, turn_on_ac: bool, env: SimulatedEnvironment):
        """Set AC state (both Shelly plug and simulation)."""
        try:
            if turn_on_ac:
                success = turn_on()
                if not success:
                    logger.error("Failed to turn Shelly plug ON")
            else:
                success = turn_off()
                if not success:
                    logger.error("Failed to turn Shelly plug OFF")

            env.set_ac_running(turn_on_ac)

        except Exception as e:
            logger.error(f"Error setting AC state: {e}", exc_info=True)
            env.set_ac_running(turn_on_ac)


class ControlRealAC(Tool):
    """Tool for realistic AC control with Shelly smart plug and automatic temperature management."""

    name = "ControlRealAC"
    description = (
        "Controls real AC unit via Shelly smart plug with automatic temperature control. "
        "Actions: 'set_target' enables automatic control to maintain target temperature with hysteresis, "
        "'turn_on' manually turns on AC and plug, 'turn_off' manually turns off AC and plug, "
        "'status' shows current temperature and AC state, 'stop_auto' disables automatic control. "
        "Requires climate simulation to be enabled first. "
        "Temperature changes gradually: -0.3°F/sec when AC on, +0.05°F/sec drift when off."
    )
    input_model = ControlRealACInput
    output_model = ControlRealACOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: ControlRealACInput) -> ToolResponse:
        """Execute AC control command."""
        logger.info(f"Real AC control: {input_data.action}")

        env = SimulatedEnvironment.get_instance()
        controller = ClimateController.get_instance()

        try:
            if input_data.action == "set_target":
                if input_data.target_temp_f is None:
                    return ToolResponse.from_model(
                        ControlRealACOutput(
                            success=False,
                            message="target_temp_f required for 'set_target' action",
                        )
                    )

                success, message = controller.start_automatic_control(
                    input_data.target_temp_f
                )

                if success:
                    _, _, temp_f, _, _ = env.read_sensor()
                    ac_running = env.get_ac_running()

                    output = ControlRealACOutput(
                        success=True,
                        message=message,
                        ac_running=ac_running,
                        current_temp=temp_f,
                        target_temp=input_data.target_temp_f,
                        auto_control_enabled=True,
                    )
                else:
                    output = ControlRealACOutput(
                        success=False,
                        message=message,
                    )

            elif input_data.action == "turn_on":
                if not env.is_simulation_enabled():
                    return ToolResponse.from_model(
                        ControlRealACOutput(
                            success=False,
                            message="Simulation not enabled. Enable with SimulateClimate first.",
                        )
                    )

                success = turn_on()
                if success:
                    env.set_ac_running(True)
                    _, _, temp_f, _, _ = env.read_sensor()

                    logger.info(f"AC manually turned ON at {temp_f:.1f}°F")
                    output = ControlRealACOutput(
                        success=True,
                        message=f"AC turned ON (manual control), current temp: {temp_f:.1f}°F",
                        ac_running=True,
                        current_temp=temp_f,
                        target_temp=env.get_target_temperature(),
                        auto_control_enabled=controller.is_auto_control_enabled(),
                    )
                else:
                    output = ControlRealACOutput(
                        success=False, message="Failed to turn on Shelly plug"
                    )

            elif input_data.action == "turn_off":
                success = turn_off()
                if success:
                    env.set_ac_running(False)
                    _, _, temp_f, _, _ = env.read_sensor()

                    logger.info(f"AC manually turned OFF at {temp_f:.1f}°F")
                    output = ControlRealACOutput(
                        success=True,
                        message=f"AC turned OFF (manual control), current temp: {temp_f:.1f}°F",
                        ac_running=False,
                        current_temp=temp_f,
                        target_temp=env.get_target_temperature(),
                        auto_control_enabled=controller.is_auto_control_enabled(),
                    )
                else:
                    output = ControlRealACOutput(
                        success=False, message="Failed to turn off Shelly plug"
                    )

            elif input_data.action == "stop_auto":
                success, message = controller.stop_automatic_control()

                _, _, temp_f, _, _ = (
                    env.read_sensor()
                    if env.is_simulation_enabled()
                    else (False, None, None, None, None)
                )

                output = ControlRealACOutput(
                    success=success,
                    message=message,
                    ac_running=False,
                    current_temp=temp_f,
                    target_temp=None,
                    auto_control_enabled=False,
                )

            elif input_data.action == "status":
                if not env.is_simulation_enabled():
                    return ToolResponse.from_model(
                        ControlRealACOutput(
                            success=False, message="Simulation not enabled"
                        )
                    )

                _, _, temp_f, _, _ = env.read_sensor()
                ac_running = env.get_ac_running()
                target_temp = env.get_target_temperature()
                auto_enabled = controller.is_auto_control_enabled()

                plug_success, plug_on = get_ac_state()
                if plug_success and plug_on != ac_running:
                    logger.warning(
                        f"State mismatch: simulation={ac_running}, plug={plug_on}"
                    )

                status_msg = (
                    f"Current: {temp_f:.1f}°F, AC: {'ON' if ac_running else 'OFF'}"
                )
                if target_temp:
                    status_msg += f", Target: {target_temp:.1f}°F"
                if auto_enabled:
                    status_msg += " (auto control active)"

                output = ControlRealACOutput(
                    success=True,
                    message=status_msg,
                    ac_running=ac_running,
                    current_temp=temp_f,
                    target_temp=target_temp,
                    auto_control_enabled=auto_enabled,
                )

            else:
                output = ControlRealACOutput(
                    success=False, message=f"Unknown action: {input_data.action}"
                )

            logger.info(f"Result: {output.message}")
            return ToolResponse.from_model(output)

        except Exception as e:
            logger.error(f"AC control failed: {e}", exc_info=True)
            return ToolResponse.from_model(
                ControlRealACOutput(success=False, message=f"Failed: {str(e)}")
            )
