"""Analysis service for power consumption analysis"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from app.models import Reading
from app.services.storage_service import StorageService


class AnalysisService:
    """Analyzes power consumption data for unknown load and spikes"""
    
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.ist = ZoneInfo("Asia/Kolkata")
    
    async def calculate_unknown_load(
        self,
        main_meter_id: str,
        smart_plug_ids: List[str],
        minutes: int = 5
    ) -> Optional[Decimal]:
        """
        Calculate unknown load for the last N minutes.
        
        Unknown load = main meter power - sum(smart plugs power)
        Can be negative if smart plugs report more than main meter (measurement variance)
        
        Args:
            main_meter_id: UUID of main meter device (as string)
            smart_plug_ids: List of UUIDs for smart plug devices (as strings)
            minutes: Time window to analyze (default 5 minutes)
            
        Returns:
            Unknown load in watts, or None if data unavailable
        """
        # FIX: Convert string UUIDs to UUID objects for comparison
        main_meter_uuid = UUID(main_meter_id)
        smart_plug_uuids = [UUID(pid) for pid in smart_plug_ids]
        
        # Get latest readings for all devices
        latest_readings_dict = await self.storage.get_latest_readings_all_devices()
        latest_readings = list(latest_readings_dict.values())  # FIX: Convert dict to list
        
        # Find main meter reading
        main_reading = next(
            (r for r in latest_readings if r.device_id == main_meter_uuid),
            None
        )
        if not main_reading:
            return None
        
        # Check if main meter reading is recent enough
        # FIX: Use naive datetime since DB stores timezone=False
        # DB stores timestamps as IST naive, so compare against naive IST
        now_ist = datetime.now(self.ist).replace(tzinfo=None)
        cutoff = now_ist - timedelta(minutes=minutes)
        if main_reading.timestamp < cutoff:
            return None
        
        # Get smart plug readings
        plug_readings = [
            r for r in latest_readings
            if r.device_id in smart_plug_uuids and r.timestamp >= cutoff
        ]
        
        # Need all plugs to report
        if len(plug_readings) != len(smart_plug_ids):
            return None
        
        # Calculate total smart plug consumption
        total_plugs = sum(r.power_watts for r in plug_readings)
        
        # Unknown load = main - sum(plugs)
        unknown = main_reading.power_watts - total_plugs
        
        return unknown
    
    async def detect_spike(
        self,
        device_id: str,
        current_power: Decimal,
        spike_threshold: float = 1.5,
        baseline_minutes: int = 10,
        min_consecutive_polls: int = 2
    ) -> Tuple[bool, Optional[Decimal]]:
        """
        Detect power spike by comparing to recent baseline.
        
        A spike is detected if:
        1. Current power > threshold * baseline_average
        2. Spike persists for at least min_consecutive_polls (prevents false positives from transient spikes)
        
        Per spec: Fire alert only if spike is near constant for 2 polls (10 seconds)
        
        Args:
            device_id: Device to analyze
            current_power: Current power reading in watts
            spike_threshold: Multiplier over baseline (default 1.5 = 50% increase)
            baseline_minutes: Minutes of history for baseline (default 10)
            min_consecutive_polls: Minimum consecutive high readings needed (default 2)
            
        Returns:
            Tuple of (is_spike, baseline_power)
            - is_spike: True if spike detected
            - baseline_power: Average baseline power, or None if no baseline
        """
        # Get recent readings for baseline (excluding very recent ones to avoid including spike)
        # Look back baseline_minutes + 1 to exclude current reading
        baseline_readings = await self.storage.get_recent_readings(
            device_id,
            minutes=baseline_minutes + 1
        )
        
        if len(baseline_readings) < 6:  # Need at least 30 seconds of data (6 readings @ 5s interval)
            return False, None
        
        # Exclude the most recent minute to avoid spike contaminating baseline
        # (at 5s intervals, 12 readings = 1 minute)
        baseline_readings = baseline_readings[12:]
        
        if len(baseline_readings) < 6:
            return False, None
        
        # Calculate baseline average
        baseline_avg = sum(r.power_watts for r in baseline_readings) / len(baseline_readings)
        
        # Check if current exceeds threshold
        if current_power <= baseline_avg * Decimal(str(spike_threshold)):
            return False, baseline_avg
        
        # Check consecutive high readings
        # Get last few readings to see if spike is sustained
        very_recent = await self.storage.get_recent_readings(device_id, minutes=1)
        
        if len(very_recent) < min_consecutive_polls:
            # Not enough recent data to confirm
            return False, baseline_avg
        
        # Count consecutive readings above threshold
        consecutive_count = 0
        threshold_power = baseline_avg * Decimal(str(spike_threshold))
        
        for reading in very_recent[:min_consecutive_polls]:
            if reading.power_watts > threshold_power:
                consecutive_count += 1
            else:
                break
        
        is_spike = consecutive_count >= min_consecutive_polls
        
        return is_spike, baseline_avg
    
    async def calculate_hourly_stats(
        self,
        device_id: str,
        hour_timestamp: datetime
    ) -> Optional[dict]:
        """
        Calculate statistics for a specific hour.
        
        Args:
            device_id: Device to analyze
            hour_timestamp: Start of the hour to analyze (should be on the hour)
            
        Returns:
            Dict with keys: avg_power, max_power, min_power, total_kwh, reading_count
            Or None if no data available
        """
        # Get readings for the hour
        start_time = hour_timestamp.replace(minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        readings = await self.storage.get_readings_range(
            device_id,
            start_time,
            end_time
        )
        
        if not readings:
            return None
        
        powers = [r.power_watts for r in readings]
        
        # Calculate energy: sum of (power * time_interval)
        # At 5-second intervals, each reading represents 5 seconds of consumption
        # kWh = sum(kW * hours) = sum(W * seconds) / (1000 * 3600)
        total_watt_seconds = sum(p * Decimal('5') for p in powers)
        total_kwh = total_watt_seconds / Decimal('3600000')  # Convert Ws to kWh
        
        return {
            'avg_power': sum(powers) / len(powers),
            'max_power': max(powers),
            'min_power': min(powers),
            'total_kwh': total_kwh,
            'reading_count': len(readings)
        }
    
    async def calculate_daily_stats(
        self,
        device_id: str,
        target_date: date
    ) -> Optional[dict]:
        """
        Calculate statistics for a full day using hourly summaries.
        
        Args:
            device_id: Device to analyze
            target_date: Date to analyze
            
        Returns:
            Dict with keys: total_kwh, avg_power, peak_hour
            Or None if no data available
        """
        # Get all hourly summaries for the day
        summaries = await self.storage.get_hourly_summaries_for_day(device_id, target_date)
        
        if not summaries:
            return None
        
        # Sum up total energy
        total_kwh = sum(s.total_kwh for s in summaries)
        
        # Calculate weighted average power (weight by reading count)
        total_power_weighted = sum(
            s.avg_power_watts * s.reading_count
            for s in summaries
        )
        total_readings = sum(s.reading_count for s in summaries)
        avg_power = total_power_weighted / total_readings if total_readings > 0 else Decimal('0')
        
        # Find peak hour (hour with highest average power)
        peak_summary = max(summaries, key=lambda s: s.avg_power_watts)
        peak_hour = peak_summary.hour_timestamp.hour
        
        return {
            'total_kwh': total_kwh,
            'avg_power': avg_power,
            'peak_hour': peak_hour
        }
