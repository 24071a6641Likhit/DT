#!/bin/bash

# Smart Energy Monitoring System - Startup Script
# This script starts the complete backend system with all services

set -e

echo "========================================"
echo "Smart Energy Monitoring System"
echo "Starting Backend Services..."
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "✗ Virtual environment not found. Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if database is setup
if [ ! -f "device_ids.txt" ]; then
    echo "✗ Database not initialized. Please run:"
    echo "  sudo bash setup_db.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✓ Virtual environment activated"

# Check PostgreSQL is running
if ! pg_isready -q; then
    echo "✗ PostgreSQL is not running. Please start it first:"
    echo "  sudo systemctl start postgresql"
    exit 1
fi

echo "✓ PostgreSQL is running"

# Check database exists
if ! psql -U postgres -lqt | cut -d \| -f 1 | grep -qw energy_monitoring; then
    echo "✗ Database 'energy_monitoring' not found. Please run:"
    echo "  sudo bash setup_db.sh"
    exit 1
fi

echo "✓ Database 'energy_monitoring' exists"

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Environment variables loaded"
else
    echo "⚠ .env file not found, using defaults"
fi

echo ""
echo "Starting services..."
echo ""
echo "Components:"
echo "  • Data Simulator (probabilistic appliance models)"
echo "  • Polling Service (5-second interval)"
echo "  • Storage Service (PostgreSQL async)"
echo "  • Analysis Service (unknown load, spike detection)"
echo "  • Alert Service (spike, overload, high consumption)"
echo "  • SSE Broadcaster (real-time updates)"
echo "  • Background Scheduler (hourly/daily summaries)"
echo "  • FastAPI Server (17 endpoints)"
echo ""
echo "Access points:"
echo "  • API: http://localhost:8000"
echo "  • Docs: http://localhost:8000/docs"
echo "  • SSE Stream: http://localhost:8000/api/stream/live"
echo "  • Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Start uvicorn with reload
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
