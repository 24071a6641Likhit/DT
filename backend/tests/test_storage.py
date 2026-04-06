"""Tests for storage service"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.storage_service import StorageService
from app.simulator.energy_simulator import SimulatedReading
from app.models import Device, Reading, Alert


@pytest.mark.asyncio
async def test_write_readings_batch(session_factory):
    """Test writing batch of readings"""
    storage_service = StorageService(session_factory)
    
    # Create test device
    async with session_factory() as session:
        device = Device(name="Test Device", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create simulated readings
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    readings = [
        SimulatedReading(
            device_id=device_id,
            device_name="Test Device",
            timestamp=now,
            power_watts=1500.50,
            voltage_volts=230.0,
            current_amps=6.52
        ),
        SimulatedReading(
            device_id=device_id,
            device_name="Test Device",
            timestamp=now + timedelta(seconds=5),
            power_watts=1520.75,
            voltage_volts=229.5,
            current_amps=6.62
        )
    ]
    
    await storage_service.write_readings_batch(readings)
    
    # Verify readings were written
    async with session_factory() as session:
        from sqlalchemy import select
        stmt = select(Reading).where(Reading.device_id == device_id)
        result = await session.execute(stmt)
        saved_readings = result.scalars().all()
        
        assert len(saved_readings) == 2
        assert saved_readings[0].power_watts == Decimal("1500.50")
        assert saved_readings[1].power_watts == Decimal("1520.75")


@pytest.mark.asyncio
async def test_get_devices(session_factory):
    """Test getting devices"""
    storage_service = StorageService(session_factory)
    
    async with session_factory() as session:
        # Create test devices
        device1 = Device(name="Active Device", device_type="main_meter", is_active=True)
        device2 = Device(name="Inactive Device", device_type="smart_plug", is_active=False)
        session.add_all([device1, device2])
        await session.commit()
    
    # Get active devices
    devices = await storage_service.get_devices(active_only=True)
    assert len(devices) >= 1
    assert all(d.is_active for d in devices)
    
    # Get all devices
    all_devices = await storage_service.get_devices(active_only=False)
    assert len(all_devices) >= 2


@pytest.mark.asyncio
async def test_create_and_acknowledge_alert(session_factory):
    """Test creating and acknowledging alert"""
    storage_service = StorageService(session_factory)
    
    async with session_factory() as session:
        # Create device
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        device_id = device.id
    
    # Create alert
    alert = await storage_service.create_alert(
        device_id=device_id,
        alert_type="spike",
        severity="warning",
        message="Test spike alert",
        threshold_value=3200.0,
        actual_value=5200.0
    )
    
    assert alert.id is not None
    assert alert.alert_type == "spike"
    assert alert.severity == "warning"
    assert alert.is_acknowledged is False
    assert alert.actual_value == Decimal("5200.0")
    
    # Acknowledge alert
    acknowledged = await storage_service.acknowledge_alert(alert.id)
    assert acknowledged.is_acknowledged is True
    assert acknowledged.acknowledged_at is not None


@pytest.mark.asyncio
async def test_get_unacknowledged_alert_count(session_factory):
    """Test counting unacknowledged alerts"""
    storage_service = StorageService(session_factory)
    
    async with session_factory() as session:
        # Create alerts
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        alert1 = Alert(
            timestamp=now,
            alert_type="spike",
            severity="warning",
            message="Alert 1",
            is_acknowledged=False
        )
        alert2 = Alert(
            timestamp=now,
            alert_type="spike",
            severity="warning",
            message="Alert 2",
            is_acknowledged=False
        )
        session.add_all([alert1, alert2])
        await session.commit()
    
    # Get count
    count = await storage_service.get_unacknowledged_alert_count()
    assert count >= 2  # At least our 2 unacknowledged alerts


@pytest.mark.asyncio
async def test_create_summaries(session_factory):
    """Test creating hourly and daily summaries"""
    storage_service = StorageService(session_factory)
    
    async with session_factory() as session:
        # Create device
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        device_id = device.id
    
    # Create hourly summary
    hour_time = datetime(2026, 4, 5, 14, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    hourly = await storage_service.create_hourly_summary(
        device_id=device_id,
        hour_timestamp=hour_time,
        avg_power=3200.50,
        max_power=4500.00,
        min_power=2100.00,
        total_kwh=3.2,
        reading_count=720
    )
    
    assert hourly.id is not None
    assert hourly.avg_power_watts == Decimal("3200.50")
    assert hourly.reading_count == 720
    
    # Create daily summary
    daily = await storage_service.create_daily_summary(
        device_id=device_id,
        summary_date=date(2026, 4, 5),
        total_kwh=68.5,
        avg_power=2854.17,
        peak_hour=20,
        estimated_cost=512.25
    )
    
    assert daily.id is not None
    assert daily.total_kwh == Decimal("68.5")
    assert daily.peak_hour == 20
    assert daily.estimated_cost_inr == Decimal("512.25")

