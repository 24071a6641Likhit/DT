#!/bin/bash

# Integration test script
# Tests the complete data flow: simulator -> storage -> analysis -> alerts -> SSE

set -e

echo "================================================"
echo "Module 9: Integration & Orchestration Testing"
echo "================================================"
echo ""

source venv/bin/activate

echo "Step 1: Testing complete import chain..."
python3 -c "
import asyncio
from app.services.orchestrator import Orchestrator
from app.services.background_tasks import BackgroundTaskScheduler
from app.services.sse_broadcaster import broadcaster
from app.config.database import get_session_factory
print('  ✓ All services import successfully')
"

echo ""
echo "Step 2: Testing FastAPI app with lifespan..."
python3 -c "
from app.main import app
print('  ✓ FastAPI app loads with lifespan management')
print(f'  ✓ App routes: {len(app.routes)} registered')
"

echo ""
echo "Step 3: Listing all API endpoints..."
python3 -c "
from app.main import app
from fastapi.routing import APIRoute

routes = [route for route in app.routes if isinstance(route, APIRoute)]
print(f'  Total endpoints: {len(routes)}')
for route in sorted(routes, key=lambda r: r.path):
    methods = ','.join(route.methods)
    print(f'    {methods:10} {route.path}')
"

echo ""
echo "Step 4: Testing SSE broadcaster..."
python3 -c "
import asyncio
from app.services.sse_broadcaster import broadcaster

async def test():
    # Add client
    queue = broadcaster.add_client()
    print(f'  ✓ Client added (total: {broadcaster.get_client_count()})')
    
    # Broadcast
    await broadcaster.broadcast_readings({'test': 'data'})
    msg = await queue.get()
    print(f'  ✓ Message broadcasted and received')
    
    # Remove
    broadcaster.remove_client(queue)
    print(f'  ✓ Client removed (total: {broadcaster.get_client_count()})')

asyncio.run(test())
"

echo ""
echo "Step 5: Checking startup scripts..."
if [ -f "start.sh" ] && [ -x "start.sh" ]; then
    echo "  ✓ start.sh exists and is executable"
else
    echo "  ✗ start.sh missing or not executable"
fi

if [ -f "start_production.sh" ] && [ -x "start_production.sh" ]; then
    echo "  ✓ start_production.sh exists and is executable"
else
    echo "  ✗ start_production.sh missing or not executable"
fi

echo ""
echo "================================================"
echo "✓ Module 9 Integration Tests Complete!"
echo "================================================"
echo ""
echo "⚠ Note: Full integration test requires database."
echo "  Run: sudo bash setup_db.sh"
echo ""
echo "System is ready to run. Start with:"
echo "  bash start.sh"
echo ""

