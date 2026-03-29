FROM python:3.12-slim as builder

WORKDIR /tmp

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -e .

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY src/ ./src/
COPY config.yaml data.yaml .env ./

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

CMD ["uvicorn", "main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
