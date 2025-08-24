# Build for Raspberry Pi 4 (arm64) on WSL
# docker buildx build --platform linux/arm64 -t mcppi:pi --load .

# Copy image to the Pi over SSH
# docker save mcppi:pi | ssh foxj7@mcppi.local 'docker load'

# Start container
# ssh foxj7@mcppi.local 'docker run -d --name mcppi -p 8000:8000 --restart=unless-stopped mcppi:pi'

# (Re)start container on the Pi
# ssh foxj7@mcppi.local 'docker rm -f mcppi || true'

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Install uv (works on arm64)
RUN pip install --no-cache-dir uv

# Only copy dep files first for better layer caching
COPY pyproject.toml uv.lock ./
# Create venv & install deps (no dev), don't install project yet
RUN uv sync --frozen --no-dev --no-install-project

# Now copy your app
COPY mcp_server/ ./mcp_server/
COPY README.md ./

EXPOSE 8000
# Run your server via uv (uses the synced venv at .venv)
CMD ["uv", "run", "-m", "mcp_server.app"]
