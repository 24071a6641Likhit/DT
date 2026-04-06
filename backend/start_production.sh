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

# FIX: Use --workers 1 to avoid duplicate orchestrator/polling/SSE issues
# With multiple workers:
# - Each worker runs its own orchestrator (duplicate polling/alerts)  
# - SSE broadcaster is in-memory per worker (clients see different data)
# - No shared state between workers
# For proper multi-worker, need to separate orchestrator into standalone process
# and use Redis pub/sub for SSE
echo "WARNING: Running with single worker to avoid state duplication."
echo "For true multi-worker, orchestrator must run as separate process."

# Start with production settings
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level warning \
    --no-access-log

