"""Tests for alert service"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.alert_service import AlertService
from app.services.storage_service import StorageService
from app.services.analysis_service import AnalysisService
from app.models import Device, Reading, Alert


IST = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_spike_alert_creation(session_factory):
    """Test that spike alert is created when spike detected"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    # Create device
    async with session_factory() as session:
        device = Device(name="Test Device", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create baseline readings (stable at 3000W)
    now = datetime.now(IST)
    async with session_factory() as session:
        readings = []
        # Old baseline: 3000W for 15 minutes
        for i in range(180, 24, -1):
            timestamp = now - timedelta(seconds=i * 5)
            readings.append(Reading(
                device_id=device_id,
                timestamp=timestamp,
                power_watts=Decimal('3000'),
                energy_kwh=Decimal('3.0')
            ))
        # Recent spike: 5000W for last 15 seconds (3 readings)
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
    
    # Check and create alerts
    alerts = await alert_service.check_and_create_alerts(
        device_id=device_id,
        device_name="Test Device",
        current_power=Decimal('5000')
    )
    
    assert len(alerts) >= 1
    spike_alert = next((a for a in alerts if a.alert_type == "spike"), None)
    assert spike_alert is not None
    assert spike_alert.severity == "warning"
    assert spike_alert.is_acknowledged is False
    assert "spike detected" in spike_alert.message.lower()
    assert spike_alert.actual_value == Decimal('5000')


@pytest.mark.asyncio
async def test_spike_alert_suppression(session_factory):
    """Test that spike alerts are suppressed within suppression window"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    async with session_factory() as session:
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create baseline and spike readings
    now = datetime.now(IST)
    async with session_factory() as session:
        readings = []
        for i in range(180, 0, -1):
            timestamp = now - timedelta(seconds=i * 5)
            power = Decimal('5000') if i < 24 else Decimal('3000')
            readings.append(Reading(
                device_id=device_id,
                timestamp=timestamp,
                power_watts=power,
                energy_kwh=power / Decimal('1000')
            ))
        session.add_all(readings)
        await session.commit()
    
    # Create first spike alert manually
    async with session_factory() as session:
        first_alert = Alert(
            device_id=device_id,
            timestamp=now - timedelta(minutes=5),  # 5 minutes ago
            alert_type="spike",
            severity="warning",
            message="First spike",
            is_acknowledged=False
        )
        session.add(first_alert)
        await session.commit()
    
    # Try to create another spike alert (should be suppressed)
    alerts = await alert_service.check_and_create_alerts(
        device_id=device_id,
        device_name="Test",
        current_power=Decimal('5000')
    )
    
    spike_alerts = [a for a in alerts if a.alert_type == "spike"]
    assert len(spike_alerts) == 0  # Suppressed due to recent alert


@pytest.mark.asyncio
async def test_overload_alert_creation(session_factory):
    """Test that overload alert is created when power exceeds threshold"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    async with session_factory() as session:
        device = Device(name="Main Meter", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create baseline (not needed for overload, but good practice)
    now = datetime.now(IST)
    async with session_factory() as session:
        reading = Reading(
            device_id=device_id,
            timestamp=now,
            power_watts=Decimal('6800'),  # Above 6400W threshold
            energy_kwh=Decimal('6.8')
        )
        session.add(reading)
        await session.commit()
    
    # Check alerts with high power
    alerts = await alert_service.check_and_create_alerts(
        device_id=device_id,
        device_name="Main Meter",
        current_power=Decimal('6800')
    )
    
    overload_alerts = [a for a in alerts if a.alert_type == "overload"]
    assert len(overload_alerts) == 1
    assert overload_alerts[0].severity == "warning"
    assert "high power consumption" in overload_alerts[0].message.lower()
    assert overload_alerts[0].actual_value == Decimal('6800')


@pytest.mark.asyncio
async def test_overload_critical_severity(session_factory):
    """Test that overload becomes critical above 7200W (90% of 8kW)"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    async with session_factory() as session:
        device = Device(name="Main", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Check with very high power (>90% of limit)
    alerts = await alert_service.check_and_create_alerts(
        device_id=device_id,
        device_name="Main",
        current_power=Decimal('7500')  # 93.75% of 8kW
    )
    
    overload_alerts = [a for a in alerts if a.alert_type == "overload"]
    assert len(overload_alerts) == 1
    assert overload_alerts[0].severity == "critical"


@pytest.mark.asyncio
async def test_high_consumption_alert(session_factory):
    """Test high consumption alert for hourly usage"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    async with session_factory() as session:
        device = Device(name="Main", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Check with high hourly consumption (>20 kWh threshold)
    alert = await alert_service.check_high_consumption_alert(
        device_id=device_id,
        device_name="Main",
        hourly_kwh=Decimal('25.5')
    )
    
    assert alert is not None
    assert alert.alert_type == "high_consumption"
    assert alert.severity == "info"
    assert "25.5" in alert.message
    assert alert.actual_value == Decimal('25.5')


@pytest.mark.asyncio
async def test_acknowledge_alert(session_factory):
    """Test alert acknowledgment"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    # Create alert
    now = datetime.now(IST)
    async with session_factory() as session:
        alert = Alert(
            timestamp=now,
            alert_type="spike",
            severity="warning",
            message="Test alert",
            is_acknowledged=False
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        alert_id = alert.id
    
    # Acknowledge it
    acknowledged = await alert_service.acknowledge_alert(alert_id)
    
    assert acknowledged is not None
    assert acknowledged.is_acknowledged is True
    assert acknowledged.acknowledged_at is not None


@pytest.mark.asyncio
async def test_get_active_alerts(session_factory):
    """Test getting active (unacknowledged) alerts"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    now = datetime.now(IST)
    async with session_factory() as session:
        device = Device(name="Test", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create mix of acknowledged and unacknowledged alerts
    async with session_factory() as session:
        alerts = [
            Alert(
                device_id=device_id,
                timestamp=now,
                alert_type="spike",
                severity="warning",
                message="Alert 1",
                is_acknowledged=False
            ),
            Alert(
                device_id=device_id,
                timestamp=now,
                alert_type="overload",
                severity="critical",
                message="Alert 2",
                is_acknowledged=False
            ),
            Alert(
                device_id=device_id,
                timestamp=now,
                alert_type="spike",
                severity="warning",
                message="Alert 3",
                is_acknowledged=True,
                acknowledged_at=now
            ),
        ]
        session.add_all(alerts)
        await session.commit()
    
    # Get active alerts
    active = await alert_service.get_active_alerts()
    
    assert len(active) >= 2  # At least our 2 unacknowledged alerts
    assert all(not a.is_acknowledged for a in active)
    
    # Filter by severity
    critical = await alert_service.get_active_alerts(severity="critical")
    assert len(critical) >= 1
    assert all(a.severity == "critical" for a in critical)


@pytest.mark.asyncio
async def test_get_alert_count(session_factory):
    """Test getting count of unacknowledged alerts"""
    storage = StorageService(session_factory)
    analysis = AnalysisService(storage)
    alert_service = AlertService(storage, analysis)
    
    now = datetime.now(IST)
    async with session_factory() as session:
        alerts = [
            Alert(timestamp=now, alert_type="spike", severity="warning", message="A1", is_acknowledged=False),
            Alert(timestamp=now, alert_type="spike", severity="warning", message="A2", is_acknowledged=False),
            Alert(timestamp=now, alert_type="spike", severity="warning", message="A3", is_acknowledged=True, acknowledged_at=now),
        ]
        session.add_all(alerts)
        await session.commit()
    
    count = await alert_service.get_alert_count()
    assert count >= 2  # At least our 2 unacknowledged alerts
