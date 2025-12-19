#!/usr/bin/env bash
exec /home/aya/Code/anytype-automation/.venv/bin/python \
  -m uvicorn main:app \
  --host 100.89.127.5 \
  --port 8001

