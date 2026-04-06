# Smart Energy Monitoring System - Technical Design Document v1.0

## Document Control
- **Version:** 1.0
- **Status:** Final for Implementation
- **Based On:** IMPLEMENTATION_SPEC.md v1.0
- **Last Updated:** 2026-04-05

---

## A. ARCHITECTURE DIAGRAM

### A.1 System Components (Text Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND (PORT 5173/80)                    │
│ ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│ │  Dashboard  │  │  Historical  │  │  Appliances  │  │   Billing    │ │
│ │    Page     │  │   Analysis   │  │  Breakdown   │  │  Estimator   │ │
│ └─────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│ ┌─────────────┐  ┌──────────────┐                                      │
│ │   Alerts    │  │   Settings   │                                      │
│ │    Page     │  │     Page     │                                      │
│ └─────────────┘  └──────────────┘                                      │
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────────┐│
│ │               SSEContext (EventSource to /stream/live-updates)      ││
│ └─────────────────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           │ HTTP REST API + SSE Stream
                           │
┌──────────────────────────▼──────────────────────────────────────────────┐
│                   FASTAPI BACKEND (PORT 8000)                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION LAYER (main.py)                    │  │
│  │  - CORS Middleware                                                │  │
│  │  - Exception Handlers                                             │  │
│  │  - Startup/Shutdown Events                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        API ROUTER LAYER                           │  │
│  │  /api/v1/devices/*  /api/v1/readings/*  /api/v1/summaries/*      │  │
│  │  /api/v1/alerts/*   /api/v1/billing/*   /api/v1/settings/*       │  │
│  │  /stream/live-updates  (SSE)                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │ Polling    │  │ Analysis   │  │   Alert    │  │  Billing   │       │
│  │ Service    │  │ Service    │  │  Service   │  │  Service   │       │
│  │            │  │            │  │            │  │            │       │
│  │ (APSched)  │  │            │  │            │  │            │       │
│  └─────┬──────┘  └──────▲─────┘  └──────▲─────┘  └──────▲─────┘       │
│        │                │                │                │             │
│        │         ┌──────┴────────────────┴────────────────┘             │
│        │         │                                                      │
│  ┌─────▼─────────▼──────────────────────────────────────────────────┐  │
│  │                      STORAGE SERVICE                              │  │
│  │  - write_reading()  - get_recent_readings()                      │  │
│  │  - create_alert()   - get_hourly_summaries()                     │  │
│  │  - update_device()  - create_daily_summary()                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────┐                                                        │
│  │  Simulator  │                                                        │
│  │   Module    │                                                        │
│  │             │                                                        │
│  │ - MainMeter │                                                        │
│  │ - ACPlug    │                                                        │
│  │ - GeyserPlug│                                                        │
│  │ - PumpPlug  │                                                        │
│  └─────────────┘                                                        │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              DATABASE ENGINE (SQLAlchemy Async)                  │   │
│  │  - AsyncEngine  - AsyncSession  - Connection Pool                │   │
│  └───────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           │ asyncpg (PostgreSQL async driver)
                           │
┌──────────────────────────▼──────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE (PORT 5432)                       │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   devices    │  │   readings   │  │hourly_summ.  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐                                    │
│  │daily_summ.   │  │   alerts     │                                    │
│  └──────────────┘  └──────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### A.2 Data Flow Architecture

```
POLLING CYCLE (Every 5 seconds):

[APScheduler Trigger]
         │
         ▼
[Simulator.generate_readings()]
         │ Returns: List[SimulatedReading]
         ▼
[PollingService.poll_and_store()]
         │
         ├─ For each device reading:
         │  └─ [StorageService.write_reading()]
         │           │
         │           ▼
         │     [PostgreSQL INSERT]
         │
         ▼
[AnalysisService.analyze_latest()]
         │
         ├─ [Calculate unknown load]
         │  └─ main_meter_power - sum(appliance_powers)
         │
         ├─ [Check for spike]
         │  └─ Query last 60 min readings
         │  └─ Calculate rolling average
         │  └─ Compare current vs threshold
         │
         └─ If spike detected:
            └─ [AlertService.create_spike_alert()]
                     │
                     ▼
               [StorageService.create_alert()]
                     │
                     ▼
               [PostgreSQL INSERT]

[SSE Broadcast Service] (Continuous)
         │
         ├─ Listens to: Latest readings queue
         ├─ Listens to: New alerts queue
         │
         └─ Every 5 seconds:
            └─ Package latest state
            └─ Broadcast to all connected clients


AGGREGATION FLOW (Hourly at :05):

[APScheduler Trigger - Hourly]
         │
         ▼
[HourlySummaryJob.run()]
         │
         ├─ For each device:
         │  └─ Query readings from last hour
         │  └─ Calculate: avg, max, min, total_kwh
         │  └─ [StorageService.create_hourly_summary()]
         │
         └─ [Cleanup old readings > 7 days]


AGGREGATION FLOW (Daily at 00:05):

[APScheduler Trigger - Daily]
         │
         ▼
[DailySummaryJob.run()]
         │
         └─ For each device:
            ├─ Query hourly summaries from yesterday
            ├─ Calculate: total_kwh, avg_power, peak_hour
            ├─ [BillingService.calculate_cost()] (main meter only)
            └─ [StorageService.create_daily_summary()]
```

---

## B. MODULE-BY-MODULE DESIGN

### B.1 Simulator Module (`app/simulator/energy_simulator.py`)

**Purpose:** Generate realistic power consumption data for 4 devices without real hardware.

**Class Structure:**

```python
@dataclass
class SimulatedReading:
    device_id: UUID
    timestamp: datetime
    power_watts: float
    voltage_volts: Optional[float] = None
    current_amps: Optional[float] = None
    state: Optional[bool] = None  # on/off for smart plugs

class ApplianceSimulator:
    """Base class for appliance simulation"""
    device_id: UUID
    device_name: str
    base_power_watts: float
    power_variance: float
    
    def should_be_on(self, current_time: datetime) -> bool:
        """Probabilistic state machine based on time of day"""
        pass
    
    def generate_power(self, is_on: bool) -> float:
        """Generate power reading with gaussian noise"""
        pass

class ACSimulator(ApplianceSimulator):
    """Air Conditioner - High power, peak usage 18:00-23:00"""
    base_power_watts: float = 1500.0
    power_variance: float = 150.0  # ±10%
    
    peak_hours: List[int] = [18, 19, 20, 21, 22, 23]
    off_peak_hours: List[int] = [0, 1, 2, 3, 4, 5]
    
    def should_be_on(self, current_time: datetime) -> bool:
        hour = current_time.hour
        day_type = "weekend" if current_time.weekday() >= 5 else "weekday"
        
        if hour in self.peak_hours:
            # 80% chance on during peak hours
            # 95% on weekends
            prob = 0.95 if day_type == "weekend" else 0.80
            return random.random() < prob
        elif hour in self.off_peak_hours:
            # 5% chance during night
            return random.random() < 0.05
        else:
            # 40% chance during day
            return random.random() < 0.40

class GeyserSimulator(ApplianceSimulator):
    """Water Geyser - Medium power, peak usage 06:00-09:00, 18:00-21:00"""
    base_power_watts: float = 2000.0
    power_variance: float = 100.0  # ±5%
    
    morning_peak: List[int] = [6, 7, 8, 9]
    evening_peak: List[int] = [18, 19, 20, 21]
    
    def should_be_on(self, current_time: datetime) -> bool:
        hour = current_time.hour
        
        if hour in self.morning_peak or hour in self.evening_peak:
            # 90% chance during peak bathing times
            return random.random() < 0.90
        else:
            # 10% chance rest of day
            return random.random() < 0.10

class PumpSimulator(ApplianceSimulator):
    """Water Pump - Medium power, sporadic usage throughout day"""
    base_power_watts: float = 750.0
    power_variance: float = 50.0  # ±7%
    
    def should_be_on(self, current_time: datetime) -> bool:
        hour = current_time.hour
        
        # Higher usage during morning (6-10) and evening (17-21)
        if hour in [6, 7, 8, 9, 10]:
            return random.random() < 0.50
        elif hour in [17, 18, 19, 20, 21]:
            return random.random() < 0.50
        elif hour in [0, 1, 2, 3, 4, 5]:
            # Rare night usage
            return random.random() < 0.05
        else:
            # Moderate daytime usage
            return random.random() < 0.25

class MainMeterSimulator:
    """Main building meter - sum of all appliances + background load"""
    base_background_watts: float = 350.0  # Lights, fans, misc
    background_variance: float = 150.0  # Background varies 200-500W
    
    def generate_reading(
        self, 
        appliance_readings: List[SimulatedReading],
        current_time: datetime
    ) -> SimulatedReading:
        # Sum all appliance power
        total_appliance_power = sum(r.power_watts for r in appliance_readings)
        
        # Add background load (varies by time of day)
        background = self._calculate_background(current_time)
        
        # Total power
        total_power = total_appliance_power + background
        
        # Add measurement jitter (±3%)
        jitter = random.gauss(0, total_power * 0.015)  # std dev = 1.5%
        final_power = max(0, total_power + jitter)
        
        # Calculate voltage and current
        voltage = random.gauss(230.0, 2.0)  # 230V ±2V
        current = final_power / voltage if voltage > 0 else 0
        
        return SimulatedReading(
            device_id=self.device_id,
            timestamp=current_time,
            power_watts=round(final_power, 2),
            voltage_volts=round(voltage, 2),
            current_amps=round(current, 2),
            state=None
        )
    
    def _calculate_background(self, current_time: datetime) -> float:
        hour = current_time.hour
        
        # Higher background during evening (lights on)
        if hour in [18, 19, 20, 21, 22, 23]:
            base = 500.0
        elif hour in [6, 7, 8, 9]:
            base = 400.0
        elif hour in [0, 1, 2, 3, 4, 5]:
            base = 200.0  # Minimal night usage
        else:
            base = 350.0
        
        # Add random variance
        variance = random.gauss(0, 50)
        return max(150, base + variance)

class EnergySimulator:
    """Main simulator coordinating all devices"""
    
    def __init__(self, device_configs: List[dict]):
        self.ac = ACSimulator(device_configs[0])
        self.geyser = GeyserSimulator(device_configs[1])
        self.pump = PumpSimulator(device_configs[2])
        self.main_meter = MainMeterSimulator(device_configs[3])
        
        # Track cumulative energy for each device
        self.cumulative_energy: Dict[UUID, float] = {}
    
    def generate_readings(self) -> List[SimulatedReading]:
        """Generate one reading per device for current moment"""
        current_time = datetime.now(ZoneInfo("Asia/Kolkata"))
        
        # Generate appliance readings
        ac_reading = self.ac.generate_reading(current_time)
        geyser_reading = self.geyser.generate_reading(current_time)
        pump_reading = self.pump.generate_reading(current_time)
        
        # Generate main meter reading (depends on appliances)
        main_reading = self.main_meter.generate_reading(
            [ac_reading, geyser_reading, pump_reading],
            current_time
        )
        
        # Update cumulative energy (kWh)
        # Assuming 5-second intervals: kWh = watts * (5/3600)
        for reading in [ac_reading, geyser_reading, pump_reading, main_reading]:
            if reading.device_id not in self.cumulative_energy:
                self.cumulative_energy[reading.device_id] = 0.0
            
            kwh_increment = reading.power_watts * (5 / 3600)
            self.cumulative_energy[reading.device_id] += kwh_increment
        
        return [main_reading, ac_reading, geyser_reading, pump_reading]
```

**Initialization:**
- On backend startup, load device IDs from database
- Initialize simulator with actual device UUIDs
- Start with cumulative energy = 0 (or load last known values from DB)

**Spike Generation:**
- 5% of the time, randomly spike main meter reading by 60-100% for 15-30 seconds
- Implemented as temporary state in MainMeterSimulator

---

### B.2 Polling Service (`app/services/polling_service.py`)

**Purpose:** Schedule and execute data collection from simulator every 5 seconds.

**Class Structure:**

```python
class PollingService:
    def __init__(
        self,
        simulator: EnergySimulator,
        storage_service: StorageService,
        analysis_service: AnalysisService
    ):
        self.simulator = simulator
        self.storage = storage_service
        self.analysis = analysis_service
        self.scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start polling job"""
        # Add job: run every 5 seconds
        self.scheduler.add_job(
            self.poll_and_store,
            trigger='interval',
            seconds=5,
            id='main_poller',
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        self.scheduler.start()
        self.logger.info("Polling service started (5s interval)")
    
    async def stop(self):
        """Stop polling job"""
        self.scheduler.shutdown(wait=True)
        self.logger.info("Polling service stopped")
    
    async def poll_and_store(self):
        """Single poll cycle - called every 5 seconds"""
        try:
            # Step 1: Generate readings
            readings = self.simulator.generate_readings()
            self.logger.debug(f"Generated {len(readings)} readings")
            
            # Step 2: Store readings in database (batch insert)
            await self.storage.write_readings_batch(readings)
            self.logger.debug("Readings stored successfully")
            
            # Step 3: Trigger analysis
            await self.analysis.analyze_latest(readings)
            
        except Exception as e:
            self.logger.error(f"Poll cycle failed: {e}", exc_info=True)
            # Do not re-raise - continue polling on next cycle
```

**Error Handling:**
- If simulator raises exception: Log error, skip this cycle, continue polling
- If database write fails: Log error, skip this cycle, continue polling
- If analysis fails: Log error but data is already stored, continue polling
- Never halt polling due to transient errors

**Concurrency:**
- `max_instances=1` ensures only one poll runs at a time
- If previous poll takes >5s, next poll waits

---

### B.3 Storage Service (`app/services/storage_service.py`)

**Purpose:** Abstract all database write/read operations.

**Class Structure:**

```python
class StorageService:
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
        self.logger = logging.getLogger(__name__)
    
    async def write_readings_batch(
        self, 
        readings: List[SimulatedReading]
    ) -> None:
        """Write multiple readings in single transaction"""
        async with self.session_factory() as session:
            try:
                reading_models = [
                    Reading(
                        device_id=r.device_id,
                        timestamp=r.timestamp,
                        power_watts=r.power_watts,
                        voltage_volts=r.voltage_volts,
                        current_amps=r.current_amps,
                        energy_kwh=0.0,  # Calculated separately
                        created_at=datetime.utcnow()
                    )
                    for r in readings
                ]
                session.add_all(reading_models)
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to write readings: {e}")
                raise
    
    async def get_recent_readings(
        self,
        device_id: UUID,
        minutes: int
    ) -> List[Reading]:
        """Get readings for device within last N minutes"""
        async with self.session_factory() as session:
            cutoff_time = datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=minutes)
            
            stmt = (
                select(Reading)
                .where(Reading.device_id == device_id)
                .where(Reading.timestamp >= cutoff_time)
                .order_by(Reading.timestamp.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def create_alert(
        self,
        device_id: Optional[UUID],
        alert_type: str,
        severity: str,
        message: str,
        threshold_value: Optional[float],
        actual_value: Optional[float]
    ) -> Alert:
        """Create new alert"""
        async with self.session_factory() as session:
            try:
                alert = Alert(
                    device_id=device_id,
                    timestamp=datetime.now(ZoneInfo("Asia/Kolkata")),
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    threshold_value=threshold_value,
                    actual_value=actual_value,
                    is_acknowledged=False,
                    created_at=datetime.utcnow()
                )
                session.add(alert)
                await session.commit()
                await session.refresh(alert)
                return alert
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to create alert: {e}")
                raise
    
    async def get_latest_readings_all_devices(self) -> Dict[UUID, Reading]:
        """Get most recent reading for each device"""
        async with self.session_factory() as session:
            # Subquery: max timestamp per device
            subq = (
                select(
                    Reading.device_id,
                    func.max(Reading.timestamp).label('max_ts')
                )
                .group_by(Reading.device_id)
                .subquery()
            )
            
            # Join to get full reading
            stmt = (
                select(Reading)
                .join(
                    subq,
                    and_(
                        Reading.device_id == subq.c.device_id,
                        Reading.timestamp == subq.c.max_ts
                    )
                )
            )
            result = await session.execute(stmt)
            readings = result.scalars().all()
            
            return {r.device_id: r for r in readings}
    
    async def get_hourly_summaries(
        self,
        device_id: Optional[UUID],
        start_date: date,
        end_date: date
    ) -> List[HourlySummary]:
        """Get hourly summaries within date range"""
        async with self.session_factory() as session:
            stmt = (
                select(HourlySummary)
                .where(HourlySummary.hour_timestamp >= start_date)
                .where(HourlySummary.hour_timestamp <= end_date)
            )
            if device_id:
                stmt = stmt.where(HourlySummary.device_id == device_id)
            
            stmt = stmt.order_by(HourlySummary.hour_timestamp.asc())
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def create_hourly_summary(
        self,
        device_id: UUID,
        hour_timestamp: datetime,
        avg_power: float,
        max_power: float,
        min_power: float,
        total_kwh: float,
        reading_count: int
    ) -> HourlySummary:
        """Create hourly summary record"""
        async with self.session_factory() as session:
            try:
                summary = HourlySummary(
                    device_id=device_id,
                    hour_timestamp=hour_timestamp,
                    avg_power_watts=avg_power,
                    max_power_watts=max_power,
                    min_power_watts=min_power,
                    total_kwh=total_kwh,
                    reading_count=reading_count,
                    created_at=datetime.utcnow()
                )
                session.add(summary)
                await session.commit()
                await session.refresh(summary)
                return summary
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to create hourly summary: {e}")
                raise
    
    async def delete_old_readings(self, days: int) -> int:
        """Delete readings older than N days"""
        async with self.session_factory() as session:
            try:
                cutoff_date = datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(days=days)
                
                stmt = delete(Reading).where(Reading.timestamp < cutoff_date)
                result = await session.execute(stmt)
                await session.commit()
                
                deleted_count = result.rowcount
                self.logger.info(f"Deleted {deleted_count} readings older than {cutoff_date}")
                return deleted_count
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to delete old readings: {e}")
                raise
```

**Connection Pool Settings:**
```python
# app/database.py
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,          # Max 10 connections
    max_overflow=20,       # Allow 20 additional connections under load
    pool_pre_ping=True,    # Test connection before using
    pool_recycle=3600      # Recycle connections every hour
)
```

---

### B.4 Analysis Service (`app/services/analysis_service.py`)

**Purpose:** Compute unknown load and detect consumption spikes.

**Class Structure:**

```python
class AnalysisService:
    def __init__(
        self,
        storage_service: StorageService,
        alert_service: 'AlertService',
        config: dict
    ):
        self.storage = storage_service
        self.alert_service = alert_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get main meter device ID from config
        self.main_meter_id: UUID = config['main_meter_device_id']
    
    async def analyze_latest(self, latest_readings: List[SimulatedReading]):
        """Run all analysis on latest readings"""
        try:
            # Analysis 1: Unknown load calculation
            unknown_load = await self._calculate_unknown_load(latest_readings)
            self.logger.debug(f"Unknown load: {unknown_load}W")
            
            # Analysis 2: Spike detection
            await self._check_for_spike(latest_readings, unknown_load)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            # Don't re-raise - analysis failure shouldn't break polling
    
    async def _calculate_unknown_load(
        self, 
        readings: List[SimulatedReading]
    ) -> float:
        """
        Unknown Load = Main Meter Power - Sum(All Smart Plug Powers)
        Can be negative if timing skew causes mismatch.
        """
        # Find main meter reading
        main_meter_reading = next(
            (r for r in readings if r.device_id == self.main_meter_id),
            None
        )
        if not main_meter_reading:
            self.logger.warning("Main meter reading not found")
            return 0.0
        
        # Sum all smart plug readings
        smart_plug_total = sum(
            r.power_watts 
            for r in readings 
            if r.device_id != self.main_meter_id
        )
        
        unknown_load = main_meter_reading.power_watts - smart_plug_total
        
        # Store in cache for SSE broadcast
        self._last_unknown_load = unknown_load
        
        return round(unknown_load, 2)
    
    async def _check_for_spike(
        self,
        latest_readings: List[SimulatedReading],
        unknown_load: float
    ):
        """
        Spike Detection Algorithm:
        1. Get last 60 minutes of main meter readings
        2. Calculate rolling average
        3. If current > threshold * average, spike detected
        4. Check suppression rules before creating alert
        """
        # Get current main meter reading
        main_reading = next(
            (r for r in latest_readings if r.device_id == self.main_meter_id),
            None
        )
        if not main_reading:
            return
        
        current_power = main_reading.power_watts
        
        # Get historical readings for rolling average
        window_minutes = self.config['rolling_average_window_minutes']
        historical_readings = await self.storage.get_recent_readings(
            self.main_meter_id,
            minutes=window_minutes
        )
        
        if len(historical_readings) < 10:
            # Not enough data for reliable average
            self.logger.debug("Insufficient data for spike detection")
            return
        
        # Calculate rolling average
        rolling_avg = sum(r.power_watts for r in historical_readings) / len(historical_readings)
        
        # Check threshold
        spike_threshold_pct = self.config['spike_threshold_percentage']
        threshold_power = rolling_avg * (1 + spike_threshold_pct / 100)
        
        if current_power > threshold_power:
            # Spike detected!
            percentage_above = ((current_power - rolling_avg) / rolling_avg) * 100
            
            self.logger.info(
                f"Spike detected: {current_power}W is {percentage_above:.1f}% "
                f"above average of {rolling_avg:.1f}W"
            )
            
            # Create alert (AlertService will handle suppression)
            await self.alert_service.create_spike_alert(
                device_id=self.main_meter_id,
                current_power=current_power,
                average_power=rolling_avg,
                percentage_above=percentage_above
            )
    
    def get_last_unknown_load(self) -> float:
        """Get cached unknown load for SSE broadcast"""
        return getattr(self, '_last_unknown_load', 0.0)
```

**Configuration Values:**
```python
# config.py
ANALYSIS_CONFIG = {
    'main_meter_device_id': UUID('...'),  # Loaded from DB on startup
    'rolling_average_window_minutes': 60,
    'spike_threshold_percentage': 50,
}
```

---

### B.5 Alert Service (`app/services/alert_service.py`)

**Purpose:** Create alerts with suppression logic.

**Class Structure:**

```python
class AlertService:
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
        self.logger = logging.getLogger(__name__)
        
        # Cache last alert per type to implement suppression
        self._last_alerts: Dict[str, Alert] = {}
    
    async def create_spike_alert(
        self,
        device_id: UUID,
        current_power: float,
        average_power: float,
        percentage_above: float
    ):
        """
        Create spike alert with suppression logic:
        - If last spike was >2 polls ago (>10s): Create new alert
        - If last spike was ≤2 polls ago AND power differs by >10%: Create new alert
        - Else: Skip (duplicate/constant spike)
        """
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        
        # Check last spike alert
        last_spike = self._last_alerts.get('spike')
        
        should_create = True
        
        if last_spike:
            time_diff = (now - last_spike.timestamp).total_seconds()
            
            if time_diff <= 10:  # Within 2 poll cycles
                # Check if spike magnitude changed significantly
                power_diff_pct = abs(current_power - last_spike.actual_value) / last_spike.actual_value
                
                if power_diff_pct <= 0.10:  # Less than 10% change
                    should_create = False
                    self.logger.debug("Suppressing duplicate spike alert")
        
        if should_create:
            # Determine severity
            if percentage_above > 75:
                severity = 'critical'
            else:
                severity = 'warning'
            
            # Create message
            message = (
                f"Power consumption spiked to {current_power:.1f}W, "
                f"{percentage_above:.1f}% above average of {average_power:.1f}W"
            )
            
            # Store alert
            alert = await self.storage.create_alert(
                device_id=device_id,
                alert_type='spike',
                severity=severity,
                message=message,
                threshold_value=average_power,
                actual_value=current_power
            )
            
            # Cache for suppression
            self._last_alerts['spike'] = alert
            
            self.logger.info(f"Created spike alert: {message}")
            
            # Notify SSE broadcast (via event queue)
            await self._notify_sse_broadcast(alert)
    
    async def _notify_sse_broadcast(self, alert: Alert):
        """Add alert to SSE broadcast queue"""
        # Implementation depends on SSE architecture
        # Could use asyncio.Queue or in-memory list
        pass
```

---

### B.6 Billing Service (`app/services/billing_service.py`)

**Purpose:** Calculate electricity cost using slab rates.

**Class Structure:**

```python
@dataclass
class SlabRate:
    min_units: int
    max_units: Optional[int]  # None for last slab
    rate_per_unit: float

@dataclass
class BillEstimate:
    total_kwh: float
    total_cost_inr: float
    slab_breakdown: List[dict]

class BillingService:
    def __init__(self, config: dict):
        self.slab_rates = [
            SlabRate(min_units=0, max_units=100, rate_per_unit=3.0),
            SlabRate(min_units=101, max_units=300, rate_per_unit=7.5),
            SlabRate(min_units=301, max_units=500, rate_per_unit=12.0),
            SlabRate(min_units=501, max_units=None, rate_per_unit=15.0),
        ]
        self.logger = logging.getLogger(__name__)
    
    def calculate_cost(self, total_kwh: float) -> BillEstimate:
        """
        Calculate bill using slab rates.
        
        Example:
        - 350 kWh consumed
        - Slab 1 (0-100): 100 units × ₹3 = ₹300
        - Slab 2 (101-300): 200 units × ₹7.5 = ₹1,500
        - Slab 3 (301-500): 50 units × ₹12 = ₹600
        - Total: ₹2,400
        """
        remaining_units = total_kwh
        total_cost = 0.0
        breakdown = []
        
        for slab in self.slab_rates:
            if remaining_units <= 0:
                break
            
            # Calculate units in this slab
            slab_capacity = (
                (slab.max_units - slab.min_units) 
                if slab.max_units 
                else float('inf')
            )
            units_in_slab = min(remaining_units, slab_capacity)
            
            # Calculate cost for this slab
            slab_cost = units_in_slab * slab.rate_per_unit
            total_cost += slab_cost
            remaining_units -= units_in_slab
            
            # Add to breakdown
            slab_label = (
                f"{slab.min_units}-{slab.max_units}" 
                if slab.max_units 
                else f"{slab.min_units}+"
            )
            breakdown.append({
                'slab': slab_label,
                'units': round(units_in_slab, 2),
                'rate': slab.rate_per_unit,
                'cost': round(slab_cost, 2)
            })
        
        return BillEstimate(
            total_kwh=round(total_kwh, 2),
            total_cost_inr=round(total_cost, 2),
            slab_breakdown=breakdown
        )
    
    def update_slab_rates(self, new_rates: List[dict]):
        """Update slab rates from settings API"""
        self.slab_rates = [
            SlabRate(
                min_units=r['min_units'],
                max_units=r.get('max_units'),
                rate_per_unit=r['rate_per_unit']
            )
            for r in new_rates
        ]
        self.logger.info("Slab rates updated")
```

---

### B.7 SSE Broadcast Service (`app/api/routes/sse.py`)

**Purpose:** Push real-time updates to connected frontend clients.

**Architecture:**

```python
class SSEBroadcaster:
    def __init__(self):
        self.connections: Set[asyncio.Queue] = set()
        self.max_connections = 10
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> asyncio.Queue:
        """Register new SSE client"""
        if len(self.connections) >= self.max_connections:
            raise HTTPException(
                status_code=429,
                detail="Maximum concurrent connections reached"
            )
        
        queue = asyncio.Queue(maxsize=100)
        self.connections.add(queue)
        self.logger.info(f"SSE client connected. Total: {len(self.connections)}")
        return queue
    
    def disconnect(self, queue: asyncio.Queue):
        """Unregister SSE client"""
        self.connections.remove(queue)
        self.logger.info(f"SSE client disconnected. Total: {len(self.connections)}")
    
    async def broadcast(self, event_type: str, data: dict):
        """Send event to all connected clients"""
        dead_queues = set()
        
        for queue in self.connections:
            try:
                queue.put_nowait({
                    'event': event_type,
                    'data': data
                })
            except asyncio.QueueFull:
                self.logger.warning("Client queue full, dropping event")
            except Exception as e:
                self.logger.error(f"Failed to queue event: {e}")
                dead_queues.add(queue)
        
        # Clean up dead connections
        for queue in dead_queues:
            self.disconnect(queue)

# Global broadcaster instance
broadcaster = SSEBroadcaster()

# Background task to push updates every 5 seconds
async def sse_update_loop(
    storage: StorageService,
    analysis: AnalysisService
):
    """Continuously push latest state to SSE clients"""
    while True:
        try:
            # Get latest readings
            latest_readings = await storage.get_latest_readings_all_devices()
            
            # Get unknown load from analysis cache
            unknown_load = analysis.get_last_unknown_load()
            
            # Get unacknowledged alerts
            alerts = await storage.get_unacknowledged_alerts()
            
            # Format for SSE
            data = {
                'timestamp': datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
                'devices': [
                    {
                        'device_id': str(r.device_id),
                        'device_name': r.device.name,
                        'power_watts': r.power_watts,
                        'voltage_volts': r.voltage_volts,
                        'current_amps': r.current_amps,
                    }
                    for r in latest_readings.values()
                ],
                'unknown_load_watts': unknown_load,
                'alerts': [
                    {
                        'id': a.id,
                        'message': a.message,
                        'severity': a.severity,
                        'timestamp': a.timestamp.isoformat()
                    }
                    for a in alerts[:3]  # Only send latest 3
                ]
            }
            
            # Broadcast to all clients
            await broadcaster.broadcast('reading', data)
            
        except Exception as e:
            logger.error(f"SSE update loop error: {e}", exc_info=True)
        
        # Wait 5 seconds
        await asyncio.sleep(5)

# Heartbeat task (every 30 seconds)
async def sse_heartbeat_loop():
    """Send keepalive to prevent connection timeout"""
    while True:
        await asyncio.sleep(30)
        await broadcaster.broadcast('heartbeat', {
            'timestamp': datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        })

# SSE endpoint
@router.get("/stream/live-updates")
async def stream_live_updates(request: Request):
    """Server-Sent Events endpoint"""
    
    async def event_generator():
        queue = await broadcaster.connect()
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for event (with timeout)
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=35.0  # Slightly longer than heartbeat
                    )
                    
                    # Format SSE message
                    yield {
                        "event": event['event'],
                        "data": json.dumps(event['data'])
                    }
                    
                except asyncio.TimeoutError:
                    # No event received, send comment to keep connection alive
                    yield {"comment": "keepalive"}
                    
        finally:
            broadcaster.disconnect(queue)
    
    return EventSourceResponse(event_generator())
```

**Startup Integration:**
```python
# app/main.py
@app.on_event("startup")
async def startup_event():
    # Start SSE background tasks
    asyncio.create_task(sse_update_loop(storage_service, analysis_service))
    asyncio.create_task(sse_heartbeat_loop())
    
    # Start polling service
    await polling_service.start()
```

---

## C. DATABASE DESIGN

### C.1 Schema Definition (PostgreSQL + SQLAlchemy)

**File:** `app/models/device.py`

```python
from sqlalchemy import Column, String, Boolean, DateTime, UUID as SQLUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(
        SQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(String(100), nullable=False)
    device_type = Column(
        String(20),
        nullable=False,
        index=True
    )  # 'main_meter' or 'smart_plug'
    location = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=True)  # Simulator identifier
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    readings = relationship("Reading", back_populates="device", lazy="select")
    hourly_summaries = relationship("HourlySummary", back_populates="device")
    daily_summaries = relationship("DailySummary", back_populates="device")
    alerts = relationship("Alert", back_populates="device")
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, type={self.device_type})>"
```

**File:** `app/models/reading.py`

```python
from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, BIGINT
from sqlalchemy import Index, UUID as SQLUUID
from sqlalchemy.orm import relationship

class Reading(Base):
    __tablename__ = 'readings'
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    device_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    timestamp = Column(DateTime(timezone=False), nullable=False, index=True)  # IST
    power_watts = Column(Numeric(10, 2), nullable=False)
    voltage_volts = Column(Numeric(6, 2), nullable=True)
    current_amps = Column(Numeric(8, 2), nullable=True)
    energy_kwh = Column(Numeric(12, 3), nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="readings")
    
    __table_args__ = (
        # Composite index for time-series queries
        Index('ix_readings_device_timestamp', 'device_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Reading(id={self.id}, device={self.device_id}, power={self.power_watts}W)>"
```

**File:** `app/models/summary.py`

```python
from sqlalchemy import Column, Integer, Date, DateTime, Numeric, ForeignKey
from sqlalchemy import Index, UUID as SQLUUID, CheckConstraint
from sqlalchemy.orm import relationship

class HourlySummary(Base):
    __tablename__ = 'hourly_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False
    )
    hour_timestamp = Column(DateTime(timezone=False), nullable=False)  # Start of hour
    avg_power_watts = Column(Numeric(10, 2), nullable=False)
    max_power_watts = Column(Numeric(10, 2), nullable=False)
    min_power_watts = Column(Numeric(10, 2), nullable=False)
    total_kwh = Column(Numeric(10, 3), nullable=False)
    reading_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="hourly_summaries")
    
    __table_args__ = (
        # Prevent duplicate summaries for same device/hour
        Index(
            'uix_hourly_device_hour',
            'device_id',
            'hour_timestamp',
            unique=True
        ),
        Index('ix_hourly_timestamp', 'hour_timestamp'),
    )

class DailySummary(Base):
    __tablename__ = 'daily_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False
    )
    date = Column(Date, nullable=False)
    total_kwh = Column(Numeric(12, 3), nullable=False)
    avg_power_watts = Column(Numeric(10, 2), nullable=False)
    peak_hour = Column(
        Integer,
        nullable=False,
        CheckConstraint('peak_hour >= 0 AND peak_hour <= 23')
    )
    estimated_cost_inr = Column(Numeric(10, 2), nullable=True)  # Main meter only
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="daily_summaries")
    
    __table_args__ = (
        Index('uix_daily_device_date', 'device_id', 'date', unique=True),
        Index('ix_daily_date', 'date'),
    )
```

**File:** `app/models/alert.py`

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Boolean
from sqlalchemy import ForeignKey, UUID as SQLUUID, CheckConstraint, Index
from sqlalchemy.orm import relationship

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='SET NULL'),
        nullable=True
    )
    timestamp = Column(DateTime(timezone=False), nullable=False, index=True)  # IST
    alert_type = Column(
        String(50),
        nullable=False,
        CheckConstraint(
            "alert_type IN ('spike', 'high_overnight', 'long_runtime', 'bill_threshold')"
        )
    )
    severity = Column(
        String(20),
        nullable=False,
        CheckConstraint("severity IN ('info', 'warning', 'critical')")
    )
    message = Column(Text, nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=True)
    actual_value = Column(Numeric(10, 2), nullable=True)
    is_acknowledged = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    
    __table_args__ = (
        Index('ix_alerts_type_timestamp', 'alert_type', 'timestamp'),
    )
```

### C.2 Alembic Migration Structure

**File:** `alembic/versions/001_initial_schema.py`

```python
"""Initial schema

Revision ID: 001
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

def upgrade():
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('device_type', sa.String(20), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_devices_type', 'devices', ['device_type'])
    op.create_index('ix_devices_active', 'devices', ['is_active'])
    
    # Create readings table
    op.create_table(
        'readings',
        sa.Column('id', sa.BIGINT, primary_key=True, autoincrement=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('voltage_volts', sa.Numeric(6, 2), nullable=True),
        sa.Column('current_amps', sa.Numeric(8, 2), nullable=True),
        sa.Column('energy_kwh', sa.Numeric(12, 3), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_readings_device', 'readings', ['device_id'])
    op.create_index('ix_readings_timestamp', 'readings', ['timestamp'])
    op.create_index('ix_readings_device_timestamp', 'readings', ['device_id', 'timestamp'])
    
    # Create hourly_summaries table
    op.create_table(
        'hourly_summaries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hour_timestamp', sa.DateTime, nullable=False),
        sa.Column('avg_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_kwh', sa.Numeric(10, 3), nullable=False),
        sa.Column('reading_count', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('uix_hourly_device_hour', 'hourly_summaries', ['device_id', 'hour_timestamp'], unique=True)
    
    # Create daily_summaries table
    op.create_table(
        'daily_summaries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('total_kwh', sa.Numeric(12, 3), nullable=False),
        sa.Column('avg_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('peak_hour', sa.Integer, nullable=False),
        sa.Column('estimated_cost_inr', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('uix_daily_device_date', 'daily_summaries', ['device_id', 'date'], unique=True)
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('threshold_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean, nullable=False, default=False),
        sa.Column('acknowledged_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_alerts_timestamp', 'alerts', ['timestamp'])
    op.create_index('ix_alerts_acknowledged', 'alerts', ['is_acknowledged'])

def downgrade():
    op.drop_table('alerts')
    op.drop_table('daily_summaries')
    op.drop_table('hourly_summaries')
    op.drop_table('readings')
    op.drop_table('devices')
```

**File:** `alembic/versions/002_seed_devices.py`

```python
"""Seed initial devices

Revision ID: 002
Depends On: 001
"""

from alembic import op
import uuid

def upgrade():
    # Define device UUIDs (these will be used in config)
    main_meter_id = uuid.uuid4()
    ac_id = uuid.uuid4()
    geyser_id = uuid.uuid4()
    pump_id = uuid.uuid4()
    
    # Insert devices
    op.execute(f"""
        INSERT INTO devices (id, name, device_type, location, is_active)
        VALUES
            ('{main_meter_id}', 'Main Building Meter', 'main_meter', 'Distribution Panel', true),
            ('{ac_id}', 'AC Unit', 'smart_plug', 'Floor 1, Common Room', true),
            ('{geyser_id}', 'Water Geyser', 'smart_plug', 'Floor 2, Bathroom Block', true),
            ('{pump_id}', 'Water Pump', 'smart_plug', 'Ground Floor, Pump Room', true)
    """)
    
    # Write UUIDs to config file for application use
    with open('/tmp/device_ids.txt', 'w') as f:
        f.write(f"MAIN_METER_ID={main_meter_id}\n")
        f.write(f"AC_ID={ac_id}\n")
        f.write(f"GEYSER_ID={geyser_id}\n")
        f.write(f"PUMP_ID={pump_id}\n")

def downgrade():
    op.execute("DELETE FROM devices")
```

---

## D. API DESIGN

### D.1 Endpoint Specifications

**Base URL:** `/api/v1`

#### D.1.1 Devices Endpoints

**GET /api/v1/devices**

Request: None

Response (200):
```json
{
  "devices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
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

**PATCH /api/v1/devices/{device_id}**

Request:
```json
{
  "name": "Updated Device Name",
  "location": "New Location"
}
```

Response (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Device Name",
  "device_type": "main_meter",
  "location": "New Location",
  "is_active": true,
  "created_at": "2026-04-05T10:00:00",
  "updated_at": "2026-04-05T14:30:00"
}
```

Errors:
- 404: Device not found
- 422: Validation error (name too long, etc.)

#### D.1.2 Readings Endpoints

**GET /api/v1/readings/current**

Request: None

Response (200):
```json
{
  "timestamp": "2026-04-05T14:32:15",
  "readings": [
    {
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "device_name": "Main Building Meter",
      "device_type": "main_meter",
      "power_watts": 3456.78,
      "voltage_volts": 230.5,
      "current_amps": 15.2,
      "energy_kwh": 245.678
    },
    {
      "device_id": "660e8400-e29b-41d4-a716-446655440001",
      "device_name": "AC Unit",
      "device_type": "smart_plug",
      "power_watts": 1523.50,
      "voltage_volts": null,
      "current_amps": null,
      "energy_kwh": 67.234
    }
  ],
  "unknown_load_watts": 832.45
}
```

**GET /api/v1/readings/historical**

Query Parameters:
- `device_id` (UUID, required)
- `start_time` (ISO 8601 datetime, required)
- `end_time` (ISO 8601 datetime, required)
- `limit` (int, optional, default=1000, max=10000)

Request: `GET /api/v1/readings/historical?device_id=550e8400-e29b-41d4-a716-446655440000&start_time=2026-04-05T10:00:00&end_time=2026-04-05T14:00:00`

Response (200):
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "Main Building Meter",
  "start_time": "2026-04-05T10:00:00",
  "end_time": "2026-04-05T14:00:00",
  "readings": [
    {
      "timestamp": "2026-04-05T14:00:00",
      "power_watts": 3200.50,
      "energy_kwh": 245.123
    }
  ],
  "count": 2880
}
```

Errors:
- 400: Date range exceeds 7 days
- 404: Device not found

#### D.1.3 Summaries Endpoints

**GET /api/v1/summaries/hourly**

Query Parameters:
- `device_id` (UUID, optional)
- `start_date` (ISO 8601 date, required)
- `end_date` (ISO 8601 date, required)

Response (200):
```json
{
  "start_date": "2026-04-01",
  "end_date": "2026-04-05",
  "summaries": [
    {
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "device_name": "Main Building Meter",
      "hour_timestamp": "2026-04-05T13:00:00",
      "avg_power_watts": 3200.50,
      "max_power_watts": 4500.00,
      "min_power_watts": 2100.00,
      "total_kwh": 3.2,
      "reading_count": 720
    }
  ]
}
```

**GET /api/v1/summaries/daily**

Query Parameters: Same as hourly

Response (200):
```json
{
  "summaries": [
    {
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
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

#### D.1.4 Alerts Endpoints

**GET /api/v1/alerts**

Query Parameters:
- `is_acknowledged` (bool, optional)
- `alert_type` (string, optional)
- `start_date` (ISO 8601 date, optional)
- `end_date` (ISO 8601 date, optional)
- `limit` (int, optional, default=100, max=1000)

Response (200):
```json
{
  "alerts": [
    {
      "id": 123,
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
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

**PATCH /api/v1/alerts/{alert_id}/acknowledge**

Request: None

Response (200):
```json
{
  "id": 123,
  "is_acknowledged": true,
  "acknowledged_at": "2026-04-05T14:35:00"
}
```

**GET /api/v1/alerts/unacknowledged/count**

Response (200):
```json
{
  "count": 12
}
```

#### D.1.5 Billing Endpoints

**GET /api/v1/billing/current-month**

Response (200):
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
    {
      "slab": "0-100",
      "units": 100.0,
      "rate": 3.0,
      "cost": 300.0
    },
    {
      "slab": "101-300",
      "units": 200.0,
      "rate": 7.5,
      "cost": 1500.0
    },
    {
      "slab": "301-500",
      "units": 42.5,
      "rate": 12.0,
      "cost": 510.0
    }
  ]
}
```

**GET /api/v1/billing/monthly-comparison**

Response (200):
```json
{
  "months": [
    {
      "month": "2026-03",
      "total_kwh": 1850.0,
      "total_cost_inr": 13875.0
    },
    {
      "month": "2026-02",
      "total_kwh": 1720.0,
      "total_cost_inr": 12900.0
    }
  ]
}
```

#### D.1.6 Settings Endpoints

**GET /api/v1/settings**

Response (200):
```json
{
  "polling_interval_seconds": 5,
  "spike_threshold_percentage": 50,
  "rolling_average_window_minutes": 60,
  "data_retention_days": 7,
  "electricity_slabs": [
    {
      "min_units": 0,
      "max_units": 100,
      "rate_per_unit": 3.0
    },
    {
      "min_units": 101,
      "max_units": 300,
      "rate_per_unit": 7.5
    },
    {
      "min_units": 301,
      "max_units": 500,
      "rate_per_unit": 12.0
    },
    {
      "min_units": 501,
      "max_units": null,
      "rate_per_unit": 15.0
    }
  ]
}
```

**PUT /api/v1/settings**

Request: (same structure as GET response)

Response (200): (updated settings)

Note: Changes to `polling_interval_seconds` require backend restart to take effect.

#### D.1.7 Admin Endpoints

**POST /api/v1/admin/cleanup-old-readings**

Request: None

Response (200):
```json
{
  "deleted_count": 12500,
  "cutoff_timestamp": "2026-03-29T14:35:00",
  "status": "success"
}
```

#### D.1.8 SSE Endpoint

**GET /stream/live-updates**

Headers:
- Accept: text/event-stream

Response: Server-Sent Events stream

Event types:
1. `reading` - New data cycle
2. `alert` - New alert generated
3. `heartbeat` - Keepalive ping

Example stream:
```
event: reading
data: {"timestamp":"2026-04-05T14:35:20","devices":[...],"unknown_load_watts":832.45,"alerts":[]}

event: heartbeat
data: {"timestamp":"2026-04-05T14:35:50"}

event: alert
data: {"id":124,"message":"Spike detected","severity":"warning"}
```

---

## E. FAILURE HANDLING

### E.1 Simulator Failures

**Scenario 1: Simulator raises exception during reading generation**

Behavior:
1. Exception caught in `PollingService.poll_and_store()`
2. Error logged with full traceback: `logger.error(f"Simulator failed: {e}", exc_info=True)`
3. This poll cycle skipped (no database writes)
4. Next poll cycle runs normally after 5 seconds
5. If 10 consecutive failures: Log critical alert, continue retrying

Implementation:
```python
self.consecutive_failures = 0

async def poll_and_store(self):
    try:
        readings = self.simulator.generate_readings()
        self.consecutive_failures = 0  # Reset on success
    except Exception as e:
        self.consecutive_failures += 1
        if self.consecutive_failures >= 10:
            self.logger.critical(f"Simulator failed {self.consecutive_failures} times")
        raise
```

**Scenario 2: Simulator returns invalid data (negative power, null values)**

Behavior:
1. Validation in `StorageService.write_readings_batch()`
2. Use Pydantic schema to validate:
   - power_watts >= 0
   - voltage_volts > 0 (if not null)
   - current_amps >= 0 (if not null)
3. If validation fails: Log error, discard reading, skip this cycle
4. Continue polling

Implementation:
```python
class ReadingSchema(BaseModel):
    device_id: UUID
    power_watts: float = Field(ge=0)
    voltage_volts: Optional[float] = Field(gt=0)
    current_amps: Optional[float] = Field(ge=0)
    
    @validator('power_watts')
    def validate_power(cls, v):
        if v < 0 or v > 100000:  # Sanity check
            raise ValueError("Invalid power reading")
        return v
```

### E.2 Database Failures

**Scenario 1: PostgreSQL unavailable during startup**

Behavior:
1. SQLAlchemy async engine fails to connect
2. Backend logs error: `"Failed to connect to database: {error}"`
3. Backend exits with code 1
4. Docker/systemd restarts backend (deployment system responsibility)

**Scenario 2: Connection lost during operation**

Behavior:
1. Write operation fails with connection error
2. SQLAlchemy session rolls back transaction
3. Error logged: `"Database write failed: {error}"`
4. This poll cycle skipped
5. Next cycle creates new connection from pool
6. SSE clients receive error event:
```json
{"event": "error", "data": {"message": "Database temporarily unavailable"}}
```

**Scenario 3: Database disk full**

Behavior:
1. Write fails with "disk full" error
2. Critical log: `"DATABASE DISK FULL - CANNOT WRITE"`
3. Polling continues but all writes fail
4. SSE broadcast continues with cached data
5. Manual intervention required (admin must free disk space or run cleanup)

**Scenario 4: Query timeout (slow query)**

Behavior:
1. Set statement timeout: `SET statement_timeout = '30s'`
2. If query exceeds 30s, PostgreSQL cancels it
3. API returns 504 Gateway Timeout
4. Frontend displays error toast

Implementation:
```python
# Set timeout per session
async with session_factory() as session:
    await session.execute(text("SET statement_timeout = '30s'"))
    # ... execute query
```

### E.3 API Failures

**Scenario 1: Client requests non-existent device**

Response:
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Device with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Scenario 2: Client sends invalid request body**

Response:
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Scenario 3: Internal server error during request processing**

Behavior:
1. Exception caught by FastAPI global exception handler
2. Error logged with full traceback
3. Response:
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": "An internal error occurred. Please try again later."
}
```

Frontend action: Display error toast, show "Retry" button

**Scenario 4: Request timeout (>30s)**

Behavior:
1. Uvicorn request timeout kills request
2. Frontend fetch() receives timeout error
3. Display error: "Request timed out. The server may be overloaded."

### E.4 SSE Failures

**Scenario 1: Client disconnects**

Behavior:
1. EventSource detects disconnect via `request.is_disconnected()`
2. Server calls `broadcaster.disconnect(queue)`
3. Client queue removed from connections set
4. No error logged (normal operation)

**Scenario 2: Client queue full (slow client)**

Behavior:
1. `queue.put_nowait()` raises `asyncio.QueueFull`
2. Event dropped (not sent to this client)
3. Warning logged: `"Client queue full, dropping event"`
4. Next event attempts delivery again
5. If queue remains full for 5 consecutive events: Disconnect client

**Scenario 3: Network interruption (client side)**

Frontend behavior:
1. EventSource fires `error` event
2. Frontend auto-reconnects with exponential backoff:
   - Attempt 1: 1 second
   - Attempt 2: 2 seconds
   - Attempt 3: 4 seconds
   - Attempt 4: 8 seconds
   - Attempt 5+: 30 seconds
3. Display "Connection Lost" banner after 3 failed reconnects
4. Banner includes "Retry Now" button

Implementation:
```javascript
let retryCount = 0;
let eventSource;

function connectSSE() {
  eventSource = new EventSource('/stream/live-updates');
  
  eventSource.onerror = (error) => {
    retryCount++;
    const delay = Math.min(Math.pow(2, retryCount), 30) * 1000;
    
    if (retryCount >= 3) {
      setConnectionStatus('disconnected');
    }
    
    setTimeout(connectSSE, delay);
  };
  
  eventSource.onopen = () => {
    retryCount = 0;
    setConnectionStatus('connected');
  };
}
```

**Scenario 4: SSE connection limit reached (10 clients)**

Response:
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Maximum concurrent connections reached. Close other dashboards and retry."
}
```

Frontend: Display error modal, suggest closing other tabs

### E.5 Background Job Failures

**Scenario 1: Hourly summary job fails**

Behavior:
1. Exception caught in job handler
2. Error logged: `"Hourly summary job failed for hour {hour}: {error}"`
3. Job does NOT retry (wait for next hour)
4. Missing summary gap in data
5. Frontend handles missing data gracefully (skip gap in chart)

**Scenario 2: Daily summary job fails**

Behavior:
1. Exception caught in job handler
2. Critical log: `"Daily summary job failed for {date}: {error}"`
3. Manual re-run required via admin endpoint: `POST /api/v1/admin/regenerate-daily-summary?date=2026-04-05`

**Scenario 3: Cleanup job deletes too much data (bug)**

Prevention:
1. Dry-run mode: Log what would be deleted without deleting
2. Require explicit confirmation via API call
3. Backup database before cleanup (deployment responsibility)

### E.6 Frontend Failures

**Scenario 1: API request fails**

Behavior:
1. Fetch catches error
2. Display error toast: `"Failed to load data. {error_message}"`
3. Show "Retry" button
4. Page retains last successful state

**Scenario 2: Chart rendering fails (invalid data)**

Behavior:
1. Recharts throws error
2. React Error Boundary catches it
3. Display fallback UI: "Unable to render chart. Try refreshing the page."
4. Error logged to console

**Scenario 3: Browser local storage full**

Behavior:
1. Settings save fails
2. Display error: "Unable to save settings. Clear browser storage and retry."
3. Settings revert to server defaults

---

## F. OPEN QUESTIONS

### F.1 Technical Decisions

**Q1: Cumulative Energy Tracking**
- Should cumulative kWh reset monthly/yearly, or increase indefinitely?
- Decision: Increase indefinitely, reset manually via admin action if needed

**Q2: Time Zone Edge Cases**
- How to handle IST to UTC conversion for date boundaries?
- What happens at midnight when aggregating daily summaries?
- Decision: Always use IST internally, convert to UTC only for database timestamps

**Q3: Concurrent Access**
- Can multiple admins edit settings simultaneously?
- Who wins in conflict?
- Decision: Last write wins, no optimistic locking (single admin assumption)

**Q4: Historical Data Backfill**
- If hourly summary job fails, can we backfill from raw readings?
- Decision: Yes, provide admin endpoint to regenerate summaries for date range

**Q5: Alert Deduplication Window**
- 2 poll cycles (10s) enough for spike suppression?
- Should there be separate windows for different alert types?
- Decision: 10s sufficient for MVP, configurable per alert type in future

### F.2 Data Integrity

**Q6: Reading Timestamp Source**
- Use simulator timestamp or server receive timestamp?
- Decision: Use server timestamp (datetime.now()) for consistency

**Q7: Missing Poll Cycles**
- If polling skips cycles due to errors, does analysis account for gaps?
- Decision: Rolling average ignores gaps (uses all available data)

**Q8: Database Constraints**
- Should we enforce `energy_kwh` monotonically increasing per device?
- Decision: No constraint, allow manual corrections

### F.3 Performance

**Q9: Query Optimization**
- At what table size do we need partitioning?
- Decision: Monitor performance, add partitioning if readings >10M rows

**Q10: SSE Broadcast Efficiency**
- Broadcasting to 10 clients every 5s - any bottleneck?
- Decision: asyncio.Queue handles this easily, no optimization needed for MVP

**Q11: Frontend Graph Performance**
- 360 data points in Recharts - any lag?
- Decision: Test on low-end devices, optimize if needed

### F.4 UX Decisions

**Q12: Alert Auto-Dismissal**
- Should alerts auto-acknowledge after X hours?
- Decision: No auto-dismissal in MVP, manual only

**Q13: Unknown Load Display**
- Show negative values or floor at 0?
- Decision: Show negative (per spec requirement)

**Q14: Historical Data Granularity**
- Show raw 5s data or hourly summaries for date ranges >1 day?
- Decision: Use hourly summaries for ranges >1 day to reduce payload

### F.5 Deployment

**Q15: Database Backups**
- Automated backups or manual?
- Decision: Manual for MVP (deployment system responsibility)

**Q16: Log Rotation**
- Max log file size? Rotation policy?
- Decision: Use Python logging with RotatingFileHandler, 10MB max, 5 backups

**Q17: Health Check Endpoint**
- Should there be `/health` endpoint for monitoring?
- Decision: Yes, add `/health` that checks database connection

---

## G. LOGGING AND MONITORING STRATEGY

### G.1 Logging Configuration

**File:** `app/config/logging.py`

```python
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/backend.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'DEBUG'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/errors.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'ERROR'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file', 'error_file']
    },
    'loggers': {
        'app.services.polling_service': {
            'level': 'DEBUG'
        },
        'app.services.analysis_service': {
            'level': 'DEBUG'
        },
        'sqlalchemy.engine': {
            'level': 'WARNING'  # Suppress SQL logs in production
        }
    }
}
```

**Log Levels:**
- DEBUG: Detailed flow (polling cycles, reading counts)
- INFO: Normal operations (service started, summaries created)
- WARNING: Recoverable issues (queue full, skipped cycle)
- ERROR: Failures (database write failed, invalid data)
- CRITICAL: System-level issues (10 consecutive failures, disk full)

### G.2 Monitoring Metrics

**Health Check Endpoint:** `GET /health`

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T14:35:00",
  "checks": {
    "database": {
      "status": "ok",
      "response_time_ms": 12
    },
    "polling_service": {
      "status": "ok",
      "last_poll": "2026-04-05T14:34:55",
      "consecutive_failures": 0
    },
    "sse_broadcaster": {
      "status": "ok",
      "connected_clients": 3
    }
  },
  "uptime_seconds": 86400
}
```

**Metrics to Track (Future):**
- Poll cycle duration (should be <1s)
- Database connection pool usage
- SSE client count
- Alert creation rate
- API response times

### G.3 Recovery Procedures

**Database Connection Lost:**
1. Backend continues retrying with new connections from pool
2. Admin checks PostgreSQL status: `sudo systemctl status postgresql`
3. If PostgreSQL down, restart: `sudo systemctl restart postgresql`
4. Backend auto-recovers on next poll cycle

**Disk Full:**
1. Check disk usage: `df -h`
2. Run cleanup: `POST /api/v1/admin/cleanup-old-readings`
3. If still full, manually delete old backups or logs
4. Backend resumes writing once space available

**SSE Clients Not Receiving Updates:**
1. Check backend logs for SSE broadcast errors
2. Check client browser console for EventSource errors
3. Verify network connectivity
4. Restart backend if issue persists

**Alerts Not Triggering:**
1. Check analysis service logs for spike detection
2. Verify rolling average calculation has sufficient data
3. Check alert suppression logic (might be suppressing valid alerts)
4. Query database for recent spike conditions manually

---

**END OF TECHNICAL DESIGN**
