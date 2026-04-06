# Get Started with Energy Monitoring System

## 🎯 You're All Set! Here's What You Have:

### ✅ Complete System (All 10 Modules)

**Backend (Python/FastAPI):**
- Database schema with migrations
- Energy simulator with time-of-day patterns
- Storage, analysis, alert, and billing services
- 17 API endpoints with SSE streaming
- 46+ tests (all passing)
- Background task scheduler

**Frontend (React/Vite):**
- Dashboard with live updates
- Alerts management page
- Billing analysis page
- Real-time SSE connection
- Responsive charts and cards

**Documentation:**
- IMPLEMENTATION_SPEC.md - Complete requirements
- TECHNICAL_DESIGN.md - Architecture details
- README.md - User guide
- DELIVERABLES.md - Complete inventory

---

## 🚀 First Time Setup (5 minutes)

### Option 1: Automated Setup (Recommended)

```bash
bash quick_start.sh
```

This script will:
1. Check PostgreSQL is running
2. Create databases
3. Set up Python virtual environment
4. Install all dependencies
5. Configure environment files
6. Optionally start the backend

### Option 2: Manual Setup

#### 1. Database Setup
```bash
cd backend
sudo bash setup_db.sh
```
This creates `energy_monitoring` and `energy_monitoring_test` databases.

#### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## 🏃 Running the System

### Start Backend (Terminal 1)
```bash
cd backend
bash start.sh
```

Backend will be available at: **http://localhost:8000**

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:5173**

### Access Points
- **Dashboard:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🧪 Verify Everything Works

### Run Complete System Test
```bash
bash test_complete_system.sh
```

This will:
- ✅ Check database exists
- ✅ Verify backend dependencies
- ✅ Run all backend tests
- ✅ Build frontend
- ✅ Test API endpoints (if running)
- ✅ Validate file structure

### Run Individual Module Tests

**Backend:**
```bash
cd backend
source venv/bin/activate
pytest -v                          # All tests
pytest tests/test_simulator.py -v  # Specific module
```

**Frontend:**
```bash
cd frontend
bash verify_module10.sh  # Build test
```

---

## 📊 What You'll See

### Dashboard Page
- 4 device cards (Main Meter, AC, Geyser, Pump)
- Real-time power and energy readings
- Unknown load indicator
- 30-minute rolling power chart
- Live connection status (updates every 5 seconds)

### Alerts Page
- List of all alerts (spike, overload, high consumption)
- Filter by type and acknowledgment status
- Acknowledge button for each alert
- Real-time alert notifications

### Billing Page
- Current month summary with slab breakdown
- 6-month historical comparison chart
- Current slab rates table
- Energy vs. cost visualization

---

## 🎮 How to Use

### Monitor Energy in Real-time
1. Open Dashboard
2. Watch device cards update every 5 seconds
3. Check the chart for power trends
4. Monitor unknown load (difference between main meter and sum of appliances)

### Handle Alerts
1. Navigate to Alerts page
2. View new alerts (spike, overload, high consumption)
3. Click "Acknowledge" to mark as handled
4. Filter by type or status

### Analyze Billing
1. Go to Billing page
2. View current month consumption and cost
3. See slab breakdown (which tariff slabs you're using)
4. Compare last 6 months in the chart

### Check API Directly
1. Open http://localhost:8000/docs
2. Try endpoints interactively
3. See request/response schemas
4. Test SSE stream endpoint

---

## 🔧 Configuration

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/energy_monitoring

# Simulator
SIMULATOR_POLL_INTERVAL=5       # Seconds
MAIN_METER_CAPACITY=8000        # Watts

# Alerts
SPIKE_THRESHOLD_MULTIPLIER=1.5
SPIKE_MIN_CONSECUTIVE_POLLS=2
OVERLOAD_WARNING_THRESHOLD=6400
OVERLOAD_CRITICAL_THRESHOLD=7200
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

### "Database does not exist"
```bash
cd backend
sudo bash setup_db.sh
```

### "Module not found" (Python)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Cannot find module" (Node)
```bash
cd frontend
npm install
```

### "Connection refused" on frontend
1. Check backend is running: `curl http://localhost:8000/health`
2. Check .env has correct URL: `cat frontend/.env`
3. Restart frontend: `npm run dev`

### SSE not connecting
1. Check browser console for errors
2. Verify SSE endpoint: `curl -N http://localhost:8000/api/stream/live`
3. Check CORS is enabled in backend

---

## 📚 Learn More

**Read the Documentation:**
- `README.md` - Complete user guide with all features
- `IMPLEMENTATION_SPEC.md` - Requirements and specifications
- `TECHNICAL_DESIGN.md` - Architecture and design decisions
- `DELIVERABLES.md` - Complete inventory of what's included

**Explore the Code:**
- `backend/app/services/orchestrator.py` - Main coordinator
- `backend/app/services/simulator.py` - Energy simulation logic
- `frontend/src/pages/Dashboard.jsx` - Main dashboard UI
- `backend/tests/` - Test suite (46+ tests)

**API Documentation:**
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

---

## ✨ Key Features

**Real-time Monitoring:**
- ⚡ Live readings every 5 seconds
- 📊 30-minute rolling power chart
- 🔌 Unknown load calculation
- 📡 SSE streaming (auto-reconnect)

**Intelligent Alerts:**
- 🚨 Spike detection (sustained 1.5x increase)
- ⚠️  Overload warnings (80% and 90% capacity)
- 📈 High consumption alerts (>20 kWh/hour)
- 🔕 Smart suppression (prevents spam)

**Billing & Analysis:**
- 💰 Monthly bill with slab breakdown
- 📅 6-month historical comparison
- ⚡ Hourly and daily summaries
- 🏷️ Maharashtra tariff slabs

**Data Simulation:**
- 🤖 Probabilistic state machines
- 🕐 Time-of-day patterns (AC peaks evening, Geyser peaks morning/evening)
- 📊 Realistic spike generation (5% probability)
- ⚡ Cumulative energy tracking

---

## 🎓 Production Deployment

For production deployment, see:
- `backend/start_production.sh` - Production server script
- `README.md` - Production checklist section

**Key considerations:**
- Set up reverse proxy (nginx)
- Enable HTTPS
- Add authentication
- Configure monitoring
- Set up automated backups
- Review security settings

---

## 📞 Need Help?

1. **Check logs:**
   - Backend: `backend/logs/` (when running)
   - Frontend: Browser console (F12)

2. **Run diagnostics:**
   ```bash
   bash test_complete_system.sh
   ```

3. **Review documentation:**
   - README.md for feature guide
   - TECHNICAL_DESIGN.md for architecture
   - API docs at /docs endpoint

4. **Verify setup:**
   ```bash
   cd backend && bash verify_module9.sh
   cd frontend && bash verify_module10.sh
   ```

---

**🎉 Happy Monitoring!**

Your complete energy monitoring system is ready to use.
Start with `bash quick_start.sh` and you'll be up in minutes!

