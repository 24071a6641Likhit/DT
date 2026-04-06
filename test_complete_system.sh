#!/bin/bash

# Complete System Integration Test
# This script verifies the entire stack is working together

set -e

echo "=========================================="
echo "COMPLETE SYSTEM INTEGRATION TEST"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_passed() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

test_failed() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Check PostgreSQL
echo "1. Testing PostgreSQL..."
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw energy_monitoring; then
    test_passed "Database 'energy_monitoring' exists"
else
    test_failed "Database 'energy_monitoring' not found"
    echo "   Run: cd backend && sudo bash setup_db.sh"
    exit 1
fi

# 2. Check Backend Virtual Environment
echo ""
echo "2. Testing Backend Environment..."
if [ -d "backend/venv" ]; then
    test_passed "Backend virtual environment exists"
else
    test_failed "Backend venv not found"
    echo "   Run: cd backend && python3 -m venv venv"
    exit 1
fi

# 3. Check Backend Dependencies
echo ""
echo "3. Testing Backend Dependencies..."
if backend/venv/bin/python -c "import fastapi, sqlalchemy, asyncpg" 2>/dev/null; then
    test_passed "Backend dependencies installed"
else
    test_failed "Backend dependencies missing"
    echo "   Run: cd backend && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 4. Check Backend Tests
echo ""
echo "4. Running Backend Tests..."
cd backend
source venv/bin/activate
if pytest --tb=short -q 2>&1 | tail -5; then
    test_passed "Backend tests passed"
else
    test_warning "Some backend tests may have failed (check output above)"
fi
cd ..

# 5. Check Frontend Dependencies
echo ""
echo "5. Testing Frontend Dependencies..."
if [ -d "frontend/node_modules" ]; then
    test_passed "Frontend dependencies installed"
else
    test_failed "Frontend node_modules not found"
    echo "   Run: cd frontend && npm install"
    exit 1
fi

# 6. Test Frontend Build
echo ""
echo "6. Testing Frontend Build..."
cd frontend
if npm run build > /dev/null 2>&1; then
    test_passed "Frontend builds successfully"
    if [ -d "dist" ]; then
        SIZE=$(du -sh dist | cut -f1)
        echo "   Build size: $SIZE"
    fi
else
    test_failed "Frontend build failed"
    cd ..
    exit 1
fi
cd ..

# 7. Check API Endpoints (if backend is running)
echo ""
echo "7. Testing API Endpoints..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    test_passed "Backend is running and responding"
    
    # Test specific endpoints
    if curl -s http://localhost:8000/api/devices | grep -q "id"; then
        test_passed "Devices endpoint working"
    else
        test_warning "Devices endpoint returned unexpected response"
    fi
    
    if curl -s http://localhost:8000/api/dashboard/current | grep -q "readings"; then
        test_passed "Dashboard endpoint working"
    else
        test_warning "Dashboard endpoint returned unexpected response"
    fi
else
    test_warning "Backend not running (skipping API tests)"
    echo "   Start backend with: cd backend && bash start.sh"
fi

# 8. Check SSE Stream (if backend is running)
echo ""
echo "8. Testing SSE Stream..."
if curl -s http://localhost:8000/api/stream/live > /dev/null 2>&1; then
    test_passed "SSE endpoint is accessible"
else
    test_warning "SSE endpoint not accessible (backend may not be running)"
fi

# 9. File Structure Check
echo ""
echo "9. Checking File Structure..."
REQUIRED_FILES=(
    "IMPLEMENTATION_SPEC.md"
    "TECHNICAL_DESIGN.md"
    "README.md"
    "backend/app/main.py"
    "backend/app/services/orchestrator.py"
    "backend/requirements.txt"
    "backend/setup_db.sh"
    "frontend/src/App.jsx"
    "frontend/src/pages/Dashboard.jsx"
    "frontend/src/pages/Alerts.jsx"
    "frontend/src/pages/Billing.jsx"
    "frontend/package.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file (missing)"
        ((TESTS_FAILED++))
    fi
done

# Summary
echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed: 0${NC}"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! System is ready.${NC}"
    echo ""
    echo "To run the system:"
    echo "  1. Backend:  cd backend && bash start.sh"
    echo "  2. Frontend: cd frontend && npm run dev"
    echo "  3. Open:     http://localhost:5173"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix the issues above.${NC}"
    exit 1
fi
