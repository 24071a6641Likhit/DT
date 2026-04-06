#!/bin/bash

echo "========================================="
echo "Module 8: Background Tasks & SSE Stream"
echo "========================================="
echo ""

# Activate virtual environment
source venv/bin/activate

echo "✓ Checking new service files..."
echo ""

files=(
    "app/services/background_tasks.py"
    "app/services/sse_broadcaster.py"
    "app/services/orchestrator.py"
    "app/api/routes/stream.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "  ✓ $file ($lines lines)"
    else
        echo "  ✗ $file (missing)"
    fi
done

echo ""
echo "✓ Checking imports..."
python3 -c "
from app.services.background_tasks import BackgroundTaskScheduler
from app.services.sse_broadcaster import SSEBroadcaster, broadcaster
from app.services.orchestrator import Orchestrator
from app.api.routes.stream import router
print('  ✓ All imports successful')
"

echo ""
echo "✓ Checking test files..."
pytest tests/test_orchestrator.py tests/test_sse_broadcaster.py -v --tb=short 2>&1 | head -20

echo ""
echo "✓ Module 8 verification complete!"
echo ""
echo "Key components:"
echo "  • BackgroundTaskScheduler - Hourly/daily summary generation"
echo "  • SSEBroadcaster - Real-time event streaming to clients"
echo "  • Orchestrator - Main data flow coordinator"
echo "  • /api/stream/live - SSE endpoint"
echo ""
echo "Next: Run 'uvicorn app.main:app --reload' to start the system"
