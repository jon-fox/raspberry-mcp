# Build for Raspberry Pi 4 (arm64) on WSL
# sudo systemctl enable pigpiod
# sudo systemctl start pigpiod
# docker buildx build --platform linux/arm64 -t mcppi:pi --load .
# docker save mcppi:pi | ssh foxj7@mcppi.local 'docker load'
# ssh foxj7@mcppi.local 'docker rm -f mcppi || true'
# ssh foxj7@mcppi.local 'docker run -d --name mcppi -p 8000:8000 --restart unless-stopped --network host --privileged mcppi:pi'
# ssh foxj7@mcppi.local 'sudo shutdown now'

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir uv

# ---- builder stage (has compilers) ----
FROM base AS builder
# Build deps for C extensions (RPi.GPIO) + crypto headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc python3-dev libffi-dev libssl-dev pkg-config \
 && rm -rf /var/lib/apt/lists/*

# layer cache for deps
COPY pyproject.toml uv.lock ./
# create venv & install deps (no dev), don't install project yet
RUN uv sync --frozen --no-dev --no-install-project

# copy app into builder so venv can resolve local package if needed later
COPY mcp_server/ ./mcp_server/
COPY README.md .

# ---- final runtime (no compilers) ----
FROM base AS final
WORKDIR /app

# copy the prepared venv from builder
COPY --from=builder /app/.venv /app/.venv
# copy app code
COPY --from=builder /app/mcp_server /app/mcp_server
COPY --from=builder /app/README.md /app/README.md

EXPOSE 8000
CMD ["uv", "run", "-m", "mcp_server.server"]
