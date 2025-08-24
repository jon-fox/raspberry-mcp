# raspberry-mcp
mcp on raspberry pi device

# uv init
pipx install uv # iso

uv python pin 3.12
uv sync --python 3.12 # if needed

uv init

# resolve local dns
raspberry pi
------------

sudo apt update && sudo apt install -y avahi-daemon
sudo systemctl status avahi-daemon   # should be active (running)
hostnamectl                          # shows Hostname: mcppi

wsl
------------

sudo apt update
sudo apt install -y libnss-mdns avahi-utils

# disable dns tunneling on wsl

notepad $env:UserProfile\.wslconfig

Paste in:
[wsl2]
dnsTunneling=false

# local login via wifi
ssh user@mcppi.local
