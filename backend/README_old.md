# Smart Energy Monitoring System - Backend

## Module 1: Database Schema and Migrations

### Setup Instructions

1. **Install PostgreSQL** (if not already installed):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

2. **Create database**:
```bash
sudo -u postgres psql
CREATE DATABASE energy_monitoring;
CREATE USER energy_user WITH PASSWORD 'energy_pass';
GRANT ALL PRIVILEGES ON DATABASE energy_monitoring TO energy_user;
\q
```

3. **Create Python virtual environment**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```

5. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your database credentials if different
```

6. **Run migrations**:
```bash
alembic upgrade head
```

### Verification

After running migrations, verify the database:

```bash
# Connect to database
psql -U postgres -d energy_monitoring

# Check tables
\dt

# Should see:
#  devices
#  readings
#  hourly_summaries
#  daily_summaries
#  alerts
#  alembic_version

# Check seed data
SELECT id, name, device_type FROM devices;

# Should see 4 devices:
#  Main Building Meter (main_meter)
#  AC Unit (smart_plug)
#  Water Geyser (smart_plug)
#  Water Pump (smart_plug)

\q
```

### Run Tests

```bash
# Create test database
sudo -u postgres psql
CREATE DATABASE energy_monitoring_test;
GRANT ALL PRIVILEGES ON DATABASE energy_monitoring_test TO energy_user;
\q

# Run tests
pytest tests/test_database.py -v
```

### Expected Output

```
tests/test_database.py::test_device_model PASSED
tests/test_database.py::test_reading_model PASSED
tests/test_database.py::test_hourly_summary_model PASSED
tests/test_database.py::test_daily_summary_model PASSED
tests/test_database.py::test_alert_model PASSED
tests/test_database.py::test_cascade_delete PASSED
```

### What Was Built

✅ Complete database schema with 5 tables
✅ SQLAlchemy async ORM models
✅ Alembic migration system
✅ Seed data for 4 devices
✅ Indexes for performance
✅ Foreign key relationships with cascade
✅ Check constraints for data integrity
✅ Comprehensive tests

### Device IDs

After running migrations, device UUIDs are saved to `device_ids.txt`. These will be used by the simulator in the next module.
