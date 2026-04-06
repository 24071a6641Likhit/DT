#!/bin/bash

# Verification script for Module 3: Storage Service
# This script tests the storage service implementation

set -e

echo "=== Module 3: Storage Service Verification ==="
echo ""

# Check if database exists
echo "Checking test database..."
python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    try:
        engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/energy_monitoring_test', echo=False)
        async with engine.connect():
            pass
        await engine.dispose()
        return True
    except Exception as e:
        print(f'✗ Test database not accessible: {e}')
        print('')
        print('Please run: sudo bash setup_db.sh')
        return False

result = asyncio.run(check())
exit(0 if result else 1)
"

echo "✓ Test database accessible"
echo ""

# Run tests
echo "Running storage service tests..."
source venv/bin/activate
pytest tests/test_storage.py -v

echo ""
echo "=== Module 3 Verification Complete ==="
echo ""
echo "All tests passed! Storage service is working correctly."
echo ""
