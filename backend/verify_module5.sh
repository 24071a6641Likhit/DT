#!/bin/bash

# Verification script for Module 5: Alert Service
# This script tests the alert service implementation

set -e

echo "=== Module 5: Alert Service Verification ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "Running alert service tests..."
pytest tests/test_alert.py -v

echo ""
echo "=== Module 5 Verification Complete ==="
echo ""
echo "All tests passed! Alert service is working correctly."
echo ""
echo "Features verified:"
echo "  ✓ Spike alert creation with sustained detection"
echo "  ✓ Alert suppression (prevents duplicates within time window)"
echo "  ✓ Overload alert creation (warning and critical)"
echo "  ✓ High consumption hourly alerts"
echo "  ✓ Alert acknowledgment workflow"
echo "  ✓ Active alert retrieval and filtering"
echo "  ✓ Unacknowledged alert counting"
echo ""
