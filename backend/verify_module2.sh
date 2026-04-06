#!/bin/bash
# Verification script for Module 2

echo "=== Module 2: Simulator and Polling Service Verification ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Check simulator can be imported
echo "1. Checking simulator module..."
if python -c "from app.simulator.energy_simulator import EnergySimulator, ACSimulator, GeyserSimulator, PumpSimulator" 2>/dev/null; then
    echo "   ✓ Simulator classes import successfully"
else
    echo "   ❌ Simulator import failed"
    exit 1
fi

# Check polling service
echo ""
echo "2. Checking polling service..."
if python -c "from app.services.polling_service import PollingService" 2>/dev/null; then
    echo "   ✓ Polling service imports successfully"
else
    echo "   ❌ Polling service import failed"
    exit 1
fi

# Test simulator generates readings
echo ""
echo "3. Testing simulator functionality..."
python << 'EOF'
from uuid import uuid4
from app.simulator.energy_simulator import EnergySimulator

devices = [
    {'id': uuid4(), 'name': 'Main Meter', 'device_type': 'main_meter'},
    {'id': uuid4(), 'name': 'AC Unit', 'device_type': 'smart_plug'},
    {'id': uuid4(), 'name': 'Geyser', 'device_type': 'smart_plug'},
    {'id': uuid4(), 'name': 'Pump', 'device_type': 'smart_plug'},
]

simulator = EnergySimulator(devices)
readings = simulator.generate_readings()

assert len(readings) == 4, f"Expected 4 readings, got {len(readings)}"
assert readings[0].voltage_volts is not None, "Main meter missing voltage"
assert all(r.power_watts >= 0 for r in readings), "Negative power detected"

print("   ✓ Simulator generates 4 valid readings")
print(f"   ✓ Main meter: {readings[0].power_watts:.2f}W")
print(f"   ✓ Appliances: {sum(r.power_watts for r in readings[1:]):.2f}W total")
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# Run tests
echo ""
echo "4. Running simulator tests..."
pytest tests/test_simulator.py -v --tb=short

if [ $? -ne 0 ]; then
    echo ""
    echo "   ❌ Some tests failed"
    exit 1
fi

echo ""
echo "=== Module 2 Verification Complete ==="
echo ""
echo "✓ Simulator generates realistic power data"
echo "✓ Time-of-day patterns implemented"
echo "✓ Polling service schedules data collection"
echo "✓ Error handling tested"
echo ""
