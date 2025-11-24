import os
import requests
import socket
import time
from typing import Dict, Optional, List
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf


class ShellyDiscoveryListener(ServiceListener):
    def __init__(self):
        self.devices: List[Dict[str, str]] = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            if addresses:
                self.devices.append({"name": name, "ip": addresses[0]})

    def remove_service(self, _zc: Zeroconf, _type_: str, _name: str) -> None:
        pass

    def update_service(self, _zc: Zeroconf, _type_: str, _name: str) -> None:
        pass


def discover_shelly_devices(timeout: int = 3) -> List[Dict[str, str]]:
    zeroconf = Zeroconf()
    listener = ShellyDiscoveryListener()
    browser = ServiceBrowser(zeroconf, "_shelly._tcp.local.", listener)
    time.sleep(timeout)
    browser.cancel()
    zeroconf.close()
    return listener.devices


def get_default_plug_ip() -> str:
    env_ip = os.getenv("SMART_PLUG_IP")
    if env_ip:
        return env_ip

    try:
        devices = discover_shelly_devices()
        if devices:
            return devices[0]["ip"]
    except Exception:
        pass

    return "10.0.0.113"


# NOTE setting this globally for script
PLUG_IP = get_default_plug_ip()


def get_plug_info(ip: str = PLUG_IP) -> Optional[Dict]:
    """Get plug device information."""
    try:
        response = requests.post(
            f"http://{ip}/rpc",
            json={"id": 1, "method": "Shelly.GetDeviceInfo"},
            timeout=2,
        )
        if response.status_code == 200:
            return response.json().get("result", {})
    except Exception:
        pass
    return None


def get_plug_status(ip: str = PLUG_IP, switch_id: int = 0) -> Optional[Dict]:
    """Get switch status."""
    try:
        response = requests.post(
            f"http://{ip}/rpc",
            json={"id": 1, "method": "Switch.GetStatus", "params": {"id": switch_id}},
            timeout=2,
        )
        if response.status_code == 200:
            return response.json().get("result", {})
    except Exception:
        pass
    return None


def toggle_plug(ip: str = PLUG_IP, switch_id: int = 0) -> bool:
    """Toggle plug on/off.

    Args:
        ip: Device IP address
        switch_id: Switch component ID (default: 0)

    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"http://{ip}/rpc",
            json={"id": 1, "method": "Switch.Toggle", "params": {"id": switch_id}},
            timeout=2,
        )
        return response.status_code == 200
    except Exception:
        return False


def set_plug(
    ip: str = PLUG_IP,
    on: bool = True,
    switch_id: int = 0,
    toggle_after: Optional[int] = None,
) -> bool:
    """Set plug state.

    Args:
        ip: Device IP address
        on: True to turn on, False to turn off
        switch_id: Switch component ID (default: 0)
        toggle_after: Auto-toggle after N seconds (optional)

    Returns:
        True if successful
    """
    try:
        params = {"id": switch_id, "on": on}
        if toggle_after:
            params["toggle_after"] = toggle_after

        response = requests.post(
            f"http://{ip}/rpc",
            json={"id": 1, "method": "Switch.Set", "params": params},
            timeout=2,
        )
        return response.status_code == 200
    except Exception:
        return False


def turn_on(ip: str = PLUG_IP, switch_id: int = 0) -> bool:
    """Turn plug on."""
    return set_plug(ip, True, switch_id)


def turn_off(ip: str = PLUG_IP, switch_id: int = 0) -> bool:
    """Turn plug off."""
    return set_plug(ip, False, switch_id)


def get_ac_state(ip: str = PLUG_IP, switch_id: int = 0) -> tuple[bool, bool]:
    """Get AC (plug) state.

    Args:
        ip: Device IP address
        switch_id: Switch component ID (default: 0)

    Returns:
        Tuple of (success, is_on)
    """
    status = get_plug_status(ip, switch_id)
    if status and "output" in status:
        return True, status["output"]
    return False, False


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Control Shelly smart plug")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("status", help="Get plug status")
    subparsers.add_parser("info", help="Get plug info")
    subparsers.add_parser("toggle", help="Toggle plug")
    subparsers.add_parser("on", help="Turn plug on")
    subparsers.add_parser("off", help="Turn plug off")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "status":
        status = get_plug_status()
        if status:
            print(f"Status: {status}")
        else:
            print("Failed to get status")

    elif args.command == "info":
        info = get_plug_info()
        if info:
            print(f"Info: {info}")
        else:
            print("Failed to get info")

    elif args.command == "toggle":
        if toggle_plug():
            print("Toggled successfully")
        else:
            print("Failed to toggle")

    elif args.command == "on":
        if turn_on():
            print("Turned on successfully")
        else:
            print("Failed to turn on")

    elif args.command == "off":
        if turn_off():
            print("Turned off successfully")
        else:
            print("Failed to turn off")
