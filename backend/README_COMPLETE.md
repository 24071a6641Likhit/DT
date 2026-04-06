# Smart Energy Monitoring System - Backend

A real-time energy monitoring system for institutional buildings with smart metering, data analytics, and live dashboards.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Virtual environment support

### Installation

1. **Clone and setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Initialize database:**
```bash
sudo bash setup_db.sh
```

4. **Start the system:**
```bash
bash start.sh
```

The API will be available at `http://localhost:8000`

## System Components

### 🔌 Data Simulator
- Probabilistic state machines for 3 appliances (AC, Geyser, Pump)
- Time-of-day power consumption patterns
- Realistic spike generation (5% probability)
- Main meter aggregation

### 📊 Polling Service
- 5-second reading intervals
- Error handling with consecutive failure tracking
- Callback system for downstream processing

### 💾 Storage Service
- PostgreSQL async ORM (SQLAlchemy)
- Batch writing for efficiency
- 7-day raw data retention (configurable)
- 90-day summary retention

### 🔍 Analysis Service
- **Unknown Load**: Main meter - sum(smart plugs)
- **Spike Detection**: 1.5x baseline, sustained 2 polls
- **Energy Calculation**: Precise kWh from 5s readings
- **Peak Hour Analysis**: Hourly and daily statistics

### 🚨 Alert Service
- **Spike Alerts**: Sudden power surges (warning)
- **Overload Alerts**: >80% capacity warning, >90% critical
- **High Consumption**: >20 kWh/hour (info)
- Smart suppression to prevent alert spam

### 💰 Billing Service
- Maharashtra slab-based rates (configurable)
- Progressive cost calculation
- Monthly consumption tracking
- Historical comparisons

### 📡 SSE Broadcasting
- Real-time updates every 5 seconds
- Auto-reconnect support
- Multi-client support
- Event types: readings, alerts, device updates

### ⏰ Background Tasks
- Hourly summary generation (top of each hour)
- Daily summary generation (midnight + 5 min)
- Weekly data cleanup (Monday 2 AM)

## API Endpoints

### Dashboard
- `GET /api/dashboard/current` - Current readings + unknown load
- `GET /api/dashboard/recent?minutes=30` - Recent readings for graphs

### Devices
- `GET /api/devices` - List all devices
- `GET /api/devices/{id}` - Get device details
- `PATCH /api/devices/{id}` - Update device (name, enabled)

### Alerts
- `GET /api/alerts?severity=warning&acknowledged=false` - List alerts
- `GET /api/alerts/count` - Count by severity
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert

### Billing
- `GET /api/billing/current-month` - Current month bill estimate
- `GET /api/billing/monthly-comparison?months=6` - Historical comparison
- `GET /api/billing/rates` - Current slab rates
- `PUT /api/billing/rates` - Update rates (admin)

### Historical Data
- `GET /api/historical/daily?start_date=2024-01-01` - Daily summaries
- `GET /api/historical/hourly?device_id={id}&date=2024-01-15` - Hourly data
- `GET /api/historical/readings?device_id={id}&start=...&end=...` - Raw readings (max 1 hour)

### Real-time Stream
- `GET /api/stream/live` - SSE endpoint for live updates
- `GET /api/stream/health` - Stream health status

### System
- `GET /health` - System health check
- `GET /` - API info

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│                  (Lifespan Management)                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│ Orchestrator │        │  Background  │
│              │        │  Scheduler   │
└──────┬───────┘        └──────┬───────┘
       │                       │
       │ ┌─────────────────────┤
       │ │                     │
       ▼ ▼                     ▼
┌──────────────┐        ┌──────────────┐
│   Polling    │        │   Hourly/    │
│   Service    │        │    Daily     │
│   (5s)       │        │  Summaries   │
└──────┬───────┘        └──────────────┘
       │
       ├──► Storage ──► Analysis ──► Alerts
       │
       └──► SSE Broadcaster ──► Connected Clients
```

## Data Flow

1. **Simulator** generates realistic power readings
2. **Polling Service** collects readings every 5 seconds
3. **Orchestrator** coordinates processing:
   - Writes to **Storage**
   - Calculates **Unknown Load** via **Analysis**
   - Checks for **Alerts**
   - Broadcasts via **SSE** to clients
4. **Background Scheduler** generates summaries periodically
5. **API** serves data to frontend dashboard

## Testing

```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_simulator.py -v

# Run with coverage
pytest --cov=app tests/

# Verify modules individually
bash verify_module1.sh  # Database
bash verify_module2.sh  # Simulator
bash verify_module3.sh  # Storage
bash verify_module4.sh  # Analysis
bash verify_module5.sh  # Alerts
bash verify_module6.sh  # Billing
bash verify_module7.sh  # API Routes
bash verify_module8.sh  # SSE & Background
bash verify_module9.sh  # Integration
```

## Development

### Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/          # API endpoints
│   ├── config/
│   │   ├── database.py
│   │   └── settings.py
│   ├── models/              # SQLAlchemy models
│   ├── services/            # Business logic
│   │   ├── analysis_service.py
│   │   ├── alert_service.py
│   │   ├── billing_service.py
│   │   ├── storage_service.py
│   │   ├── polling_service.py
│   │   ├── orchestrator.py
│   │   ├── sse_broadcaster.py
│   │   └── background_tasks.py
│   ├── simulator/           # Data generation
│   └── main.py
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── requirements.txt
├── setup_db.sh             # Database initialization
├── start.sh                # Development startup
└── start_production.sh     # Production startup
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/energy_monitoring

# Application
DEBUG=True
LOG_LEVEL=INFO
TIMEZONE=Asia/Kolkata

# Feature Flags
ENABLE_SSE=True
ENABLE_BACKGROUND_TASKS=True
DATA_RETENTION_DAYS=7
```

### Adding New Features

1. **Models**: Add to `app/models/`
2. **Migration**: `alembic revision --autogenerate -m "description"`
3. **Service**: Add to `app/services/`
4. **API**: Add route to `app/api/routes/`
5. **Tests**: Add to `tests/`

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong database password
- [ ] Configure firewall (port 8000)
- [ ] Set up reverse proxy (nginx)
- [ ] Enable SSL/TLS
- [ ] Configure log rotation
- [ ] Set up monitoring (optional)
- [ ] Schedule database backups

### Docker (Optional)
```bash
# Build
docker build -t energy-monitor-backend .

# Run
docker run -p 8000:8000 --env-file .env energy-monitor-backend
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# View live logs (when using start.sh)
tail -f logs/app.log

# Check last 100 lines
tail -100 logs/app.log
```

### Database
```bash
# Connect to database
psql -U postgres -d energy_monitoring

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check reading count
SELECT COUNT(*) FROM readings;

# Check alerts
SELECT alert_type, COUNT(*) FROM alerts GROUP BY alert_type;
```

## Troubleshooting

### Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
psql -U postgres -lqt | grep energy_monitoring

# Recreate database
sudo bash setup_db.sh
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python3 --version  # Should be 3.11+
```

### SSE Not Working
- Check CORS settings in `app/main.py`
- Verify firewall allows port 8000
- Test with: `curl -N http://localhost:8000/api/stream/live`

### No Readings Generated
- Check orchestrator started: Look for "Orchestrator started" in logs
- Verify devices seeded: `SELECT COUNT(*) FROM devices;` (should be 4)
- Check polling service: `GET /health` should show `polling_active: true`

## Performance

- **Readings**: ~17,280 per day per device (5s interval)
- **Database Size**: ~2GB per month (with 7-day raw retention)
- **API Latency**: <50ms for current readings
- **SSE Clients**: Tested with 50+ concurrent connections
- **Memory**: ~200MB base + ~2MB per SSE client

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Verify setup: `bash verify_module9.sh`
3. Check database: `psql -U postgres -d energy_monitoring`
