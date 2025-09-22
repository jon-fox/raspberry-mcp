#!/bin/bash

set -e  # Exit on any error

# Check if PI_PASSWORD environment variable is set
if [ -z "$PI_PASSWORD" ]; then
    echo "Error: PI_PASSWORD environment variable not set"
    echo "Please set it with: export PI_PASSWORD='your_password'"
    exit 1
fi

echo "Starting deployment to Raspberry Pi..."

# Build Docker image for ARM64
echo "Building Docker image for ARM64..."
docker buildx build --platform linux/arm64 -t mcppi:pi --no-cache --load .

# Save and transfer image to Pi
echo "Transferring image to Raspberry Pi..."
docker save mcppi:pi | sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker load'

# Stop and remove existing container
echo "Stopping existing container..."
sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker rm -f mcppi || true'

# Run new container
echo "Starting new container..."
sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker run -d --name mcppi -p 8000:8000 --restart unless-stopped --network host --privileged mcppi:pi'

echo "Deployment complete!"