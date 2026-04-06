"""Dashboard API routes"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.api.dependencies import get_storage_service, get_analysis_service
from app.services import StorageService, AnalysisService

router = APIRouter()


@router.get("/dashboard/current")
async def get_current_dashboard(
    storage: StorageService = Depends(get_storage_service),
    analysis: AnalysisService = Depends(get_analysis_service)
):
    """
    Get current dashboard data (all devices latest readings + unknown load)
    
    Returns:
        - timestamp: Current time (ISO format)
        - devices: List of device readings
        - unknown_load_watts: Calculated unknown load
        - total_power_watts: Total building consumption
    """
    # Get all active devices
    devices = await storage.get_devices(active_only=True)
    
    if not devices:
        raise HTTPException(status_code=404, detail="No active devices found")
    
    # Get latest readings for all devices
    latest_readings = await storage.get_latest_readings_all_devices()
    
    # Build device data
    device_data = []
    main_meter_id = None
    smart_plug_ids = []
    total_power = Decimal('0')
    
    for device in devices:
        # latest_readings is Dict[UUID, Reading], get by device.id key
        reading = latest_readings.get(device.id)
        
        # Match field names with SSE broadcast format for consistency
        device_info = {
            "device_id": str(device.id),
            "device_name": device.name,  # Match SSE format
            "device_type": device.device_type,
            "location": device.location,
            "power_watts": float(reading.power_watts) if reading else None,
            "voltage_volts": float(reading.voltage_volts) if reading and reading.voltage_volts else None,
            "current_amps": float(reading.current_amps) if reading and reading.current_amps else None,
            "cumulative_kwh": float(reading.energy_kwh) if reading else None,  # Match SSE format
            "timestamp": reading.timestamp.isoformat() if reading else None,
            "is_online": device.is_active  # Match SSE format
        }
        
        device_data.append(device_info)
        
        # Track main meter and smart plugs for unknown load calculation
        if device.device_type == "main_meter":
            main_meter_id = str(device.id)
            if reading:
                total_power = reading.power_watts
        elif device.device_type == "smart_plug":
            smart_plug_ids.append(str(device.id))
    
    # Calculate unknown load
    unknown_load = None
    if main_meter_id and smart_plug_ids:
        unknown_load_decimal = await analysis.calculate_unknown_load(
            main_meter_id,
            smart_plug_ids,
            minutes=5
        )
        unknown_load = float(unknown_load_decimal) if unknown_load_decimal is not None else None
    
    return {
        "timestamp": datetime.now().isoformat(),
        "devices": device_data,
        "unknown_load_watts": unknown_load,
        "total_power_watts": float(total_power)
    }


# NOTE: This endpoint is currently unused by the frontend
# Frontend uses SSE for live data, not this REST endpoint
# If re-enabling, need to either:
# 1. Make device_id optional and return data for all devices, or  
# 2. Update frontend to pass device_id parameter
# Commented out to avoid confusion about broken contract
#
# @router.get("/dashboard/recent")
# async def get_recent_readings(
#     device_id: str,
#     minutes: int = 30,
#     storage: StorageService = Depends(get_storage_service)
# ):
#     """
#     Get recent readings for a specific device (for live graph)
#     
#     Args:
#         device_id: Device UUID
#         minutes: Minutes of history to retrieve (default 30)
#         
#     Returns:
#         List of readings with timestamp and power
#     """
#     readings = await storage.get_recent_readings(device_id, minutes=minutes)
#     
#     return {
#         "device_id": device_id,
#         "minutes": minutes,
#         "readings": [
#             {
#                 "timestamp": r.timestamp.isoformat(),
#                 "power_watts": float(r.power_watts),
#                 "energy_kwh": float(r.energy_kwh)
#             }
#             for r in readings
#         ]
#     }
