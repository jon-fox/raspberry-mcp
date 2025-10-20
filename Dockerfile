# =========================
# Build for Raspberry Pi 4 (arm64)
# =========================
# NOTE: DHT22 sensor uses adafruit-circuitpython-dht with libgpiod (Debian Trixie)
# Ensure pigpiod is stopped: sudo systemctl stop pigpiod
#
# Build and deploy:
# docker buildx build --platform linux/arm64 -t mcppi:pi --load .
# docker save mcppi:pi | sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker load'
# sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker rm -f mcppi || true'
# sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker run -d --name mcppi -p 8000:8000 --restart unless-stopped --network host --privileged --device /dev/gpiomem mcppi:pi'
#
# SSH in: sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local
# Shutdown Pi: sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'sudo shutdown now'

# =========================
# Base image
# =========================
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir uv

# =========================
# Builder stage (full Python + build tools)
# =========================
FROM python:3.12 AS builder
WORKDIR /app

# Install build tools, GPIO libs, and Python headers for C extensions
# Must install these BEFORE uv to ensure proper compilation environment
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libgpiod-dev \
 && rm -rf /var/lib/apt/lists/*

# Install uv in the builder
RUN pip install --no-cache-dir uv

# Verify build environment is properly configured
RUN gcc --version && ld --version && which gcc && python --version && uname -m

# Layer cache for deps - copy dependency files first
COPY pyproject.toml uv.lock ./

# Create venv & install deps (no dev), don't install project yet
# uv will automatically select correct wheels for the target platform (arm64)
RUN uv sync --frozen --no-dev --no-install-project

# Verify pydantic-core was installed correctly
RUN .venv/bin/python -c "import pydantic_core; print(f'pydantic_core version: {pydantic_core.__version__}')"

# Copy application code LAST to prevent caching issues
COPY mcp_server/ ./mcp_server/
COPY README.md ./

# =========================
# Final runtime stage (no build tools needed)
# =========================
FROM base AS final
WORKDIR /app

# Install runtime libgpiod3 (Debian Trixie) and create symlink for libgpiod2 compatibility
# Note: All C extensions (sysv_ipc, etc.) are precompiled in builder stage
RUN apt-get update && apt-get install -y \
    libgpiod3 \
 && ln -sf /usr/lib/aarch64-linux-gnu/libgpiod.so.3 /usr/lib/aarch64-linux-gnu/libgpiod.so.2 \
 && rm -rf /var/lib/apt/lists/*

# Copy the prepared venv from builder (with all compiled C extensions)
COPY --from=builder /app/.venv /app/.venv
# Copy app code from builder (includes latest changes)
COPY --from=builder /app/mcp_server /app/mcp_server
COPY --from=builder /app/README.md /app/README.md
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Force Blinka to use Raspberry Pi 4B GPIO backend
# Valid board IDs: https://github.com/adafruit/Adafruit_Blinka/blob/main/src/adafruit_blinka/board/__init__.py
ENV BLINKA_FORCEBOARD=RASPBERRY_PI_4B

# Add venv to PATH so we use the precompiled packages
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Use python directly from venv instead of uv run to avoid re-syncing
CMD ["python", "-m", "mcp_server.server"]