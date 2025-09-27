# Build for Raspberry Pi 4 (arm64) on WSL
# sudo systemctl enable pigpiod
# sudo systemctl start pigpiod
# docker buildx build --platform linux/arm64 -t mcppi:pi --load .
# docker save mcppi:pi | sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker load'
# sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker rm -f mcppi || true'
# sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'docker run -d --name mcppi -p 8000:8000 --restart unless-stopped --network host --privileged mcppi:pi'

# ssh in
# sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local

# shutdown Pi after finished
# sshpass -p "$PI_PASSWORD" ssh foxj7@mcppi.local 'sudo shutdown now'

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir uv

# ---- builder stage - use python:3.12 (not slim) for build tools ----
FROM python:3.12 AS builder
WORKDIR /app

# Install uv in the builder
RUN pip install --no-cache-dir uv

# layer cache for deps - copy dependency files first
COPY pyproject.toml uv.lock ./
# create venv & install deps (no dev), don't install project yet
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code LAST to prevent caching issues
COPY mcp_server/ ./mcp_server/
COPY README.md ./

# ---- final runtime (no compilers) ----
FROM base AS final
WORKDIR /app

# copy the prepared venv from builder
COPY --from=builder /app/.venv /app/.venv
# copy app code from builder (this will now include your latest changes)
COPY --from=builder /app/mcp_server /app/mcp_server
COPY --from=builder /app/README.md /app/README.md
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

EXPOSE 8000
CMD ["uv", "run", "-m", "mcp_server.server"]