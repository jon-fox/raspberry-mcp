#!/usr/bin/env python3
"""
Simple climate simulation test - agent reacts to temperature.

Workflow:
1. Enable simulation at 75°F (too hot)
2. Agent reads sensor, detects too hot
3. Agent calls ControlSimulatedAC to cool (cools by 2°F per call)
4. Agent reads sensor again, repeats until target reached
"""

import asyncio
from mcp_server.tools.simulation import SimulateClimate, ControlSimulatedAC
from mcp_server.tools.simulation.simulation_models import SimulateClimateInput
from mcp_server.tools.simulation.ac_models import ControlACInput
from mcp_server.tools.humidity_sensor import ReadHumiditySensor
from mcp_server.tools.humidity_sensor.humidity_models import ReadHumidityInput


async def main():
    print("=" * 60)
    print("Climate Control Simulation - Agent Reactive Demo")
    print("=" * 60)
    
    sim_tool = SimulateClimate()
    ac_tool = ControlSimulatedAC()
    sensor_tool = ReadHumiditySensor()
    
    target_temp = 65.0
    
    # 1. Enable simulation at hot temperature
    print(f"\n1. Starting simulation at 75°F (too hot!)")
    result = await sim_tool.execute(SimulateClimateInput(
        action="enable",
        temp_f=75.0
    ))
    print(f"   {result.output.message}")
    
    # 2. Agent monitoring loop
    print(f"\n2. Agent monitoring temperature (target: {target_temp}°F)\n")
    
    cycle = 0
    while True:
        cycle += 1
        
        # Agent reads sensor
        result = await sensor_tool.execute(ReadHumidityInput())
        current_temp = result.output.temperature_f
        
        print(f"   Cycle {cycle}:")
        print(f"   - Read sensor: {current_temp}°F")
        
        # Agent decides: too hot?
        if current_temp <= target_temp:
            print(f"   - Decision: Target reached! ✓")
            # Agent would turn off real AC here
            result = await ac_tool.execute(ControlACInput(action="turn_off"))
            print(f"   - {result.output.message}")
            break
        
        # Agent turns on AC to cool
        print(f"   - Decision: Too hot ({current_temp}°F > {target_temp}°F)")
        result = await ac_tool.execute(ControlACInput(
            action="turn_on",
            target_temp_f=target_temp
        ))
        print(f"   - {result.output.message}\n")
        
        await asyncio.sleep(1)  # Pause for readability
    
    print("\n" + "=" * 60)
    print("Simulation complete!")
    print("\nWhat happened:")
    print("- Agent read sensor and detected temp too high")
    print("- Agent called ControlSimulatedAC repeatedly to cool")
    print("- Each call cooled by 2°F (simulating AC effect)")
    print("- Agent stopped when target reached")
    print("\nIn production:")
    print("- Replace ControlSimulatedAC with SendIRCommand(device='ac')")
    print("- Real sensor readings change gradually over time")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
