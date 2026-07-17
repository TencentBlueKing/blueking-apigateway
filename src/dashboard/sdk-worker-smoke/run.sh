#!/usr/bin/env bash
set -euo pipefail

cd /app
export PYTHONPATH=/app
python /app/sdk-worker-smoke/run.py
