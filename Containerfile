# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV PYTHONUNBUFFERED=1 UV_NO_SYNC_PROGRESS=1

# Non-root user for defense in depth (rootless Podman remaps anyway)
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Copy dependency manifests first for layer caching
COPY pipebot/pyproject.toml pipebot/uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy source
COPY pipebot/pipebot.py ./pipebot.py
COPY pipebot/cogs ./cogs
COPY pipebot/profile_pics ./profile_pics

USER appuser

# Health-friendly: run through uv so the venv is activated
ENTRYPOINT ["uv", "run", "python", "pipebot.py"]
