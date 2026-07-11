#!/usr/bin/env bash
# Render startup script

set -o errexit

# Make sure we're in the correct directory
cd /opt/render/project/src

# Run uvicorn using Python module
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8002}
