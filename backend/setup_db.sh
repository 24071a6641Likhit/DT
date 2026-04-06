#!/bin/bash
# Database setup script

set -e

echo "=== Smart Energy Monitoring System - Database Setup ==="
echo ""

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL:"
    echo "   sudo systemctl start postgresql"
    exit 1
fi

echo "✓ PostgreSQL is running"
echo ""

# Create database
echo "Creating database..."
sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS energy_monitoring;
CREATE DATABASE energy_monitoring;
GRANT ALL PRIVILEGES ON DATABASE energy_monitoring TO postgres;
EOF

echo "✓ Database created"
echo ""

# Create test database
echo "Creating test database..."
sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS energy_monitoring_test;
CREATE DATABASE energy_monitoring_test;
GRANT ALL PRIVILEGES ON DATABASE energy_monitoring_test TO postgres;
EOF

echo "✓ Test database created"
echo ""

# Run migrations
echo "Running Alembic migrations..."
cd "$(dirname "$0")"
source venv/bin/activate
alembic upgrade head

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Device IDs have been generated and saved to: device_ids.txt"
echo ""
echo "To verify, run:"
echo "  psql -U postgres -d energy_monitoring -c 'SELECT name, device_type FROM devices;'"
echo ""
