# Module 4: Analysis Service

## Status: ✅ COMPLETE

## What Was Built

The Analysis Service implements the core analytical algorithms for the energy monitoring system:
unknown load calculation, spike detection, and statistics aggregation.

### Files Created

1. **app/services/analysis_service.py** (240+ lines)
   - `AnalysisService` class with 4 main methods
   - Unknown load calculation with negative value support
   - Sustained spike detection with consecutive poll requirement
   - Hourly and daily statistics calculation

2. **tests/test_analysis.py** (350+ lines)
   - 8 comprehensive test scenarios
   - Tests all analysis algorithms
   - Edge cases: negative load, missing data, sustained vs transient spikes

3. **app/services/__init__.py** (Updated)
   - Added AnalysisService to exports

4. **verify_module4.sh**
   - Automated verification script

## Key Features Implemented

### 1. Unknown Load Calculation
```python
unknown = await analysis.calculate_unknown_load(
    main_meter_id=main_meter.id,
    smart_plug_ids=[plug1_id, plug2_id, plug3_id],
    minutes=5  # Look back 5 minutes
)
# Returns: Decimal (watts) or None if data unavailable
# Can be negative (per spec) if smart plugs report more than main meter
```

**Algorithm:**
- Gets latest readings for all devices within time window
- Unknown Load = Main Meter Power - Sum(Smart Plug Powers)
- Returns None if any device data is missing or stale
- Handles negative values (measurement variance)

**Edge Cases Handled:**
- Missing main meter reading → None
- Stale readings (older than window) → None
- Missing smart plug readings → None  
- Negative result → Returned as-is (per spec: "display it even if negative")

### 2. Spike Detection
```python
is_spike, baseline = await analysis.detect_spike(
    device_id=device.id,
    current_power=Decimal('5200'),
    spike_threshold=1.5,  # 50% above baseline
    baseline_minutes=10,
    min_consecutive_polls=2  # Must sustain for 2 polls (10 seconds)
)
```

**Algorithm:**
1. Get baseline from last 10 minutes (excluding most recent minute to avoid spike contamination)
2. Calculate baseline average (need ≥6 readings = 30 seconds of data)
3. Check if current_power > baseline_avg * threshold
4. Verify spike is sustained for ≥2 consecutive polls
5. Return (is_spike: bool, baseline: Decimal)

**Per Spec:**
- "Fire alert only if spike is near constant for 2 polls (only if the spike is near constant)"
- Prevents false positives from transient spikes
- Uses 1.5x threshold (configurable)

**Edge Cases:**
- Insufficient baseline data → (False, None)
- Transient spike (1 poll only) → (False, baseline)
- Sustained spike (2+ polls) → (True, baseline)

### 3. Hourly Statistics
```python
stats = await analysis.calculate_hourly_stats(
    device_id=device.id,
    hour_timestamp=datetime(2026, 4, 5, 14, 0, 0, tzinfo=IST)
)
# Returns: {'avg_power', 'max_power', 'min_power', 'total_kwh', 'reading_count'}
```

**Algorithm:**
- Get all readings for the hour
- Calculate min/max/avg power
- Calculate energy: kWh = sum(power_watts * 5 seconds) / 3600000
- Returns None if no readings

**Energy Calculation:**
- Each reading at 5-second intervals represents 5 seconds of consumption
- Total Watt-seconds = sum(power * 5)
- kWh = Watt-seconds / 3,600,000

### 4. Daily Statistics
```python
stats = await analysis.calculate_daily_stats(
    device_id=device.id,
    date=date(2026, 4, 5)
)
# Returns: {'total_kwh', 'avg_power', 'peak_hour'}
```

**Algorithm:**
- Get all hourly summaries for the day
- Sum total_kwh from all hours
- Calculate weighted average power (weighted by reading_count)
- Find peak hour (hour with highest avg_power)

## Design Decisions

### Why Exclude Recent Minute from Baseline?
When detecting a spike, if we include the spike itself in the baseline calculation, it artificially raises the baseline and makes the spike harder to detect. By excluding the most recent minute (12 readings @ 5s intervals), we ensure the baseline represents normal consumption before the spike.

### Why Require Consecutive Polls?
Per spec: "fire alert only if spike is near constant for 2 polls." This prevents false positives from:
- Single measurement errors
- Brief transient spikes (AC compressor starting, etc.)
- Network glitches

A real sustained spike (like a fault) will persist for multiple polls.

### Why Allow Negative Unknown Load?
Per spec answer to Q2: "Display it even if negative but label it clearly."

Negative unknown load can occur due to:
- Measurement variance between devices
- Calibration differences
- Timing skew (readings not perfectly synchronized)

The UI will handle labeling this appropriately.

### Energy Calculation Method
Using discrete summation rather than integration:
- Readings every 5 seconds
- Each reading = snapshot of instantaneous power
- Energy = sum(power_i × time_interval_i)  
- At fixed 5s intervals: E = (sum of powers) × 5s / 3,600,000

This is accurate for our poll rate and simpler than interpolation.

## Test Coverage

### Test Scenarios
1. ✅ Unknown load with positive result
2. ✅ Unknown load with negative result (measurement variance)
3. ✅ Unknown load returns None when data missing
4. ✅ Spike detection: no spike (normal variation)
5. ✅ Spike detection: sustained spike detected
6. ✅ Hourly stats: full hour of readings
7. ✅ Daily stats: 24 hours of summaries with peak detection

### Test Strategy
- Create realistic reading patterns
- Test edge cases (missing data, negative values)
- Verify algorithm correctness with known inputs
- Test timing-sensitive logic (sustained vs transient)

## Integration Points

### Used By (Future Modules)
- **Alert Service** → calls `detect_spike()` to trigger alerts
- **API Routes** → calls `calculate_unknown_load()` for dashboard
- **Background Tasks** → calls `calculate_hourly_stats()`, `calculate_daily_stats()` for summaries
- **SSE Stream** → provides unknown load in real-time updates

### Depends On
- **Storage Service** (Module 3) for all data queries ✅
- **Models** (Module 1) for Reading, HourlySummary types ✅

## Performance Considerations

### Query Efficiency
- `calculate_unknown_load()`: O(1) - uses `get_latest_readings_all_devices()` with optimized subquery
- `detect_spike()`: O(n) where n = baseline_minutes × 12 readings/min (typically ~120 readings)
- `calculate_hourly_stats()`: O(n) where n = 720 readings/hour
- `calculate_daily_stats()`: O(24) - operates on hourly summaries, not raw readings

### Memory Usage
- All operations work with in-memory lists of Decimal values
- Largest dataset: hourly stats (720 readings × ~50 bytes = ~36KB)
- No caching needed for MVP

### Database Load
- Most queries use indexed (device_id, timestamp) lookups
- Spike detection: 2 queries (baseline + recent)
- Stats calculation: 1 query per time period
- Acceptable for MVP with 4 devices polling at 5s intervals

## Known Limitations

1. **No Statistical Outlier Removal**
   - Baseline includes all readings without filtering outliers
   - Fine for simulated data, may need improvement with real hardware
   - Could add IQR-based outlier filtering if needed

2. **Fixed Spike Threshold**
   - Currently 1.5x baseline (50% increase)
   - Configurable but not device-specific
   - May need device-specific thresholds for different appliances

3. **No Trend Analysis**
   - Detects spikes but doesn't track trends over days/weeks
   - Acceptable for MVP
   - Could add trend detection in future versions

4. **Synchronous Calculation**
   - Stats are calculated on-demand, not pre-computed
   - Fine for MVP query load
   - Could move to background tasks for scale

## Acceptance Criteria Met

✅ **Unknown Load Calculation**
- Computes main_meter - sum(smart_plugs)  
- Returns None if data unavailable
- Displays negative values (per spec Q2)

✅ **Spike Detection Logic**
- Compares to baseline from last N minutes
- Requires sustained spike (2 consecutive polls per spec)
- Configurable threshold (default 1.5x)

✅ **Statistics Aggregation**
- Hourly: avg, min, max power; total kWh; reading count
- Daily: total kWh, avg power, peak hour
- Energy calculation accounts for 5s poll interval

## Next Steps

After Module 4 verification:
→ **Module 5: Alert Service** (alert creation with suppression logic)

