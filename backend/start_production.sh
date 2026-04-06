#!/bin/bash

# Production startup script (no reload, optimized for deployment)

set -e

echo "Starting Smart Energy Monitoring System (Production Mode)..."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start with production settings
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level warning \
    --no-access-log
