#!/bin/bash

# Verification script for Module 4: Analysis Service
# This script tests the analysis service implementation

set -e

echo "=== Module 4: Analysis Service Verification ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "Running analysis service tests..."
pytest tests/test_analysis.py -v

echo ""
echo "=== Module 4 Verification Complete ==="
echo ""
echo "All tests passed! Analysis service is working correctly."
echo ""
echo "Features verified:"
echo "  ✓ Unknown load calculation (positive and negative)"
echo "  ✓ Spike detection with sustained threshold logic"
echo "  ✓ Hourly statistics aggregation"
echo "  ✓ Daily statistics from hourly summaries"
echo ""
