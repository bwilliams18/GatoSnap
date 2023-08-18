#!/bin/bash
set -euo pipefail
poetry run uvicorn main:app --port "$PORT" --host 0.0.0.0