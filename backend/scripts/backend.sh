#!/bin/bash
set -euo pipefail
poetry run uvicorn main:app --host 0.0.0.0