#!/bin/bash

# Verification script for Module 6: Billing Service
# This script tests the billing service implementation

set -e

echo "=== Module 6: Billing Service Verification ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "Running billing service tests..."
pytest tests/test_billing.py -v

echo ""
echo "=== Module 6 Verification Complete ==="
echo ""
echo "All tests passed! Billing service is working correctly."
echo ""
echo "Features verified:"
echo "  ✓ Single slab cost calculation"
echo "  ✓ Multi-slab cost calculation (progressive rates)"
echo "  ✓ Unlimited slab handling (501+ units)"
echo "  ✓ Current month bill estimation"
echo "  ✓ Monthly comparison (last 6 months)"
echo "  ✓ Slab rate configuration (update/get)"
echo "  ✓ Edge cases (zero consumption, fractional kWh)"
echo ""
echo "Default Maharashtra slab rates:"
echo "  • 0-100 units: ₹3/kWh"
echo "  • 101-300 units: ₹7.5/kWh"
echo "  • 301-500 units: ₹12/kWh"
echo "  • 501+ units: ₹15/kWh"
echo ""
