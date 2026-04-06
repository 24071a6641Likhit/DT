"""
Orchestrator service that coordinates all backend components.
Manages the data flow: Polling -> Storage -> Analysis -> Alerts -> Broadcasting.
"""
import asyncio
import logging
from typing import List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.simulator.energy_simulator import EnergySimulator, SimulatedReading
from .polling_service import PollingService
from .storage_service import StorageService
from .analysis_service import AnalysisService
from .alert_service import AlertService
from .sse_broadcaster import broadcaster

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates all backend services and manages data flow."""
    
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory
        
        # Initialize services
        self.simulator = None  # Will be initialized with device IDs
        self.polling_service = None
        self.storage = StorageService(session_factory)
        self.analysis = AnalysisService(self.storage)  # FIX: Pass StorageService
        self.alert_service = AlertService(self.storage, self.analysis)  # FIX: Pass StorageService
        
    async def initialize(self):
        """Initialize simulator with device IDs from database."""
        try:
            # Get devices from database
            devices = await self.storage.get_devices()
            
            if len(devices) != 4:
                raise ValueError(f"Expected 4 devices, found {len(devices)}")
                
            # Prepare device list for simulator (expects List[Dict])
            device_list = []
            for device in devices:
                device_list.append({
                    'id': device.id,
                    'name': device.name,
                    'device_type': device.device_type
                })
            
            # FIX: Pass list of device dicts
            self.simulator = EnergySimulator(devices=device_list)
            
            # FIX: Pass callback in constructor (add_callback doesn't exist)
            self.polling_service = PollingService(
                simulator=self.simulator,
                callback=self._handle_new_readings,
                interval_seconds=5
            )
            
            logger.info("Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
            
    async def _handle_new_readings(self, readings: List[SimulatedReading]):
        """
        Process new readings from the polling service.
        This is the main data flow pipeline.
        """
        try:
            # Step 1: Store readings in database
            await self.storage.write_readings_batch(readings)
            
            # Step 2: Get latest readings for all devices (for dashboard)
            latest_readings_dict = await self.storage.get_latest_readings_all_devices()
            
            # FIX: Determine device IDs dynamically
            main_meter_reading = next((r for r in latest_readings_dict.values() if r.device.device_type == 'main_meter'), None)
            smart_plug_readings = [r for r in latest_readings_dict.values() if r.device.device_type == 'smart_plug']
            smart_plug_ids = [r.device_id for r in smart_plug_readings]
            
            # Step 3: Calculate unknown load
            unknown_load = None
            if main_meter_reading:
                unknown_load = await self.analysis.calculate_unknown_load(
                    main_meter_id=main_meter_reading.device_id,
                    smart_plug_ids=smart_plug_ids
                )
            
            # Step 4: Prepare dashboard data
            dashboard_data = {
                'devices': [],
                'unknown_load_watts': float(unknown_load) if unknown_load else None  # Match API format
            }
            
            # FIX: Iterate dict correctly
            for device_id, reading in latest_readings_dict.items():
                if reading:
                    dashboard_data['devices'].append({
                        'device_id': str(reading.device_id),
                        'device_type': reading.device.device_type,
                        'device_name': reading.device.name,
                        'power_watts': float(reading.power_watts),
                        'cumulative_kwh': float(reading.energy_kwh),  # FIX: cumulative_kwh doesn't exist, use energy_kwh
                        'timestamp': reading.timestamp.isoformat(),
                        'is_online': reading.device.is_active  # FIX: is_online doesn't exist, use is_active
                    })
            
            # Step 5: Broadcast to SSE clients
            await broadcaster.broadcast_readings(dashboard_data)
            
            # Step 6: Check for alerts (main meter only)
            # FIX: Find main meter from readings
            main_meter_simulated = next(
                (r for r in readings if r.device_name == 'Main Building Meter'),  # Match by name
                None
            )
            
            if main_meter_simulated:
                # Get device name for alert message
                main_device = latest_readings_dict.get(main_meter_simulated.device_id)
                device_name = main_device.device.name if main_device else 'Main Meter'
                
                alerts = await self.alert_service.check_and_create_alerts(
                    device_id=main_meter_simulated.device_id,
                    device_name=device_name,
                    current_power=Decimal(str(main_meter_simulated.power_watts))
                )
                
                # Broadcast any new alerts
                for alert in alerts:
                    await broadcaster.broadcast_alert({
                        'id': alert.id,
                        'device_id': str(alert.device_id),
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        # FIX: Use correct field names
                        'value': float(alert.actual_value) if alert.actual_value else None,
                        'threshold': float(alert.threshold_value) if alert.threshold_value else None,
                        'timestamp': alert.timestamp.isoformat(),
                        'acknowledged': alert.is_acknowledged  # FIX: acknowledged -> is_acknowledged
                    })
                    logger.info(f"Alert created: {alert.alert_type} - {alert.message}")
                    
        except Exception as e:
            logger.error(f"Error processing readings: {e}", exc_info=True)
            
    def start(self):
        """Start the polling service."""
        if not self.polling_service:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
        self.polling_service.start()
        logger.info("Orchestrator started - polling active")
        
    def stop(self):
        """Stop the polling service."""
        if self.polling_service:
            self.polling_service.stop()
        logger.info("Orchestrator stopped")
