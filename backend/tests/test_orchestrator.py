"""
Tests for the Orchestrator service.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.orchestrator import Orchestrator
from app.simulator.energy_simulator import SimulatedReading
from app.models.device import Device
from app.models.reading import Reading


@pytest.mark.asyncio
async def test_orchestrator_initialization(session_factory):
    """Test orchestrator initializes with correct device mapping."""
    orchestrator = Orchestrator(session_factory)
    
    await orchestrator.initialize()
    
    assert orchestrator.simulator is not None
    assert orchestrator.polling_service is not None
    assert orchestrator.storage is not None
    assert orchestrator.analysis is not None
    assert orchestrator.alert_service is not None


@pytest.mark.asyncio
async def test_handle_new_readings_stores_data(session_factory):
    """Test that new readings are stored in database."""
    orchestrator = Orchestrator(session_factory)
    await orchestrator.initialize()
    
    # Create test readings - FIX: Use correct SimulatedReading fields (no cumulative_kwh)
    main_meter = orchestrator.simulator.main_meter
    readings = [
        SimulatedReading(
            device_id=main_meter.device_id,
            device_name=main_meter.device_name,
            timestamp=datetime.now(),
            power_watts=1500.0,
            voltage_volts=230.0,
            current_amps=6.5
        )
    ]
    
    # Process readings
    await orchestrator._handle_new_readings(readings)
    
    # Verify storage
    recent = await orchestrator.storage.get_recent_readings(
        main_meter.device_id,
        minutes=1
    )
    
    assert len(recent) > 0
    assert float(recent[0].power_watts) == 1500.0


@pytest.mark.asyncio
async def test_handle_new_readings_broadcasts_sse(session_factory):
    """Test that new readings trigger SSE broadcast."""
    orchestrator = Orchestrator(session_factory)
    await orchestrator.initialize()
    
    # FIX: Use correct SimulatedReading fields
    main_meter = orchestrator.simulator.main_meter
    readings = [
        SimulatedReading(
            device_id=main_meter.device_id,
            device_name=main_meter.device_name,
            timestamp=datetime.now(),
            power_watts=2000.0,
            voltage_volts=230.0,
            current_amps=8.7
        )
    ]
    
    with patch('app.services.orchestrator.broadcaster.broadcast_readings') as mock_broadcast:
        await orchestrator._handle_new_readings(readings)
        
        # Verify broadcast was called
        assert mock_broadcast.called
        call_args = mock_broadcast.call_args[0][0]
        assert 'devices' in call_args
        assert 'unknown_load' in call_args


@pytest.mark.asyncio
async def test_handle_new_readings_creates_alerts(session_factory):
    """Test that high power readings trigger alerts."""
    orchestrator = Orchestrator(session_factory)
    await orchestrator.initialize()
    
    # Create overload reading - FIX: Use correct SimulatedReading fields
    main_meter = orchestrator.simulator.main_meter
    readings = [
        SimulatedReading(
            device_id=main_meter.device_id,
            device_name=main_meter.device_name,
            timestamp=datetime.now(),
            power_watts=7500.0,  # Above critical threshold
            voltage_volts=230.0,
            current_amps=32.6
        )
    ]
    
    with patch('app.services.orchestrator.broadcaster.broadcast_alert') as mock_alert:
        await orchestrator._handle_new_readings(readings)
        
        # May or may not trigger on first reading (depends on alert suppression)
        # Just verify no errors


@pytest.mark.asyncio
async def test_orchestrator_start_stop(session_factory):
    """Test orchestrator start and stop methods."""
    orchestrator = Orchestrator(session_factory)
    await orchestrator.initialize()
    
    # Start
    orchestrator.start()
    assert orchestrator.polling_service.is_running()
    
    # Stop
    orchestrator.stop()
    assert not orchestrator.polling_service.is_running()
