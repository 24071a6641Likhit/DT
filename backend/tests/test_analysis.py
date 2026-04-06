"""Tests for analysis service"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.analysis_service import AnalysisService
from app.services.storage_service import StorageService
from app.models import Device, Reading, HourlySummary


IST = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_calculate_unknown_load(session_factory):
    """Test unknown load calculation"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    # Create devices
    async with session_factory() as session:
        main_meter = Device(name="Main Meter", device_type="main_meter", is_active=True)
        plug1 = Device(name="AC", device_type="smart_plug", is_active=True)
        plug2 = Device(name="Geyser", device_type="smart_plug", is_active=True)
        plug3 = Device(name="Pump", device_type="smart_plug", is_active=True)
        session.add_all([main_meter, plug1, plug2, plug3])
        await session.commit()
        await session.refresh(main_meter)
        await session.refresh(plug1)
        await session.refresh(plug2)
        await session.refresh(plug3)
        
        main_id = main_meter.id
        plug_ids = [plug1.id, plug2.id, plug3.id]
    
    # Create readings
    now = datetime.now(IST)
    async with session_factory() as session:
        # Main meter: 5000W
        main_reading = Reading(
            device_id=main_id,
            timestamp=now,
            power_watts=Decimal('5000'),
            energy_kwh=Decimal('5.0')
        )
        # Plugs: AC=2000W, Geyser=1500W, Pump=800W = 4300W total
        plug_readings = [
            Reading(device_id=plug_ids[0], timestamp=now, power_watts=Decimal('2000'), energy_kwh=Decimal('2.0')),
            Reading(device_id=plug_ids[1], timestamp=now, power_watts=Decimal('1500'), energy_kwh=Decimal('1.5')),
            Reading(device_id=plug_ids[2], timestamp=now, power_watts=Decimal('800'), energy_kwh=Decimal('0.8')),
        ]
        session.add_all([main_reading] + plug_readings)
        await session.commit()
    
    # Calculate unknown load
    unknown = await analysis.calculate_unknown_load(main_id, plug_ids, minutes=5)
    
    # Unknown load = 5000 - 4300 = 700W
    assert unknown is not None
    assert unknown == Decimal('700')


@pytest.mark.asyncio
async def test_calculate_unknown_load_negative(session_factory):
    """Test unknown load can be negative (measurement variance)"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    async with session_factory() as session:
        main_meter = Device(name="Main", device_type="main_meter", is_active=True)
        plug = Device(name="Plug", device_type="smart_plug", is_active=True)
        session.add_all([main_meter, plug])
        await session.commit()
        await session.refresh(main_meter)
        await session.refresh(plug)
        main_id = main_meter.id
        plug_id = plug.id
    
    now = datetime.now(IST)
    async with session_factory() as session:
        # Smart plug reports more than main meter (measurement error)
        main_reading = Reading(device_id=main_id, timestamp=now, power_watts=Decimal('1000'), energy_kwh=Decimal('1.0'))
        plug_reading = Reading(device_id=plug_id, timestamp=now, power_watts=Decimal('1100'), energy_kwh=Decimal('1.1'))
        session.add_all([main_reading, plug_reading])
        await session.commit()
    
    unknown = await analysis.calculate_unknown_load(main_id, [plug_id], minutes=5)
    
    # Unknown = 1000 - 1100 = -100W (negative, as per spec)
    assert unknown == Decimal('-100')


@pytest.mark.asyncio
async def test_calculate_unknown_load_missing_data(session_factory):
    """Test unknown load returns None when data is missing"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    async with session_factory() as session:
        main_meter = Device(name="Main", device_type="main_meter", is_active=True)
        plug = Device(name="Plug", device_type="smart_plug", is_active=True)
        session.add_all([main_meter, plug])
        await session.commit()
        await session.refresh(main_meter)
        await session.refresh(plug)
        main_id = main_meter.id
        plug_id = plug.id
    
    # No readings created
    unknown = await analysis.calculate_unknown_load(main_id, [plug_id], minutes=5)
    
    # Should return None (no data)
    assert unknown is None


@pytest.mark.asyncio
async def test_detect_spike_no_spike(session_factory):
    """Test spike detection when power is normal"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    async with session_factory() as session:
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create baseline readings (stable at ~3000W)
    now = datetime.now(IST)
    async with session_factory() as session:
        readings = []
        for i in range(120):  # 10 minutes of data @ 5s intervals
            timestamp = now - timedelta(seconds=i * 5)
            readings.append(Reading(
                device_id=device_id,
                timestamp=timestamp,
                power_watts=Decimal('3000') + Decimal(str(i % 10)) - Decimal('5'),  # 2995-3005W variation
                energy_kwh=Decimal('3.0')
            ))
        session.add_all(readings)
        await session.commit()
    
    # Check for spike with current power = 3100W (normal increase, not a spike)
    is_spike, baseline = await analysis.detect_spike(device_id, Decimal('3100'))
    
    assert is_spike is False
    assert baseline is not None
    assert baseline > Decimal('2990')  # Should be around 3000
    assert baseline < Decimal('3010')


@pytest.mark.asyncio
async def test_detect_spike_sustained(session_factory):
    """Test spike detection when power spikes and sustains"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    async with session_factory() as session:
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id  # FIX: was device_id = device_id (typo)
    
    # Create baseline (stable at 3000W)
    now = datetime.now(IST)
    async with session_factory() as session:
        readings = []
        
        # Old baseline: 15 minutes ago to 2 minutes ago, all at 3000W
        for i in range(150, 24, -1):
            timestamp = now - timedelta(seconds=i * 5)
            readings.append(Reading(
                device_id=device_id,
                timestamp=timestamp,
                power_watts=Decimal('3000'),
                energy_kwh=Decimal('3.0')
            ))
        
        # Recent spike: last 15 seconds (3 readings) at 5000W
        for i in range(2, -1, -1):
            timestamp = now - timedelta(seconds=i * 5)
            readings.append(Reading(
                device_id=device_id,
                timestamp=timestamp,
                power_watts=Decimal('5000'),
                energy_kwh=Decimal('5.0')
            ))
        
        session.add_all(readings)
        await session.commit()
    
    # Check for spike with current power = 5000W
    # Threshold 1.5, so 3000 * 1.5 = 4500W needed to trigger
    # Current = 5000W > 4500W, and sustained for 2+ polls
    is_spike, baseline = await analysis.detect_spike(device_id, Decimal('5000'), min_consecutive_polls=2)
    
    assert is_spike is True
    assert baseline is not None
    assert baseline > Decimal('2990')
    assert baseline < Decimal('3010')


@pytest.mark.asyncio
async def test_calculate_hourly_stats(session_factory):
    """Test hourly statistics calculation"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    async with session_factory() as session:
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create one hour of readings
    hour_start = datetime(2026, 4, 5, 14, 0, 0, tzinfo=IST)
    async with session_factory() as session:
        readings = []
        # 720 readings in one hour @ 5s intervals
        for i in range(720):
            timestamp = hour_start + timedelta(seconds=i * 5)
            # Vary power between 2000-4000W
            power = Decimal('3000') + Decimal(str((i % 100) * 10))
            readings.append(Reading(
                device_id=device_id,
                timestamp=timestamp,
                power_watts=power,
                energy_kwh=power / Decimal('1000')
            ))
        session.add_all(readings)
        await session.commit()
    
    # Calculate stats
    stats = await analysis.calculate_hourly_stats(device_id, hour_start)
    
    assert stats is not None
    assert stats['reading_count'] == 720
    assert stats['min_power'] == Decimal('3000')
    assert stats['max_power'] == Decimal('3990')
    assert stats['avg_power'] > Decimal('3000')
    assert stats['avg_power'] < Decimal('4000')
    assert stats['total_kwh'] > Decimal('3')  # ~3.5 kWh for one hour at ~3500W avg


@pytest.mark.asyncio
async def test_calculate_daily_stats(session_factory):
    """Test daily statistics calculation from hourly summaries"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    
    async with session_factory() as session:
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create hourly summaries for a full day
    test_date = date(2026, 4, 5)
    async with session_factory() as session:
        summaries = []
        for hour in range(24):
            timestamp = datetime(2026, 4, 5, hour, 0, 0, tzinfo=IST)
            # Peak during evening hours (18-23)
            avg_power = Decimal('5000') if 18 <= hour < 23 else Decimal('3000')
            summaries.append(HourlySummary(
                device_id=device_id,
                hour_timestamp=timestamp,
                avg_power_watts=avg_power,
                max_power_watts=avg_power + Decimal('500'),
                min_power_watts=avg_power - Decimal('500'),
                total_kwh=avg_power / Decimal('1000'),  # 1 hour at avg_power
                reading_count=720
            ))
        session.add_all(summaries)
        await session.commit()
    
    # Calculate daily stats
    stats = await analysis.calculate_daily_stats(device_id, test_date)
    
    assert stats is not None
    # Total: 19 hours @ 3kWh + 5 hours @ 5kWh = 57 + 25 = 82 kWh
    assert stats['total_kwh'] == Decimal('82')
    # Peak hour should be in range 18-23
    assert 18 <= stats['peak_hour'] < 23
    # Average should be weighted average
    assert stats['avg_power'] > Decimal('3000')
    assert stats['avg_power'] < Decimal('5000')
