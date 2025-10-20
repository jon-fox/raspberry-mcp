#!/bin/bash

set -e  # Exit on any error

# Configuration - easily change these
IMAGE_NAME="mcppi"
IMAGE_TAG="v2"
CONTAINER_NAME="mcppi"

# Check if PI_PASSWORD environment variable is set
if [ -z "$PI_PASSWORD" ]; then
    echo "Error: PI_PASSWORD environment variable not set"
    echo "Please set it with: export PI_PASSWORD='your_password'"
    exit 1
fi

echo "Starting deployment to Raspberry Pi..."
echo "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Build Docker image for ARM64
echo "Building Docker image for ARM64..."
docker buildx build --platform linux/arm64 -t ${IMAGE_NAME}:${IMAGE_TAG} --no-cache --load .

# Save and transfer image to Pi
echo "Transferring image to Raspberry Pi..."
docker save ${IMAGE_NAME}:${IMAGE_TAG} | sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker load'

# Stop and remove existing container
echo "Stopping existing container..."
sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local "docker rm -f ${CONTAINER_NAME} || true"

# Stop pigpiod if running (conflicts with adafruit-circuitpython-dht)
echo "Stopping pigpiod daemon (not needed for DHT22)..."
sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local "sudo systemctl stop pigpiod || true"

# Run new container with GPIO access
echo "Starting new container with GPIO access..."
sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local "docker run -d --name ${CONTAINER_NAME} -p 8000:8000 --restart unless-stopped --network host --privileged --device /dev/gpiomem --device /dev/gpiochip0 ${IMAGE_NAME}:${IMAGE_TAG}"

echo "Deployment complete!"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Container: ${CONTAINER_NAME}"