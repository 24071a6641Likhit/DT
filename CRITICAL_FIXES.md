# Critical Fixes Required - System Won't Start

## A. BLOCKING ISSUES (System won't boot)

### A1. Orchestrator Constructor Mismatch ✗ CRITICAL
**File:** `backend/app/services/orchestrator.py:30-32`
**Problem:** 
```python
self.analysis = AnalysisService(session_factory)  # WRONG - expects StorageService
self.alert_service = AlertService(session_factory, self.analysis)  # WRONG - expects (StorageService, AnalysisService)
```
**Fix:** Pass StorageService instance, not session_factory

### A2. EnergySimulator Constructor Mismatch ✗ CRITICAL
**File:** `backend/app/services/orchestrator.py:46-51`
**Problem:** Passes keyword arguments (main_meter_id, ac_id, etc.)
**Reality:** `backend/app/simulator/energy_simulator.py:257` expects `devices: List[Dict]`
**Fix:** Pass list of device dicts

### A3. PollingService.add_callback() Doesn't Exist ✗ CRITICAL
**File:** `backend/app/services/orchestrator.py:58`
**Problem:** Tries to call `polling_service.add_callback()` but constructor needs callback
**Fix:** Pass callback in PollingService constructor

### A4. Alert Type Enum Violation ✗ CRITICAL  
**File:** `backend/app/models/alert.py:38` CHECK constraint only allows: spike, high_overnight, long_runtime, bill_threshold
**Reality:** `backend/app/services/alert_service.py:145` writes 'overload', line 189 writes 'high_consumption'
**Fix:** Update database constraint or change alert type names in code

### A5. Device Type Mismatch ✗ CRITICAL
**Seed data:** Inserts device_type='smart_plug' (generic)
**Orchestrator expects:** device_type in ('smart_plug_ac', 'smart_plug_geyser', 'smart_plug_pump')
**Fix:** Use specific device_type values or fix lookup logic

### A6. StorageService.get_alerts() Signature Mismatch ✗ CRITICAL
**Definition:** `backend/app/services/storage_service.py:239` accepts (is_acknowledged, alert_type, start_date, end_date, limit)
**Usage:** 
- Line 226 calls with (device_id, alert_type, since, limit) - device_id and since DON'T EXIST
- Line 262 calls with (device_id, is_acknowledged, severity) - severity DOESN'T EXIST
**Fix:** Update method signature to match all usages

### A7. get_latest_readings_all_devices() Returns Dict, Iteration Assumes List ✗ CRITICAL
**Returns:** `Dict[UUID, Reading]`
**Usage:** `backend/app/services/analysis_service.py:43` and dashboard route iterate like it's a list
**Fix:** Either change return type or fix iteration

## B. CONTRACT MISMATCHES (Will error at runtime)

### B1. Frontend/Backend Alert Field Naming
**Frontend expects:** `acknowledged`, `value`, `threshold`
**Backend returns:** `is_acknowledged`, `actual_value`, `threshold_value`

### B2. Dashboard API Contract Mismatch
**Frontend:** `api.getRecentReadings(30)` - no device_id
**Backend:** `/api/dashboard/recent` requires device_id query param

### B3. Billing API Field Mismatches
**Frontend expects:** Fields that billing API doesn't return

### B4. Settings API Doesn't Persist
**Problem:** Creates new BillingService per request, mutations don't persist

## C. PRODUCTION DEPLOYMENT ISSUES

### C1. Multi-worker Will Duplicate Everything
**File:** `backend/start_production.sh:18` uses `--workers 2`
**Problem:** Each worker runs orchestrator, duplicate polling, duplicate alerts, SSE clients split

### C2. Timezone Inconsistency
**DB:** DateTime(timezone=False)
**Code:** Uses timezone-aware IST datetime objects

## SEVERITY CLASSIFICATION

**STOP-SHIP (system won't start):**
- A1, A2, A3, A4, A5, A6, A7

**WILL-FAIL-IN-USE (runtime errors after start):**
- B1, B2, B3, B4

**PRODUCTION-ONLY (dev works, prod fails):**
- C1, C2

## FIX PRIORITY

1. Fix orchestrator service instantiation (A1)
2. Fix simulator instantiation (A2)  
3. Fix polling service callback (A3)
4. Fix alert type constraint (A4)
5. Fix device type lookup (A5)
6. Fix storage service signatures (A6)
7. Fix dict/list iteration (A7)
8. Test full startup cycle
9. Fix API contracts (B1-B4)
10. Fix deployment config (C1)
