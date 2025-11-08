"""Utility for controlling Shelly smart plugs via HTTP."""

import socket
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ShellyPlug:
    ip: str
    name: Optional[str] = None
    
    @property
    def base_url(self) -> str:
        return f"http://{self.ip}"


def discover_plugs(timeout: int = 2) -> List[ShellyPlug]:
    """Discover Shelly plugs on the local network via mDNS/broadcast.
    
    Args:
        timeout: Discovery timeout in seconds
        
    Returns:
        List of discovered ShellyPlug instances
    """
    plugs = []
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        
        message = b'discover'
        sock.sendto(message, ('<broadcast>', 5353))
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                if _is_shelly(ip):
                    info = get_plug_info(ip)
                    name = info.get('name') if info else None
                    plugs.append(ShellyPlug(ip=ip, name=name))
            except socket.timeout:
                break
                
    except Exception as e:
        print(f"Discovery error: {e}")
    finally:
        sock.close()
    
    return plugs


def _is_shelly(ip: str) -> bool:
    """Check if IP is a Shelly device."""
    try:
        response = requests.get(f"http://{ip}/shelly", timeout=1)
        return response.status_code == 200
    except:
        return False


def get_plug_info(ip: str) -> Optional[Dict]:
    """Get plug device information."""
    try:
        response = requests.post(
            f"http://{ip}/rpc",
            json={"id": 1, "method": "Shelly.GetDeviceInfo"},
            timeout=2
        )
        if response.status_code == 200:
            return response.json().get("result", {})
    except:
        pass
    return None


def get_plug_status(ip: str, switch_id: int = 0) -> Optional[Dict]:
    """Get switch status."""
    try:
        response = requests.post(
            f"http://{ip}/rpc",
            json={"id": 1, "method": "Switch.GetStatus", "params": {"id": switch_id}},
            timeout=2
        )
        if response.status_code == 200:
            return response.json().get("result", {})
    except:
        pass
    return None


def toggle_plug(ip: str, switch_id: int = 0) -> bool:
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
            timeout=2
        )
        return response.status_code == 200
    except:
        return False


def set_plug(ip: str, on: bool, switch_id: int = 0, toggle_after: Optional[int] = None) -> bool:
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
            timeout=2
        )
        return response.status_code == 200
    except:
        return False


def turn_on(ip: str, switch_id: int = 0) -> bool:
    """Turn plug on."""
    return set_plug(ip, True, switch_id)


def turn_off(ip: str, switch_id: int = 0) -> bool:
    """Turn plug off."""
    return set_plug(ip, False, switch_id)


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Control Shelly smart plugs")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    subparsers.add_parser("discover", help="Discover plugs on network")
    
    status_parser = subparsers.add_parser("status", help="Get plug status")
    status_parser.add_argument("ip", help="Plug IP address")
    
    info_parser = subparsers.add_parser("info", help="Get plug info")
    info_parser.add_argument("ip", help="Plug IP address")
    
    toggle_parser = subparsers.add_parser("toggle", help="Toggle plug")
    toggle_parser.add_argument("ip", help="Plug IP address")
    
    on_parser = subparsers.add_parser("on", help="Turn plug on")
    on_parser.add_argument("ip", help="Plug IP address")
    
    off_parser = subparsers.add_parser("off", help="Turn plug off")
    off_parser.add_argument("ip", help="Plug IP address")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "discover":
        print("Discovering plugs...")
        plugs = discover_plugs(timeout=3)
        if plugs:
            print(f"\nFound {len(plugs)} plug(s):")
            for plug in plugs:
                print(f"  - {plug.ip} ({plug.name or 'Unknown'})")
        else:
            print("No plugs found")
    
    elif args.command == "status":
        status = get_plug_status(args.ip)
        if status:
            print(f"Status: {status}")
        else:
            print("Failed to get status")
    
    elif args.command == "info":
        info = get_plug_info(args.ip)
        if info:
            print(f"Info: {info}")
        else:
            print("Failed to get info")
    
    elif args.command == "toggle":
        if toggle_plug(args.ip):
            print("Toggled successfully")
        else:
            print("Failed to toggle")
    
    elif args.command == "on":
        if turn_on(args.ip):
            print("Turned on successfully")
        else:
            print("Failed to turn on")
    
    elif args.command == "off":
        if turn_off(args.ip):
            print("Turned off successfully")
        else:
            print("Failed to turn off")
