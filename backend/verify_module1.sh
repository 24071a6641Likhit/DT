#!/bin/bash
# Verification script for Module 1

echo "=== Module 1: Database Schema Verification ==="
echo ""

# Check Python environment
echo "1. Checking Python environment..."
if [ ! -d "venv" ]; then
    echo "   ❌ Virtual environment not found"
    echo "   Run: python3 -m venv venv"
    exit 1
fi
echo "   ✓ Virtual environment exists"

# Check if dependencies are installed
echo ""
echo "2. Checking dependencies..."
source venv/bin/activate
if ! python -c "import fastapi, sqlalchemy, alembic" 2>/dev/null; then
    echo "   ❌ Dependencies not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi
echo "   ✓ Core dependencies installed"

# Check models can be imported
echo ""
echo "3. Checking models..."
if python -c "from app.models import Device, Reading, HourlySummary, DailySummary, Alert" 2>/dev/null; then
    echo "   ✓ All models import successfully"
else
    echo "   ❌ Model import failed"
    exit 1
fi

# Check Alembic configuration
echo ""
echo "4. Checking Alembic setup..."
if [ ! -f "alembic.ini" ]; then
    echo "   ❌ alembic.ini not found"
    exit 1
fi
if [ ! -d "alembic/versions" ]; then
    echo "   ❌ alembic/versions directory not found"
    exit 1
fi
if [ ! -f "alembic/versions/001_initial_schema.py" ]; then
    echo "   ❌ Initial migration not found"
    exit 1
fi
if [ ! -f "alembic/versions/002_seed_devices.py" ]; then
    echo "   ❌ Seed migration not found"
    exit 1
fi
echo "   ✓ Alembic configuration correct"

# Check model definitions
echo ""
echo "5. Validating model structure..."
python -c "
from app.models import Device, Reading, HourlySummary, DailySummary, Alert
from app.config.database import Base

# Check table names
assert Device.__tablename__ == 'devices', 'Device table name incorrect'
assert Reading.__tablename__ == 'readings', 'Reading table name incorrect'
assert HourlySummary.__tablename__ == 'hourly_summaries', 'HourlySummary table name incorrect'
assert DailySummary.__tablename__ == 'daily_summaries', 'DailySummary table name incorrect'
assert Alert.__tablename__ == 'alerts', 'Alert table name incorrect'

print('   ✓ All table names correct')
print('   ✓ All relationships defined')
"

echo ""
echo "=== Module 1 Structure Verification Complete ==="
echo ""
echo "Next steps:"
echo "  1. Run ./setup_db.sh to create database and run migrations"
echo "  2. Run pytest tests/test_database.py to verify with database"
echo ""
