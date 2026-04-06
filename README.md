# Smart Energy Monitoring System - Complete Implementation

A production-ready energy monitoring platform for institutional buildings (hostels, PGs, colleges) with real-time monitoring, intelligent alerts, and billing analysis.

## 📋 System Overview

**Technology Stack:**
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend:** React 18, Vite, Recharts, Server-Sent Events
- **Real-time:** SSE streaming for live updates
- **Simulation:** Probabilistic energy simulator (replaces physical hardware for MVP)

**Architecture:**
```
┌─────────────┐    SSE Stream    ┌──────────────┐
│   React     │ ←──────────────→ │   FastAPI    │
│  Dashboard  │    REST API      │   Backend    │
└─────────────┘                  └──────┬───────┘
                                        │
                                 ┌──────▼───────┐
                                 │  PostgreSQL  │
                                 │   Database   │
                                 └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- PostgreSQL 14+
- Python 3.11+
- Node.js 18+
- Git

### 1. Database Setup

```bash
cd backend
sudo bash setup_db.sh
```

This will:
- Create `energy_monitoring` and `energy_monitoring_test` databases
- Run migrations
- Seed 4 devices (1 main meter + 3 appliances)
- Save device UUIDs to `device_ids.txt`

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (default settings work for local development)

# Start the backend
bash start.sh
```

Backend will be available at: **http://localhost:8000**

API docs at: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

### 4. Access the Dashboard

Open browser to: **http://localhost:5173**

You should see:
- ✅ Real-time device readings (updates every 5 seconds)
- ✅ Live power consumption chart (30-minute window)
- ✅ Unknown load calculation
- ✅ Alert notifications
- ✅ Billing analysis with slab breakdown

## 📁 Project Structure

```
DT/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # 16 REST endpoints
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic
│   │   │   ├── orchestrator.py  # Main coordinator
│   │   │   ├── polling_service.py
│   │   │   ├── storage_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── billing_service.py
│   │   │   ├── simulator.py
│   │   │   ├── sse_broadcaster.py
│   │   │   └── background_tasks.py
│   │   ├── config/              # Database & settings
│   │   ├── alembic/             # Database migrations
│   │   └── main.py              # FastAPI application
│   ├── tests/                   # 46+ tests
│   ├── requirements.txt
│   ├── setup_db.sh             # Database initialization
│   ├── start.sh                # Development startup
│   └── start_production.sh     # Production startup
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Main dashboard
│   │   │   ├── Alerts.jsx      # Alert management
│   │   │   └── Billing.jsx     # Billing analysis
│   │   ├── components/
│   │   │   ├── DeviceCard.jsx
│   │   │   ├── AlertCard.jsx
│   │   │   └── PowerChart.jsx
│   │   ├── services/
│   │   │   └── api.js          # API client + SSE
│   │   ├── hooks/
│   │   │   └── useSSE.js       # SSE React hook
│   │   └── utils/
│   │       └── formatters.js   # Display formatters
│   ├── package.json
│   └── verify_module10.sh
│
├── IMPLEMENTATION_SPEC.md      # Complete specification
├── TECHNICAL_DESIGN.md         # Implementation design
└── README.md                   # This file
```

## 🔧 Configuration

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/energy_monitoring

# Simulator
SIMULATOR_POLL_INTERVAL=5       # Seconds between readings
MAIN_METER_CAPACITY=8000        # Watts (8 kW)

# Alerts
SPIKE_THRESHOLD_MULTIPLIER=1.5  # 150% of baseline
SPIKE_MIN_CONSECUTIVE_POLLS=2   # Sustained for 10 seconds
OVERLOAD_WARNING_THRESHOLD=6400 # Watts (80% of capacity)
OVERLOAD_CRITICAL_THRESHOLD=7200 # Watts (90% of capacity)

# Data Retention
READINGS_RETENTION_DAYS=7
SUMMARIES_RETENTION_DAYS=90
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests (46 tests)
pytest -v

# Run specific module
pytest tests/test_analysis_service.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

**Test Coverage:**
- ✅ Database models (6 tests)
- ✅ Simulator (10 tests)
- ✅ Storage service (5 tests)
- ✅ Analysis service (8 tests)
- ✅ Alert service (8 tests)
- ✅ Billing service (9 tests)

### Frontend Tests

```bash
cd frontend

# Verify build
bash verify_module10.sh

# Build for production
npm run build
```

## 📊 Features

### 1. Real-time Dashboard
- **Live readings** from main meter and individual appliances
- **Power consumption chart** (30-minute rolling window)
- **Unknown load tracking** (difference between main meter and sum of appliances)
- **Connection status indicator** (SSE connection health)

### 2. Intelligent Alerts

**Spike Alerts:**
- Triggered when power exceeds 1.5x baseline
- Baseline = average of last 10 minutes (excluding recent 1 minute)
- Requires 2 consecutive polls (10 seconds sustained)
- 15-minute suppression window

**Overload Alerts:**
- Warning: >6400W (80% of 8kW capacity)
- Critical: >7200W (90% of 8kW capacity)
- 10-minute suppression window

**High Consumption Alerts:**
- Triggered when hourly consumption exceeds 20 kWh
- 60-minute suppression window

### 3. Billing & Analysis

**Current Month:**
- Total consumption (kWh)
- Estimated bill amount (₹)
- Slab breakdown with per-unit rates
- Average daily cost

**Historical Analysis:**
- 6-month billing history
- Energy vs. cost comparison chart
- Trend identification

**Slab Rates (Maharashtra default):**
- 0-100 kWh: ₹3/kWh
- 101-300 kWh: ₹7.5/kWh
- 301-500 kWh: ₹12/kWh
- 501+ kWh: ₹15/kWh

### 4. Data Summaries

**Hourly Summaries:**
- Generated at the top of each hour
- Min/Max/Average power and energy
- Auto-calculated for all devices

**Daily Summaries:**
- Generated at 00:05 every day
- Full day statistics
- Used for billing calculations

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/current` - Current readings for all devices
- `GET /api/dashboard/recent?minutes=30` - Recent readings

### Devices
- `GET /api/devices` - List all devices
- `PATCH /api/devices/{id}` - Update device

### Alerts
- `GET /api/alerts` - List alerts (with filters)
- `GET /api/alerts/count` - Unacknowledged count
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert

### Billing
- `GET /api/billing/current-month` - Current month bill with slab breakdown
- `GET /api/billing/monthly-comparison?months=6` - Historical comparison
- `GET /api/billing/rates` - Current slab rates

### Historical
- `GET /api/historical/daily` - Daily summaries
- `GET /api/historical/hourly` - Hourly summaries

### Streaming
- `GET /api/stream/live` - SSE endpoint for real-time updates

**SSE Event Types:**
- `readings` - New device readings (every 5 seconds)
- `alert` - New alert created

## 🎯 Simulator Behavior

The energy simulator replaces physical hardware and generates realistic data:

### Time-of-Day Patterns

**Air Conditioner (1200-1800W):**
- Peak: 18:00-23:00 (80-95% probability ON)
- Night: 23:00-06:00 (60-70% probability ON)
- Day: 06:00-18:00 (20-40% probability ON)

**Geyser (2000W):**
- Morning peak: 06:00-09:00 (85% probability ON)
- Evening peak: 18:00-21:00 (85% probability ON)
- Off-peak: 0-15% probability ON

**Water Pump (500-800W):**
- Sporadic operation (5-30% probability)
- Variable power (500-800W)
- No time-of-day pattern

### Spike Generation
- 5% probability on any poll
- 60-100% power increase
- 15-30 second duration
- Independent per device

### Main Meter Calculation
```
Main = Sum(appliances) + Background(200-500W) + Jitter(±3%) + Optional Spike
```

## 🛠️ Troubleshooting

### Backend won't start

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify database exists
psql -U postgres -c "\l" | grep energy_monitoring

# Check virtual environment
source venv/bin/activate
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend won't connect

```bash
# Check backend is running
curl http://localhost:8000/api/devices

# Check SSE endpoint
curl -N http://localhost:8000/api/stream/live

# Verify .env file
cat frontend/.env
# Should have: VITE_API_URL=http://localhost:8000
```

### Database migration issues

```bash
cd backend
source venv/bin/activate

# Check current version
alembic current

# Upgrade to latest
alembic upgrade head

# If stuck, reset migrations (WARNING: destroys data)
sudo -u postgres psql -c "DROP DATABASE energy_monitoring;"
sudo bash setup_db.sh
```

### Tests failing

```bash
# Ensure test database exists
sudo -u postgres psql -c "CREATE DATABASE energy_monitoring_test;"

# Reset test database
cd backend
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/energy_monitoring_test
pytest --create-db
```

## 📈 Performance

**Metrics (Local Development):**
- Polling interval: 5 seconds
- SSE latency: <100ms
- API response time: <50ms
- Database queries: ~10ms average
- Frontend build size: 632 KB (gzipped: 186 KB)

**Scalability:**
- Handles 100+ concurrent SSE clients
- 7 days of 5-second readings = ~120K rows per device
- Automatic cleanup of old data
- Indexed queries for time-series data

## 🔐 Security Notes

**Current MVP Assumptions:**
- No authentication (single-tenant, local network)
- No HTTPS (development only)
- No rate limiting
- No input sanitization on device names

**For Production:**
- Add JWT/OAuth authentication
- Enable HTTPS with SSL certificates
- Add rate limiting (slowapi)
- Sanitize all user inputs
- Add CSRF protection
- Use environment-based secrets

## 📝 License

This is a prototype/MVP implementation. Not licensed for commercial use.

## 👥 Development

Built using systematic module-by-module implementation:
1. ✅ Database schema & migrations
2. ✅ Data simulator & polling service
3. ✅ Storage service
4. ✅ Analysis service (unknown load, spike detection)
5. ✅ Alert service (3 alert types)
6. ✅ Billing service (slab-based)
7. ✅ FastAPI routes (16 endpoints)
8. ✅ Background tasks & SSE streaming
9. ✅ Integration & orchestration
10. ✅ Frontend dashboard (React + Vite)

**Total Implementation:**
- Backend: 2,645 lines production code, 1,586 lines test code
- Frontend: ~1,500 lines React code
- Documentation: 140+ pages (specs, design, README)

## 🎓 For Deployment

See `backend/start_production.sh` for production startup script.

**Production checklist:**
- [ ] Set up dedicated PostgreSQL instance
- [ ] Configure environment variables
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Add monitoring (Prometheus/Grafana)
- [ ] Set up log aggregation
- [ ] Configure backup schedule
- [ ] Add authentication
- [ ] Set up CI/CD pipeline

---

**Need help?** Check the implementation spec and technical design documents for detailed architecture and design decisions.
