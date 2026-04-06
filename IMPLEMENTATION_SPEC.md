# Smart Energy Monitoring System - Implementation Specification v1.0

## Document Control
- **Version:** 1.0
- **Status:** Final
- **Target:** MVP Deployment (Single Building Pilot)
- **Last Updated:** 2026-04-05

---

## 1. Scope of the MVP

### 1.1 In-Scope Features

**Data Collection & Storage**
- Simulated data generation for 1 main building meter + 3 smart plug appliances (AC, Geyser, Water Pump)
- 5-second polling interval from simulator to database
- Raw reading storage with 7-day retention policy
- Hourly and daily aggregated summary generation

**Real-Time Monitoring**
- Live dashboard showing current total building power consumption
- Per-appliance current power draw display
- Unknown/background load calculation (difference between total and known loads)
- 30-minute rolling live graph with auto-updates via Server-Sent Events

**Analysis & Insights**
- Spike detection using configurable rolling average window and threshold
- Bill estimation using Maharashtra electricity slab rates (configurable)
- Daily and monthly consumption summaries
- Peak hour identification

**Alert System**
- Consumption spike alerts
- Alert log with manual acknowledgment
- Unacknowledged alert counter in UI

**Historical Analysis**
- Date range selector for historical data viewing
- Daily consumption trends over selected periods
- Day-of-week consumption comparisons
- Per-appliance consumption breakdown

**User Configuration**
- Device name and location label editing
- Spike detection threshold adjustment (percentage)
- Electricity slab rate configuration
- Polling interval configuration (requires backend restart)

### 1.2 Deployment Scope
- Single building deployment on local network
- Single administrator access (no multi-user authentication)
- Development: Native Python + React (no Docker during dev)
- Production: Docker Compose setup for final deployment

---

## 2. Non-Goals

### 2.1 Explicitly Excluded from MVP

**Hardware Integration**
- No real Tuya API integration
- No real Tapo P110 local API integration
- No WiFi network discovery or device pairing flows

**Multi-Tenancy**
- No user authentication or authorization
- No role-based access control (admin vs viewer)
- No multi-building support in single deployment

**Advanced Analytics**
- No machine learning predictions
- No anomaly detection beyond threshold-based spike detection
- No energy optimization recommendations
- No appliance scheduling or automation

**Notifications**
- No email alerts
- No SMS notifications
- No push notifications
- No webhook integrations

**Mobile Experience**
- No dedicated mobile app
- No PWA features
- Responsive web only (tablet and desktop)

**Export & Reporting**
- No PDF report generation
- No CSV/Excel export
- No scheduled reports

**Third-Party Integrations**
- No weather API correlation
- No occupancy sensor integration
- No calendar/scheduling system integration

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  - Live Dashboard  - Historical Analysis  - Settings        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTP REST + SSE Stream
                 │
┌────────────────▼────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11+)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Simulator  │  │ Analysis     │  │ Alert        │       │
│  │  Module     │  │ Engine       │  │ Engine       │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Polling    │  │ Storage      │  │ API          │       │
│  │  Engine     │  │ Module       │  │ Layer        │       │
│  │(APScheduler)│  │(SQLAlchemy)  │  │(FastAPI)     │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Async DB Queries
                 │
┌────────────────▼────────────────────────────────────────────┐
│              PostgreSQL Database                             │
│  - readings  - devices  - hourly_summaries                  │
│  - daily_summaries  - alerts                                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack (Strict Requirements)

**Backend**
- Python 3.11 or 3.12
- FastAPI 0.104+
- SQLAlchemy 2.0+ (async mode only)
- Alembic (for database migrations)
- APScheduler 3.10+
- asyncpg (PostgreSQL async driver)
- Pydantic v2 (for data validation)

**Database**
- PostgreSQL 15 or 16
- TimescaleDB extension NOT required (standard PostgreSQL only)

**Frontend**
- React 18+
- Vite 5+
- React Router v6
- Recharts 2.x (for graphs)
- Vanilla CSS only (no CSS frameworks, no Tailwind, no component libraries)
- Context API (state management)

**Development Tools**
- Docker and Docker Compose (for final deployment only)
- Python venv (for local development)
- Node.js 20+ / npm (for frontend development)

---

## 4. Module Boundaries and Responsibilities

### 4.1 Backend Module Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database engine and session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── device.py           # Device ORM model
│   │   ├── reading.py          # Reading ORM model
│   │   ├── summary.py          # Summary ORM models
│   │   └── alert.py            # Alert ORM model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── device.py           # Pydantic schemas for devices
│   │   ├── reading.py          # Pydantic schemas for readings
│   │   ├── summary.py          # Pydantic schemas for summaries
│   │   └── alert.py            # Pydantic schemas for alerts
│   ├── simulator/
│   │   ├── __init__.py
│   │   └── energy_simulator.py # Probabilistic appliance simulator
│   ├── services/
│   │   ├── __init__.py
│   │   ├── polling_service.py  # APScheduler polling logic
│   │   ├── storage_service.py  # Database write operations
│   │   ├── analysis_service.py # Unknown load, spike detection
│   │   ├── alert_service.py    # Alert generation logic
│   │   └── billing_service.py  # Bill calculation logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── devices.py      # Device CRUD endpoints
│   │   │   ├── readings.py     # Reading query endpoints
│   │   │   ├── summaries.py    # Summary query endpoints
│   │   │   ├── alerts.py       # Alert query and acknowledge
│   │   │   ├── billing.py      # Bill estimation endpoints
│   │   │   └── sse.py          # Server-Sent Events stream
│   │   └── dependencies.py     # FastAPI dependencies
│   └── jobs/
│       ├── __init__.py
│       ├── hourly_summary.py   # Hourly aggregation job
│       └── daily_summary.py    # Daily aggregation job
├── alembic/
│   ├── versions/
│   └── env.py
├── requirements.txt
└── Dockerfile
```

### 4.2 Module Responsibility Matrix

| Module | Primary Responsibility | Data Input | Data Output | External Dependencies |
|--------|------------------------|------------|-------------|----------------------|
| **Simulator** | Generate realistic appliance power data | System time, device config | Power readings (W), state (on/off) | Random number generator |
| **Polling Service** | Fetch data from simulator every 5s | Simulator output | Reading objects | APScheduler, Simulator |
| **Storage Service** | Write readings to PostgreSQL | Reading objects | Write confirmation/error | SQLAlchemy async session |
| **Analysis Service** | Compute unknown load, detect spikes | Recent readings from DB | Analysis results, spike flags | None |
| **Alert Service** | Generate and persist alerts | Spike flags, thresholds | Alert objects | Storage Service |
| **Billing Service** | Calculate cost estimates | Cumulative kWh, slab config | Bill amount (₹), slab breakdown | None |
| **API Layer** | Expose REST endpoints | HTTP requests | JSON responses | All services |
| **SSE Stream** | Push real-time updates to frontend | Latest readings + analysis | Event stream | Analysis Service |
| **Hourly Summary Job** | Aggregate 1-hour chunks | Last hour's readings | Hourly summary record | Storage Service |
| **Daily Summary Job** | Aggregate 24-hour chunks | Last day's readings | Daily summary record | Billing Service, Storage |

### 4.3 Frontend Component Structure

```
frontend/
├── src/
│   ├── App.jsx                 # Root component with router
│   ├── main.jsx                # React entry point
│   ├── styles/
│   │   ├── global.css          # CSS variables, reset, typography
│   │   └── components/         # Component-specific CSS modules
│   ├── context/
│   │   ├── SSEContext.jsx      # SSE connection state
│   │   └── SettingsContext.jsx # App-wide settings
│   ├── hooks/
│   │   ├── useSSE.js           # SSE connection hook
│   │   └── useAPI.js           # REST API hook
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx     # Navigation sidebar
│   │   │   └── TopBar.jsx      # Status bar with alerts
│   │   ├── dashboard/
│   │   │   ├── PowerCard.jsx   # Current power display
│   │   │   ├── LiveGraph.jsx   # Recharts real-time line chart
│   │   │   └── UnknownLoadCard.jsx
│   │   ├── historical/
│   │   │   ├── DateRangePicker.jsx
│   │   │   ├── DailyTrendChart.jsx
│   │   │   └── WeekdayComparison.jsx
│   │   ├── appliances/
│   │   │   ├── ApplianceCard.jsx
│   │   │   └── RuntimeChart.jsx
│   │   ├── alerts/
│   │   │   ├── AlertBanner.jsx
│   │   │   └── AlertLog.jsx
│   │   ├── billing/
│   │   │   ├── CurrentBillCard.jsx
│   │   │   ├── ProjectionChart.jsx
│   │   │   └── SlabBreakdown.jsx
│   │   └── settings/
│   │       ├── DeviceSettings.jsx
│   │       ├── ThresholdSettings.jsx
│   │       └── SlabRateEditor.jsx
│   └── pages/
│       ├── Dashboard.jsx
│       ├── Historical.jsx
│       ├── Appliances.jsx
│       ├── Alerts.jsx
│       ├── Billing.jsx
│       └── Settings.jsx
├── package.json
├── vite.config.js
└── Dockerfile
```

---

## 5. Data Flow from Hardware to Dashboard

### 5.1 Primary Data Pipeline (5-Second Cycle)

**Step 1: Simulation Trigger (every 5 seconds)**
- APScheduler fires scheduled job at 5-second intervals
- Current IST timestamp captured

**Step 2: Data Generation**
- Simulator queries current IST time
- For each device (main meter + 3 appliances):
  - Probabilistic state machine determines on/off state
  - If on, calculate power draw based on appliance profile + gaussian noise
  - If off, power = 0W
- Main meter sums all appliance powers + background load (200-500W random) + jitter (±3%)

**Step 3: Data Packaging**
- Polling service receives 4 readings:
  - `main_meter`: {power: float, voltage: float, current: float, timestamp: datetime}
  - `ac_plug`: {power: float, state: bool, timestamp: datetime}
  - `geyser_plug`: {power: float, state: bool, timestamp: datetime}
  - `pump_plug`: {power: float, state: bool, timestamp: datetime}

**Step 4: Database Write (Single Transaction)**
- Storage service opens async DB transaction
- Inserts 4 rows into `readings` table with device_id, timestamp (IST), power, voltage, current, energy_kwh (cumulative)
- Transaction commits or rolls back as atomic unit
- On write failure: Log error, skip this cycle (do not halt polling)

**Step 5: Analysis Trigger**
- Analysis service queries last 5 readings for each device
- Computes unknown load: `main_meter.power - sum(appliance_powers)`
- If unknown load < 0: Flag as measurement error, display as negative value
- Queries last 60 minutes of main meter readings (up to 720 readings)
- Computes rolling average of main meter power
- If current power > (average × spike_threshold), flag spike

**Step 6: Alert Generation**
- If spike detected:
  - Check last alert timestamp for type='spike'
  - If last spike was >2 polls ago (>10 seconds): Create new alert
  - If last spike was ≤2 polls ago AND current spike is within ±10% of previous: Skip (duplicate)
  - If last spike was ≤2 polls ago AND current spike differs by >10%: Create new alert
- Insert alert into `alerts` table with timestamp, device_id, type, severity, message

**Step 7: SSE Broadcast**
- SSE service packages:
  - Latest 4 device readings
  - Unknown load calculation
  - Current spike status
  - Unacknowledged alert count
- Broadcasts to all connected SSE clients
- Clients receive within ~100ms of data generation

**Step 8: Frontend Update**
- React SSE hook receives event
- Updates context state with new readings
- LiveGraph component appends new data point (keeps last 360 points = 30 minutes)
- PowerCard components re-render with new values
- If new alert: AlertBanner appears at top of dashboard

### 5.2 Aggregation Pipeline (Hourly)

**Trigger:** Cron job at :05 past each hour (e.g., 01:05, 02:05)

**Process:**
1. Query all readings from previous hour (e.g., 00:00:00 to 00:59:59) per device
2. Calculate:
   - `avg_power`: Average of all power readings
   - `max_power`: Maximum power reading
   - `min_power`: Minimum power reading
   - `total_kwh`: Sum of energy deltas
3. Insert into `hourly_summaries` table with `hour_timestamp` (start of hour)
4. Delete raw readings older than 7 days from current timestamp

### 5.3 Aggregation Pipeline (Daily)

**Trigger:** Cron job at 00:05 IST each day

**Process:**
1. Query all hourly summaries from previous day (00:00 to 23:59) per device
2. Calculate:
   - `total_kwh`: Sum of all hourly kWh
   - `avg_power`: Average of hourly averages
   - `peak_hour`: Hour with maximum avg_power
   - `estimated_cost`: Run billing calculation on total_kwh
3. Insert into `daily_summaries` table with `date` field
4. Query all alerts from previous day, count by type

---

## 6. Database Schema Requirements

### 6.1 Table: `devices`

**Purpose:** Store metadata for each hardware device (1 main meter + 3 smart plugs)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique device identifier |
| `name` | VARCHAR(100) | NOT NULL | Human-readable name (e.g., "Main Building Meter") |
| `device_type` | VARCHAR(20) | NOT NULL, CHECK IN ('main_meter', 'smart_plug') | Device category |
| `location` | VARCHAR(200) | NULLABLE | Location label (e.g., "Floor 2, Room 203 AC") |
| `ip_address` | VARCHAR(50) | NULLABLE | Simulator identifier (not used for real IP) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether device is currently polling |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `device_type` for filtering queries
- INDEX on `is_active` for active device queries

**Initial Seed Data (4 rows):**
```
id: <uuid1>, name: "Main Building Meter", device_type: "main_meter", location: "Distribution Panel", is_active: true
id: <uuid2>, name: "AC Unit", device_type: "smart_plug", location: "Floor 1, Common Room", is_active: true
id: <uuid3>, name: "Water Geyser", device_type: "smart_plug", location: "Floor 2, Bathroom Block", is_active: true
id: <uuid4>, name: "Water Pump", device_type: "smart_plug", location: "Ground Floor, Pump Room", is_active: true
```

### 6.2 Table: `readings`

**Purpose:** Store raw time-series data from all devices (high-volume, 7-day retention)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing reading ID |
| `device_id` | UUID | NOT NULL, FOREIGN KEY REFERENCES devices(id) | Device that generated reading |
| `timestamp` | TIMESTAMP | NOT NULL | Reading timestamp in IST |
| `power_watts` | NUMERIC(10, 2) | NOT NULL | Instantaneous power in watts |
| `voltage_volts` | NUMERIC(6, 2) | NULLABLE | Voltage (NULL for smart plugs) |
| `current_amps` | NUMERIC(8, 2) | NULLABLE | Current (NULL for smart plugs) |
| `energy_kwh` | NUMERIC(12, 3) | NOT NULL | Cumulative energy consumed in kWh |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Row insertion time |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `device_id` for device-specific queries
- INDEX on `timestamp DESC` for time-range queries (critical for performance)
- COMPOSITE INDEX on `(device_id, timestamp DESC)` for per-device time-series queries

**Data Volume Estimate:**
- 4 devices × 12 readings/minute × 60 minutes × 24 hours = 69,120 rows/day
- 7-day retention: ~484,000 rows maximum

**Cleanup Strategy:**
- Manual admin action via API endpoint `/admin/cleanup-old-readings`
- Deletes rows where `timestamp < NOW() - INTERVAL '7 days'`

### 6.3 Table: `hourly_summaries`

**Purpose:** Aggregated hourly statistics (retained indefinitely)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing summary ID |
| `device_id` | UUID | NOT NULL, FOREIGN KEY REFERENCES devices(id) | Device being summarized |
| `hour_timestamp` | TIMESTAMP | NOT NULL | Start of hour (e.g., 2026-04-05 14:00:00) |
| `avg_power_watts` | NUMERIC(10, 2) | NOT NULL | Average power over hour |
| `max_power_watts` | NUMERIC(10, 2) | NOT NULL | Peak power during hour |
| `min_power_watts` | NUMERIC(10, 2) | NOT NULL | Minimum power during hour |
| `total_kwh` | NUMERIC(10, 3) | NOT NULL | Total energy consumed during hour |
| `reading_count` | INTEGER | NOT NULL | Number of raw readings aggregated |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Aggregation time |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `(device_id, hour_timestamp)` to prevent duplicate aggregations
- INDEX on `hour_timestamp DESC` for time-series queries

**Data Volume Estimate:**
- 4 devices × 24 hours/day × 365 days = 35,040 rows/year

### 6.4 Table: `daily_summaries`

**Purpose:** Aggregated daily statistics with cost estimates (retained indefinitely)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing summary ID |
| `device_id` | UUID | NOT NULL, FOREIGN KEY REFERENCES devices(id) | Device being summarized |
| `date` | DATE | NOT NULL | Day being summarized (e.g., 2026-04-05) |
| `total_kwh` | NUMERIC(12, 3) | NOT NULL | Total energy consumed during day |
| `avg_power_watts` | NUMERIC(10, 2) | NOT NULL | Average power over day |
| `peak_hour` | INTEGER | NOT NULL, CHECK (peak_hour BETWEEN 0 AND 23) | Hour with highest consumption (0-23) |
| `estimated_cost_inr` | NUMERIC(10, 2) | NULLABLE | Estimated cost in rupees (main meter only) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Aggregation time |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `(device_id, date)` to prevent duplicate aggregations
- INDEX on `date DESC` for time-series queries

**Data Volume Estimate:**
- 4 devices × 365 days = 1,460 rows/year

### 6.5 Table: `alerts`

**Purpose:** Log of all system alerts with acknowledgment tracking

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing alert ID |
| `device_id` | UUID | NULLABLE, FOREIGN KEY REFERENCES devices(id) | Device that triggered alert (NULL for system alerts) |
| `timestamp` | TIMESTAMP | NOT NULL | When alert was triggered (IST) |
| `alert_type` | VARCHAR(50) | NOT NULL, CHECK IN ('spike', 'high_overnight', 'long_runtime', 'bill_threshold') | Alert category |
| `severity` | VARCHAR(20) | NOT NULL, CHECK IN ('info', 'warning', 'critical') | Alert severity level |
| `message` | TEXT | NOT NULL | Human-readable alert description |
| `threshold_value` | NUMERIC(10, 2) | NULLABLE | Threshold that was exceeded (if applicable) |
| `actual_value` | NUMERIC(10, 2) | NULLABLE | Actual value that triggered alert |
| `is_acknowledged` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether admin has acknowledged |
| `acknowledged_at` | TIMESTAMP | NULLABLE | When alert was acknowledged |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Row creation time |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `timestamp DESC` for chronological alert queries
- INDEX on `is_acknowledged` for filtering unacknowledged alerts
- COMPOSITE INDEX on `(alert_type, timestamp DESC)` for type-specific queries

**Alert Message Templates:**
- `spike`: "Power consumption spiked to {actual_value}W, {percentage}% above average of {threshold_value}W"
- `high_overnight`: "High consumption detected during off-peak hours (00:00-06:00): {actual_value}W"
- `long_runtime`: "{device_name} has been running continuously for {hours} hours"
- `bill_threshold`: "Projected monthly bill (₹{actual_value}) exceeds threshold of ₹{threshold_value}"

---

## 7. API Contract Requirements

### 7.1 Base URL and CORS Configuration

**Base URL:** `http://localhost:8000/api/v1`

**CORS Settings:**
- Allow Origins: `http://localhost:5173` (Vite dev server)
- Allow Methods: `GET, POST, PUT, PATCH, DELETE, OPTIONS`
- Allow Headers: `Content-Type, Accept`
- Allow Credentials: `false`

### 7.2 REST Endpoints

#### 7.2.1 Devices

**GET /devices**
- **Purpose:** List all devices
- **Query Parameters:** None
- **Response:** 200 OK
```json
{
  "devices": [
    {
      "id": "uuid-string",
      "name": "Main Building Meter",
      "device_type": "main_meter",
      "location": "Distribution Panel",
      "is_active": true,
      "created_at": "2026-04-05T10:00:00",
      "updated_at": "2026-04-05T10:00:00"
    }
  ]
}
```

**GET /devices/{device_id}**
- **Purpose:** Get single device details
- **Path Parameters:** `device_id` (UUID)
- **Response:** 200 OK (same schema as array item above)
- **Error:** 404 Not Found if device doesn't exist

**PATCH /devices/{device_id}**
- **Purpose:** Update device metadata
- **Path Parameters:** `device_id` (UUID)
- **Request Body:**
```json
{
  "name": "Updated Name",
  "location": "New Location"
}
```
- **Response:** 200 OK (updated device object)
- **Error:** 404 Not Found, 422 Validation Error

#### 7.2.2 Readings

**GET /readings/current**
- **Purpose:** Get latest reading for all active devices
- **Query Parameters:** None
- **Response:** 200 OK
```json
{
  "readings": [
    {
      "device_id": "uuid-string",
      "device_name": "Main Building Meter",
      "timestamp": "2026-04-05T13:45:20",
      "power_watts": 3456.78,
      "voltage_volts": 230.5,
      "current_amps": 15.2,
      "energy_kwh": 245.678
    }
  ],
  "unknown_load_watts": 823.45,
  "timestamp": "2026-04-05T13:45:20"
}
```

**GET /readings/historical**
- **Purpose:** Query historical readings for specific device and time range
- **Query Parameters:**
  - `device_id` (UUID, required)
  - `start_time` (ISO 8601 datetime, required)
  - `end_time` (ISO 8601 datetime, required)
  - `limit` (integer, optional, default=1000, max=10000)
- **Response:** 200 OK
```json
{
  "device_id": "uuid-string",
  "readings": [
    {
      "timestamp": "2026-04-05T13:45:20",
      "power_watts": 1234.56,
      "energy_kwh": 245.678
    }
  ],
  "count": 150
}
```
- **Error:** 400 Bad Request if date range > 7 days (raw data only kept 7 days)

#### 7.2.3 Summaries

**GET /summaries/hourly**
- **Purpose:** Get hourly aggregated data
- **Query Parameters:**
  - `device_id` (UUID, optional, if omitted returns all devices)
  - `start_date` (ISO 8601 date, required)
  - `end_date` (ISO 8601 date, required)
- **Response:** 200 OK
```json
{
  "summaries": [
    {
      "device_id": "uuid-string",
      "device_name": "Main Building Meter",
      "hour_timestamp": "2026-04-05T13:00:00",
      "avg_power_watts": 3200.50,
      "max_power_watts": 4500.00,
      "min_power_watts": 2100.00,
      "total_kwh": 3.2
    }
  ]
}
```

**GET /summaries/daily**
- **Purpose:** Get daily aggregated data
- **Query Parameters:** Same as hourly
- **Response:** 200 OK
```json
{
  "summaries": [
    {
      "device_id": "uuid-string",
      "device_name": "Main Building Meter",
      "date": "2026-04-05",
      "total_kwh": 68.5,
      "avg_power_watts": 2854.17,
      "peak_hour": 20,
      "estimated_cost_inr": 512.25
    }
  ]
}
```

#### 7.2.4 Alerts

**GET /alerts**
- **Purpose:** Get all alerts with optional filtering
- **Query Parameters:**
  - `is_acknowledged` (boolean, optional)
  - `alert_type` (string, optional)
  - `start_date` (ISO 8601 date, optional)
  - `end_date` (ISO 8601 date, optional)
  - `limit` (integer, optional, default=100, max=1000)
- **Response:** 200 OK
```json
{
  "alerts": [
    {
      "id": 123,
      "device_id": "uuid-string",
      "device_name": "Main Building Meter",
      "timestamp": "2026-04-05T13:45:20",
      "alert_type": "spike",
      "severity": "warning",
      "message": "Power consumption spiked to 5200W, 62% above average of 3200W",
      "threshold_value": 3200.0,
      "actual_value": 5200.0,
      "is_acknowledged": false,
      "acknowledged_at": null
    }
  ],
  "total_count": 45,
  "unacknowledged_count": 12
}
```

**PATCH /alerts/{alert_id}/acknowledge**
- **Purpose:** Mark alert as acknowledged
- **Path Parameters:** `alert_id` (integer)
- **Request Body:** None
- **Response:** 200 OK (updated alert object)
- **Error:** 404 Not Found

**GET /alerts/unacknowledged/count**
- **Purpose:** Get count of unacknowledged alerts (for badge)
- **Response:** 200 OK
```json
{
  "count": 12
}
```

#### 7.2.5 Billing

**GET /billing/current-month**
- **Purpose:** Get billing estimate for current month
- **Query Parameters:** None
- **Response:** 200 OK
```json
{
  "billing_period_start": "2026-04-01",
  "billing_period_end": "2026-04-30",
  "current_date": "2026-04-05",
  "days_elapsed": 5,
  "days_remaining": 25,
  "total_kwh": 342.5,
  "projected_monthly_kwh": 2055.0,
  "estimated_cost_inr": 2562.50,
  "projected_cost_inr": 15375.00,
  "slab_breakdown": [
    {"slab": "0-100 units", "units": 100, "rate": 3.0, "cost": 300.0},
    {"slab": "101-300 units", "units": 200, "rate": 7.5, "cost": 1500.0},
    {"slab": "301-500 units", "units": 42.5, "rate": 12.0, "cost": 510.0}
  ]
}
```

**GET /billing/monthly-comparison**
- **Purpose:** Get last 6 months comparison
- **Query Parameters:** None
- **Response:** 200 OK
```json
{
  "months": [
    {
      "month": "2026-03",
      "total_kwh": 1850.0,
      "total_cost_inr": 13875.0
    }
  ]
}
```

#### 7.2.6 Settings

**GET /settings**
- **Purpose:** Get all configurable settings
- **Response:** 200 OK
```json
{
  "polling_interval_seconds": 5,
  "spike_threshold_percentage": 50,
  "rolling_average_window_minutes": 60,
  "electricity_slabs": [
    {"min_units": 0, "max_units": 100, "rate_per_unit": 3.0},
    {"min_units": 101, "max_units": 300, "rate_per_unit": 7.5},
    {"min_units": 301, "max_units": 500, "rate_per_unit": 12.0},
    {"min_units": 501, "max_units": null, "rate_per_unit": 15.0}
  ],
  "data_retention_days": 7
}
```

**PUT /settings**
- **Purpose:** Update settings (requires backend restart for some changes)
- **Request Body:** (same schema as GET response)
- **Response:** 200 OK (updated settings object)
- **Side Effects:** Write to config file, does NOT restart backend automatically

#### 7.2.7 Admin Operations

**POST /admin/cleanup-old-readings**
- **Purpose:** Manually trigger cleanup of readings older than 7 days
- **Request Body:** None
- **Response:** 200 OK
```json
{
  "deleted_count": 12500,
  "cutoff_timestamp": "2026-03-29T13:45:20"
}
```

### 7.3 Server-Sent Events (SSE) Endpoint

**GET /stream/live-updates**
- **Purpose:** Real-time stream of latest readings and analysis
- **Protocol:** Server-Sent Events (text/event-stream)
- **Heartbeat:** Every 30 seconds (comment line to keep connection alive)
- **Event Format:**
```
event: reading
data: {"timestamp":"2026-04-05T13:45:20","devices":[{"device_id":"uuid","device_name":"Main","power_watts":3200.5}],"unknown_load_watts":800.0,"alerts":[]}

event: heartbeat
data: {"timestamp":"2026-04-05T13:45:50"}
```

**Event Types:**
- `reading`: New data cycle (every 5 seconds)
- `alert`: New alert generated
- `heartbeat`: Keep-alive ping (every 30 seconds)

**Client Reconnection:**
- If connection drops, client MUST reconnect with exponential backoff
- Initial retry: 1 second
- Max retry delay: 30 seconds
- Backoff multiplier: 2x

---

## 8. Real-Time Update Strategy

### 8.1 SSE Connection Lifecycle

**Frontend Connection Establishment:**
1. On Dashboard page mount, React hook initiates SSE connection to `/stream/live-updates`
2. EventSource object created with auto-retry enabled
3. Connection state stored in SSEContext: `connecting`, `connected`, `disconnected`, `error`

**Connection States:**
- `connecting`: Initial connection attempt in progress
- `connected`: Active connection, receiving events
- `disconnected`: Connection lost, attempting reconnect
- `error`: Permanent error, requires page refresh

**Frontend Reconnection Logic:**
```
Attempt 1: Wait 1 second
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
Attempt 4: Wait 8 seconds
Attempt 5+: Wait 30 seconds
```

**Backend Connection Management:**
- No authentication required (local network assumption)
- Maximum 10 concurrent SSE connections (configurable)
- If connection count exceeds limit, reject with 429 Too Many Requests
- On client disconnect, immediately clean up server-side event queue

### 8.2 Live Graph Update Behavior

**Data Retention in Frontend:**
- Live graph displays last 30 minutes of data
- At 5-second intervals, that's 360 data points maximum
- New data point appended to array
- If array length > 360, remove oldest point (shift)

**Graph Rendering:**
- Recharts LineChart with ResponsiveContainer
- X-axis: Time labels (HH:mm:ss format)
- Y-axis: Power in watts (auto-scale)
- Transition animation: 300ms ease-in-out
- No full re-render, only incremental data point addition

**Performance Requirement:**
- Graph update must complete within 100ms of receiving SSE event
- No visible lag or frame drops on 60Hz display

### 8.3 Alert Banner Behavior

**Alert Display Rules:**
- Only unacknowledged alerts shown on dashboard
- Maximum 3 alert banners visible simultaneously
- If >3 unacknowledged alerts, show "2 more alerts" link to Alerts page
- Alerts sorted by timestamp DESC (newest first)

**Alert Appearance:**
- Severity `info`: Blue background, info icon
- Severity `warning`: Amber background, warning icon
- Severity `critical`: Red background, alert icon

**Dismiss Action:**
- Click "Dismiss" button on alert banner
- Sends PATCH request to `/alerts/{id}/acknowledge`
- On success, banner fades out over 300ms
- Alert removed from unacknowledged count

---

## 9. Alert Logic Requirements

### 9.1 Spike Detection Algorithm

**Trigger Conditions:**
1. Current power reading from main meter
2. Rolling average calculated from last 60 minutes of readings
3. Configurable threshold percentage (default: 50%)

**Algorithm:**
```
rolling_avg = AVG(power_watts) FROM readings 
              WHERE device_id = main_meter_id 
              AND timestamp >= NOW() - INTERVAL '60 minutes'

threshold_power = rolling_avg * (1 + (spike_threshold_percentage / 100))

IF current_power > threshold_power THEN
  spike_detected = TRUE
  percentage_above = ((current_power - rolling_avg) / rolling_avg) * 100
END IF
```

**Alert Generation Rules:**
- Query last alert of type='spike' for main meter
- Calculate time difference: `delta = NOW() - last_alert.timestamp`
- If delta > 10 seconds (>2 polls):
  - Create new alert
- If delta ≤ 10 seconds:
  - Calculate power difference: `diff = abs(current_power - last_alert.actual_value) / last_alert.actual_value`
  - If diff > 0.10 (10% change):
    - Create new alert (significant change in spike magnitude)
  - Else:
    - Skip (duplicate spike, near constant)

**Alert Severity Mapping:**
- 50-75% above average: `warning`
- >75% above average: `critical`

**Alert Message:**
```
"Power consumption spiked to {current_power}W, {percentage_above}% above average of {rolling_avg}W"
```

### 9.2 Additional Alert Types (Future - Not Implemented in MVP)

**High Overnight Usage:**
- Trigger: Average power between 00:00-06:00 exceeds 50% of daytime average
- Not implemented in MVP

**Long Runtime:**
- Trigger: Smart plug continuously on for >6 hours
- Not implemented in MVP

**Bill Threshold:**
- Trigger: Projected monthly bill exceeds configurable limit
- Not implemented in MVP

---

## 10. Billing and Analysis Requirements

### 10.1 Maharashtra Electricity Slab Rates (2024 Domestic)

**Default Configuration:**
| Slab | Units (kWh) | Rate per Unit (₹) |
|------|-------------|-------------------|
| 1 | 0 - 100 | 3.00 |
| 2 | 101 - 300 | 7.50 |
| 3 | 301 - 500 | 12.00 |
| 4 | 501+ | 15.00 |

**Billing Calculation Algorithm:**
```python
def calculate_bill(total_kwh: float, slabs: list) -> dict:
    remaining_units = total_kwh
    total_cost = 0.0
    slab_breakdown = []
    
    for slab in slabs:
        if remaining_units <= 0:
            break
        
        slab_min = slab['min_units']
        slab_max = slab['max_units'] or float('inf')
        slab_rate = slab['rate_per_unit']
        
        slab_capacity = slab_max - slab_min
        units_in_slab = min(remaining_units, slab_capacity)
        
        slab_cost = units_in_slab * slab_rate
        total_cost += slab_cost
        remaining_units -= units_in_slab
        
        slab_breakdown.append({
            'slab': f"{slab_min}-{slab_max if slab_max != float('inf') else 'above'}",
            'units': units_in_slab,
            'rate': slab_rate,
            'cost': slab_cost
        })
    
    return {
        'total_cost': round(total_cost, 2),
        'slab_breakdown': slab_breakdown
    }
```

**Billing Period:**
- Calendar month (1st to last day of month)
- Current month calculation: Sum of all main meter daily kWh from 1st to current date
- Projection: `projected_monthly_kwh = (total_kwh / days_elapsed) * days_in_month`

**Configuration:**
- Slab rates editable via Settings page
- Changes persisted to config file
- No retroactive recalculation of historical bills

### 10.2 Unknown Load Calculation

**Formula:**
```
unknown_load_watts = main_meter.power_watts - SUM(smart_plug.power_watts for all active plugs)
```

**Edge Cases:**
1. **Negative Unknown Load:**
   - Cause: Timing skew between main meter poll and smart plug polls
   - Handling: Display negative value as-is, no flooring to zero
   - Indication: Likely measurement error or timing issue

2. **Zero Unknown Load:**
   - Interpretation: All building consumption accounted for by smart plugs
   - Valid state: Possible but unlikely in real deployment

3. **High Unknown Load (>1000W):**
   - Interpretation: Significant background loads (lights, fans, misc appliances)
   - Valid state: Expected in real buildings

### 10.3 Analysis Metrics

**Peak Hour Identification:**
- Per daily summary, find hour with maximum avg_power_watts
- Stored as integer 0-23 (24-hour format)

**Average Usage:**
- Hourly: Average of all 5-second readings within hour
- Daily: Average of all hourly averages within day

**Energy Calculation:**
- Raw readings store cumulative kWh (monotonically increasing)
- Hourly kWh: Latest reading in hour - earliest reading in hour
- Daily kWh: Sum of all hourly kWh

---

## 11. Deployment Assumptions

### 11.1 Development Environment

**Backend:**
- OS: Ubuntu 22.04 LTS (or compatible Linux)
- Python: 3.11 or 3.12 installed via system package manager
- Virtual environment: `python3 -m venv venv`
- PostgreSQL: Installed locally via `apt install postgresql postgresql-contrib`
- Database: Created manually via `createdb energy_monitoring`

**Frontend:**
- Node.js: 20.x LTS
- Package manager: npm (not yarn or pnpm)
- Dev server: Vite on port 5173

**Running Development:**
```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### 11.2 Production Environment (Docker Compose)

**Architecture:**
- 3 containers: PostgreSQL, Backend (FastAPI), Frontend (Nginx serving static build)
- Network: Shared Docker network, no host network mode
- Volumes: PostgreSQL data volume for persistence

**Container Details:**
- `postgres`: Official PostgreSQL 16 image, exposed port 5432 (internal only)
- `backend`: Custom Python image, exposed port 8000
- `frontend`: Custom Nginx image, exposed port 80

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: Frontend URL
- `POLLING_INTERVAL`: Default 5 seconds
- `TIMEZONE`: Asia/Kolkata

**Startup Order:**
1. PostgreSQL container starts
2. Backend waits for PostgreSQL health check (pg_isready)
3. Backend runs Alembic migrations automatically
4. Backend starts polling service
5. Frontend starts Nginx

### 11.3 Network Assumptions

**Local Network Only:**
- No public internet access required for core functionality
- All devices (backend, frontend clients) on same LAN
- No DNS required (access via IP address)

**Firewall:**
- Backend port 8000 open to LAN
- Frontend port 80/5173 open to LAN
- PostgreSQL port 5432 NOT exposed outside Docker network

**IP Addressing:**
- Static IP recommended for backend server
- Frontend accessed via `http://<backend-ip>` in production

---

## 12. Failure Handling and Fallback Behavior

### 12.1 Database Connection Failures

**Scenario:** PostgreSQL unreachable during backend startup

**Behavior:**
- Backend exits with error code 1
- Error logged: "Failed to connect to database at {url}"
- No retry logic (expect deployment system to restart)

**Scenario:** Database connection lost during operation

**Behavior:**
- Active transactions rolled back
- Polling service continues attempting to write readings
- Each write attempt uses new connection from pool
- Failed writes logged but do not halt polling
- SSE clients receive error event:
```json
{"event": "error", "data": {"message": "Database temporarily unavailable"}}
```

### 12.2 Simulator Failures

**Scenario:** Simulator raises exception during data generation

**Behavior:**
- Exception logged with full traceback
- Poller skips this cycle (no readings written)
- Next poll cycle attempts normally
- If simulator fails 10 consecutive times: Backend logs critical error, continues retrying

**Scenario:** Simulator returns invalid data (e.g., negative power)

**Behavior:**
- Validation layer rejects reading
- Error logged with invalid values
- Reading discarded, database not written
- Next poll cycle attempts normally

### 12.3 API Endpoint Failures

**Scenario:** Client requests historical data beyond 7-day retention

**Behavior:**
- Return 400 Bad Request
- Error message: "Requested date range exceeds available raw data. Use /summaries/hourly for data older than 7 days."

**Scenario:** Client requests non-existent device

**Behavior:**
- Return 404 Not Found
- Error message: "Device with ID {device_id} not found"

**Scenario:** Internal server error during request processing

**Behavior:**
- Return 500 Internal Server Error
- Error logged on backend with full traceback
- Generic error message to client: "An internal error occurred. Please try again."

### 12.4 SSE Connection Failures

**Scenario:** Client disconnects from SSE stream

**Backend Behavior:**
- Detect disconnect via broken pipe or timeout
- Clean up event queue for that client
- Log disconnect event

**Frontend Behavior:**
- EventSource automatically attempts reconnect
- If reconnect fails, custom logic applies exponential backoff
- Display "Connection Lost" banner after 3 failed reconnects
- Banner includes "Retry Now" button for manual reconnect

**Scenario:** SSE endpoint exceeds connection limit (10 clients)

**Behavior:**
- Return 429 Too Many Requests
- Error message: "Maximum concurrent connections reached"
- Client displays error: "Too many active dashboards. Close other tabs and retry."

### 12.5 Frontend Data Loading Failures

**Scenario:** REST API call times out (>30 seconds)

**Behavior:**
- Display error toast: "Request timed out. Please check your connection."
- Retry button appears
- Page state unchanged (shows last successful data)

**Scenario:** REST API returns 500 error

**Behavior:**
- Display error toast: "Server error occurred. Please try again later."
- Retry button appears
- Console logs full error response for debugging

**Scenario:** SSE stream delivers malformed JSON

**Behavior:**
- Log parsing error to console
- Discard malformed event
- Continue processing subsequent events
- If 5 consecutive malformed events: Display warning banner, suggest page refresh

---

## 13. Security and Access Assumptions

### 13.1 Authentication and Authorization

**Assumption:** Single-tenant, local network deployment with no authentication

**Implications:**
- No login page
- No user roles
- No password storage
- No session management
- Any device on local network can access full dashboard

**Risk Acknowledgment:**
- Unauthorized users on LAN can view all data
- Unauthorized users can acknowledge alerts
- Unauthorized users can modify device names and settings
- Acceptable for MVP in controlled environment (hostel/college LAN)

**Future Consideration (Post-MVP):**
- Add basic authentication (username/password)
- Implement admin vs viewer roles
- Add session tokens

### 13.2 Data Privacy

**Assumption:** No personally identifiable information (PII) collected

**Data Stored:**
- Device names and locations (non-sensitive)
- Power readings (non-sensitive)
- Alert logs (operational data)
- No user data, no occupancy data, no tracking

**Compliance:**
- GDPR not applicable (no personal data)
- No data export to third parties

### 13.3 Input Validation

**Backend:**
- All API inputs validated via Pydantic schemas
- SQL injection prevented by SQLAlchemy parameterized queries
- No raw SQL strings from user input

**Frontend:**
- Form inputs validated before submission
- XSS prevention via React's built-in escaping
- No `dangerouslySetInnerHTML` usage

### 13.4 Network Security

**Assumption:** Backend and database run on trusted local network

**Exposed Ports:**
- Backend: 8000 (HTTP, no HTTPS in MVP)
- Frontend: 5173 (dev) / 80 (prod)
- PostgreSQL: NOT exposed outside Docker network

**HTTPS:**
- Not required for MVP (local network only)
- If deploying over internet: HTTPS mandatory (post-MVP)

### 13.5 Configuration Security

**Sensitive Data:**
- Database connection string contains password
- Stored in environment variable, not in code
- Not committed to version control (.env in .gitignore)

**Config File Permissions:**
- Settings JSON file readable/writable by backend user only
- File permissions: 600 (owner read/write only)

---

## 14. Acceptance Criteria

### 14.1 Phase 1: Database Setup

**Criteria:**
- [ ] PostgreSQL database created and accessible
- [ ] Alembic configured with initial migration
- [ ] All 5 tables created via migration (devices, readings, hourly_summaries, daily_summaries, alerts)
- [ ] Indexes created as specified
- [ ] 4 seed devices inserted
- [ ] Manual query verification: `SELECT * FROM devices` returns 4 rows

### 14.2 Phase 2: Data Simulator

**Criteria:**
- [ ] Simulator generates readings for main meter + 3 appliances
- [ ] AC simulator: Probabilistic on/off state, realistic power curve
- [ ] Geyser simulator: Probabilistic on/off state, realistic power curve
- [ ] Pump simulator: Probabilistic on/off state, realistic power curve
- [ ] Main meter = sum(appliances) + background load (200-500W) + jitter (±3%)
- [ ] Weekday vs weekend behavior observable (higher consumption on weekends)
- [ ] Occasional spikes generated (>50% above average, ~5% of time)
- [ ] Manual verification: Run simulator for 5 minutes, inspect output values for realism

### 14.3 Phase 3: Polling Engine

**Criteria:**
- [ ] APScheduler configured and running
- [ ] Poller executes every 5 seconds
- [ ] Each poll generates 4 readings (1 main meter + 3 plugs)
- [ ] Readings written to database with IST timestamps
- [ ] Database contains readings after 1 minute of operation (minimum 48 rows: 4 devices × 12 polls)
- [ ] No polling failures logged
- [ ] Manual verification: Query database after 2 minutes, verify continuous data

### 14.4 Phase 4: Analysis Engine

**Criteria:**
- [ ] Unknown load calculation implemented
- [ ] Unknown load = main meter - sum(appliances)
- [ ] Negative unknown load values handled correctly (displayed as negative)
- [ ] Spike detection algorithm implemented
- [ ] Rolling average calculated from last 60 minutes
- [ ] Spike threshold configurable (default 50%)
- [ ] Alert created when spike detected
- [ ] Alert suppression logic working (duplicate spikes within 2 polls)
- [ ] Manual verification: Force spike by modifying simulator, verify alert generated

### 14.5 Phase 5: REST API

**Criteria:**
- [ ] All endpoints documented in section 7.2 implemented
- [ ] GET /devices returns 4 devices
- [ ] GET /readings/current returns latest readings + unknown load
- [ ] GET /summaries endpoints return aggregated data
- [ ] GET /alerts returns alert list
- [ ] PATCH /alerts/{id}/acknowledge updates alert status
- [ ] GET /billing/current-month returns bill estimate
- [ ] Settings endpoints functional
- [ ] CORS configured for frontend origin
- [ ] Manual verification: Test each endpoint with curl or Postman

### 14.6 Phase 6: SSE Endpoint

**Criteria:**
- [ ] SSE endpoint at /stream/live-updates implemented
- [ ] Events sent every 5 seconds with latest readings
- [ ] Event payload includes devices, unknown_load, alerts
- [ ] Heartbeat events sent every 30 seconds
- [ ] Multiple clients can connect simultaneously
- [ ] Client disconnect handled gracefully
- [ ] Manual verification: Connect with browser EventSource, observe events for 1 minute

### 14.7 Phase 7: Frontend Foundation

**Criteria:**
- [ ] React app initialized with Vite
- [ ] Global CSS with dark theme applied
- [ ] CSS variables defined for colors, spacing, typography
- [ ] Sidebar navigation with links to all pages
- [ ] Top bar with placeholder for alert count
- [ ] React Router configured with routes
- [ ] All page components created (Dashboard, Historical, Appliances, Alerts, Billing, Settings)
- [ ] Manual verification: Navigate between pages, verify routing works

### 14.8 Phase 8: Real-Time Components

**Criteria:**
- [ ] SSE hook implemented with auto-reconnect
- [ ] LiveGraph component displays 30-minute data
- [ ] Graph updates every 5 seconds via SSE
- [ ] PowerCard components show current device readings
- [ ] Unknown load card displayed on dashboard
- [ ] Alert banner appears when new alert received
- [ ] Unacknowledged alert count shown in top bar
- [ ] Manual verification: Watch dashboard for 2 minutes, verify live updates

### 14.9 Phase 9: Data Visualization Pages

**Criteria:**
- [ ] Historical Analysis page with date range picker
- [ ] Daily trend chart displays historical data
- [ ] Day-of-week comparison chart functional
- [ ] Appliance Breakdown page shows per-appliance stats
- [ ] Runtime hours displayed per appliance
- [ ] Alerts page shows full alert log
- [ ] Alert acknowledgment working from UI
- [ ] Bill Estimator page shows current month + projection
- [ ] Slab breakdown displayed
- [ ] Settings page allows editing device names, thresholds, slab rates
- [ ] Manual verification: Test each page with real data

### 14.10 Phase 10: Hourly & Daily Jobs

**Criteria:**
- [ ] Hourly summary job runs at :05 past each hour
- [ ] Hourly summaries created for all 4 devices
- [ ] Daily summary job runs at 00:05 IST
- [ ] Daily summaries include bill estimates
- [ ] Data cleanup endpoint functional
- [ ] Manual verification: Run system for 2 hours, verify hourly summaries exist

### 14.11 Phase 11: Containerization

**Criteria:**
- [ ] Backend Dockerfile created and builds successfully
- [ ] Frontend Dockerfile created and builds successfully
- [ ] docker-compose.yml includes all 3 services
- [ ] Containers start in correct order (postgres → backend → frontend)
- [ ] Backend connects to PostgreSQL container
- [ ] Frontend accessible from host browser
- [ ] Alembic migrations run automatically on backend startup
- [ ] Manual verification: `docker-compose up`, access dashboard at http://localhost

### 14.12 Final System Verification

**End-to-End Test Scenario:**
1. Start system (Docker Compose or native)
2. Wait 2 minutes for data accumulation
3. Open dashboard in browser
4. **Verify:**
   - [ ] Current total building power displayed and updating every 5 seconds
   - [ ] 3 appliance cards showing current power
   - [ ] Unknown load calculation displayed
   - [ ] Live graph showing last 30 minutes, smooth updates
   - [ ] At least 1 spike alert generated (if simulator produced spike)
   - [ ] Alert banner visible on dashboard
   - [ ] Unacknowledged alert count in top bar
5. Navigate to Historical Analysis page
6. **Verify:**
   - [ ] Date range picker functional
   - [ ] Daily trend chart displays data
7. Navigate to Billing page
8. **Verify:**
   - [ ] Current month kWh displayed
   - [ ] Projected bill calculated
   - [ ] Slab breakdown shown
9. Navigate to Settings page
10. **Verify:**
    - [ ] Device names editable
    - [ ] Spike threshold adjustable
    - [ ] Slab rates editable
11. Acknowledge an alert
12. **Verify:**
    - [ ] Alert disappears from dashboard
    - [ ] Unacknowledged count decreases
13. Disconnect network / stop backend
14. **Verify:**
    - [ ] Frontend shows "Connection Lost" banner
15. Reconnect / restart backend
16. **Verify:**
    - [ ] Frontend auto-reconnects
    - [ ] Live updates resume

**Performance Criteria:**
- [ ] SSE events received within 500ms of generation
- [ ] Graph updates within 100ms of receiving SSE event
- [ ] API response time <200ms for all endpoints (excluding historical queries)
- [ ] Historical query response time <1 second for 7-day range
- [ ] No memory leaks (backend memory stable over 1 hour)
- [ ] No browser console errors

**Data Accuracy Criteria:**
- [ ] Unknown load matches manual calculation: main_meter - sum(appliances) within ±5W tolerance
- [ ] Bill estimate matches manual slab calculation
- [ ] Spike alerts correlate with actual power spikes in data

---

## 15. Assumptions and Risks

### 15.1 Explicit Assumptions

**Technical Assumptions:**
1. Python 3.11+ available on deployment system
2. PostgreSQL 15+ installed and running
3. Local network has DHCP or static IP configuration
4. Backend server has minimum 2GB RAM, 10GB disk space
5. Frontend clients use modern browsers (Chrome 90+, Firefox 88+, Safari 14+)

**Data Assumptions:**
6. Polling every 5 seconds is sufficient granularity (no sub-second monitoring needed)
7. 7-day raw data retention is sufficient for operational needs
8. Hourly and daily summaries provide adequate historical analysis
9. Main meter always reports value >= sum of smart plugs (within timing tolerance)
10. IST timezone does not observe daylight saving time

**Business Assumptions:**
11. Single building deployment (no multi-site management)
12. Single administrator user (no concurrent user conflicts)
13. Electricity slab rates change infrequently (manual config acceptable)
14. Alerts do not require immediate notification (dashboard check sufficient)
15. No integration with billing system or payment processing

**Deployment Assumptions:**
16. Backend server runs 24/7 without scheduled downtime
17. Network is stable (no frequent WiFi disconnections)
18. No backup/disaster recovery required for MVP
19. No load balancing or high availability required
20. Local network is trusted (no hostile actors)

### 15.2 Known Risks

**Technical Risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Database fills disk (no auto-cleanup) | Medium | High | Manual cleanup endpoint, monitoring |
| SSE connection limit reached | Low | Medium | 10-connection limit, clear error message |
| Timing skew causes negative unknown load | High | Low | Display as-is, acceptable for demo |
| Simulator lacks realism | Medium | Medium | Iterative tuning based on feedback |
| Frontend graph performance degrades | Low | Medium | Fixed 360-point window |

**Operational Risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Admin changes settings incorrectly | Medium | Medium | Validation, clear labels, defaults |
| Network outage interrupts monitoring | Medium | High | No mitigation (accept data loss) |
| Backend crash loses recent readings | Low | Medium | No mitigation (accept 5-30s loss) |
| PostgreSQL corruption | Low | High | No mitigation (manual DB restore) |

**Data Quality Risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Simulator produces unrealistic patterns | Medium | Low | Probabilistic state machines, tuning |
| Spike alerts too frequent (alert fatigue) | Medium | Medium | Configurable threshold, suppression |
| Bill estimate inaccurate | Low | Low | Use real slab rates, clear "estimate" label |

---

## 16. Out-of-Scope Clarifications

**Hardware:**
- No real device communication (Tuya, Tapo)
- No device discovery or pairing
- No firmware updates
- No hardware failure detection

**Advanced Features:**
- No predictive analytics
- No occupancy correlation
- No weather integration
- No carbon footprint calculation
- No energy optimization suggestions
- No automated control (no smart plug on/off from dashboard)

**Multi-User:**
- No user authentication
- No role-based access
- No audit logs
- No concurrent editing conflicts

**Notifications:**
- No email/SMS alerts
- No push notifications
- No webhooks
- No third-party integrations

**Reporting:**
- No PDF export
- No scheduled reports
- No CSV download
- No custom report builder

**Deployment:**
- No Kubernetes
- No cloud hosting
- No CDN for frontend
- No automated backups

---

**END OF SPECIFICATION**
