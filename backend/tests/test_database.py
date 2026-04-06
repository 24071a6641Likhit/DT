"""Tests for database models and schema"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, Reading, HourlySummary, DailySummary, Alert


@pytest.mark.asyncio
async def test_device_model(db_session: AsyncSession):
    """Test Device model creation and retrieval"""
    device = Device(
        name="Test Device",
        device_type="main_meter",
        location="Test Location",
        is_active=True
    )
    
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    
    assert device.id is not None
    assert device.name == "Test Device"
    assert device.device_type == "main_meter"
    assert device.is_active is True
    assert device.created_at is not None


@pytest.mark.asyncio
async def test_reading_model(db_session: AsyncSession):
    """Test Reading model with foreign key relationship"""
    # Create device first
    device = Device(
        name="Test Meter",
        device_type="main_meter",
        is_active=True
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    
    # Create reading
    reading = Reading(
        device_id=device.id,
        timestamp=datetime.now(),
        power_watts=Decimal("1500.50"),
        voltage_volts=Decimal("230.0"),
        current_amps=Decimal("6.52"),
        energy_kwh=Decimal("10.5")
    )
    
    db_session.add(reading)
    await db_session.commit()
    await db_session.refresh(reading)
    
    assert reading.id is not None
    assert reading.device_id == device.id
    assert reading.power_watts == Decimal("1500.50")
    
    # Test relationship
    stmt = select(Reading).where(Reading.id == reading.id)
    result = await db_session.execute(stmt)
    retrieved_reading = result.scalar_one()
    
    assert retrieved_reading.device.name == "Test Meter"


@pytest.mark.asyncio
async def test_hourly_summary_model(db_session: AsyncSession):
    """Test HourlySummary model"""
    device = Device(name="Test", device_type="main_meter", is_active=True)
    db_session.add(device)
    await db_session.commit()
    
    summary = HourlySummary(
        device_id=device.id,
        hour_timestamp=datetime(2026, 4, 5, 14, 0, 0),
        avg_power_watts=Decimal("3200.50"),
        max_power_watts=Decimal("4500.00"),
        min_power_watts=Decimal("2100.00"),
        total_kwh=Decimal("3.2"),
        reading_count=720
    )
    
    db_session.add(summary)
    await db_session.commit()
    
    assert summary.id is not None
    assert summary.avg_power_watts == Decimal("3200.50")


@pytest.mark.asyncio
async def test_daily_summary_model(db_session: AsyncSession):
    """Test DailySummary model with peak_hour constraint"""
    device = Device(name="Test", device_type="main_meter", is_active=True)
    db_session.add(device)
    await db_session.commit()
    
    summary = DailySummary(
        device_id=device.id,
        date=date(2026, 4, 5),
        total_kwh=Decimal("68.5"),
        avg_power_watts=Decimal("2854.17"),
        peak_hour=20,
        estimated_cost_inr=Decimal("512.25")
    )
    
    db_session.add(summary)
    await db_session.commit()
    
    assert summary.id is not None
    assert summary.peak_hour == 20
    assert summary.total_kwh == Decimal("68.5")


@pytest.mark.asyncio
async def test_alert_model(db_session: AsyncSession):
    """Test Alert model with check constraints"""
    device = Device(name="Test", device_type="main_meter", is_active=True)
    db_session.add(device)
    await db_session.commit()
    
    alert = Alert(
        device_id=device.id,
        timestamp=datetime.now(),
        alert_type="spike",
        severity="warning",
        message="Test spike alert",
        threshold_value=Decimal("3200.0"),
        actual_value=Decimal("5200.0"),
        is_acknowledged=False
    )
    
    db_session.add(alert)
    await db_session.commit()
    
    assert alert.id is not None
    assert alert.alert_type == "spike"
    assert alert.severity == "warning"
    assert alert.is_acknowledged is False


@pytest.mark.asyncio
async def test_cascade_delete(db_session: AsyncSession):
    """Test cascade delete behavior"""
    device = Device(name="Test", device_type="main_meter", is_active=True)
    db_session.add(device)
    await db_session.commit()
    device_id = device.id
    
    # Add readings
    reading = Reading(
        device_id=device_id,
        timestamp=datetime.now(),
        power_watts=Decimal("1000.0"),
        energy_kwh=Decimal("1.0")
    )
    db_session.add(reading)
    await db_session.commit()
    
    # Delete device
    await db_session.delete(device)
    await db_session.commit()
    
    # Verify readings are also deleted (CASCADE)
    stmt = select(Reading).where(Reading.device_id == device_id)
    result = await db_session.execute(stmt)
    readings = result.scalars().all()
    
    assert len(readings) == 0
