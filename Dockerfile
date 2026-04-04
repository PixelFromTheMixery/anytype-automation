# --- Stage 1: Build ---
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./ 
RUN uv sync --frozen --no-dev

# --- Stage 2: Runtime ---
FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src/ ./src/
COPY .env ./

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

ENV IP_ADDR=0.0.0.0
ENV IP_PORT=8000

# 3. Use the shell form of CMD to resolve the variables
CMD uvicorn main:create_app --factory --host $IP_ADDR --port $IP_PORT