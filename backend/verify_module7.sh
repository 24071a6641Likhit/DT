#!/bin/bash

# Verification script for Module 7: FastAPI Routes
# This script verifies the API implementation

set -e

echo "=== Module 7: FastAPI Routes Verification ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Check FastAPI imports
echo "Checking FastAPI application..."
python3 << 'EOF'
from app.main import app

routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api')]
print(f'✓ FastAPI app initialized')
print(f'✓ {len(routes)} API endpoints registered')

# List all endpoints
print('\nEndpoints:')
for r in sorted(routes, key=lambda x: x.path):
    methods = ', '.join(sorted(r.methods)) if hasattr(r, 'methods') else 'GET'
    print(f'  {methods:10} {r.path}')
EOF

echo ""
echo "=== Module 7 Verification Complete ==="
echo ""
echo "API routes successfully created!"
echo ""
echo "To start the API server:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API will be available at:"
echo "  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Redoc: http://localhost:8000/redoc"
echo ""
