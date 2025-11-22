# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV PYTHONUNBUFFERED=1 UV_NO_SYNC_PROGRESS=1

RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY pipebot.py ./pipebot.py
COPY cogs ./cogs
COPY profile_pics ./profile_pics

USER appuser

ENTRYPOINT ["uv", "run", "python", "pipebot.py"]
