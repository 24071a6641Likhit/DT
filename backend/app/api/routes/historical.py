"""Historical data API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date, datetime
from typing import Optional

from app.api.dependencies import get_storage_service
from app.services import StorageService

router = APIRouter()


@router.get("/historical/daily")
async def get_daily_summaries(
    device_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get daily summaries for date range
    
    Args:
        device_id: Device UUID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        List of daily summaries
    """
    summaries = await storage.get_daily_summaries_range(device_id, start_date, end_date)
    
    return {
        "device_id": device_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "summaries": [
            {
                "date": s.date.isoformat(),  # FIX: Model uses 'date' not 'summary_date'
                "total_kwh": float(s.total_kwh),
                "avg_power_watts": float(s.avg_power_watts),
                "peak_hour": s.peak_hour,
                "estimated_cost_inr": float(s.estimated_cost_inr) if s.estimated_cost_inr else None
            }
            for s in summaries
        ]
    }


@router.get("/historical/hourly")
async def get_hourly_summaries(
    device_id: str,
    date: date = Query(..., description="Date (YYYY-MM-DD)"),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get hourly summaries for a specific day
    
    Args:
        device_id: Device UUID
        date: Date to get hourly data for
        
    Returns:
        List of hourly summaries
    """
    summaries = await storage.get_hourly_summaries_for_day(device_id, date)
    
    return {
        "device_id": device_id,
        "date": date.isoformat(),
        "summaries": [
            {
                "hour": s.hour_timestamp.hour,
                "timestamp": s.hour_timestamp.isoformat(),
                "avg_power_watts": float(s.avg_power_watts),
                "max_power_watts": float(s.max_power_watts),
                "min_power_watts": float(s.min_power_watts),
                "total_kwh": float(s.total_kwh),
                "reading_count": s.reading_count
            }
            for s in summaries
        ]
    }


@router.get("/historical/readings")
async def get_readings_range(
    device_id: str,
    start_time: datetime = Query(..., description="Start timestamp (ISO format)"),
    end_time: datetime = Query(..., description="End timestamp (ISO format)"),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get raw readings for a time range
    
    Note: Use sparingly, prefer daily/hourly summaries for large ranges
    
    Args:
        device_id: Device UUID
        start_time: Start timestamp
        end_time: End timestamp
        
    Returns:
        List of raw readings
    """
    # Limit range to prevent huge queries
    duration = (end_time - start_time).total_seconds()
    if duration > 3600:  # More than 1 hour
        raise HTTPException(
            status_code=400,
            detail="Time range too large (max 1 hour). Use daily/hourly summaries for longer periods."
        )
    
    readings = await storage.get_readings_range(device_id, start_time, end_time)
    
    return {
        "device_id": device_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "count": len(readings),
        "readings": [
            {
                "timestamp": r.timestamp.isoformat(),
                "power_watts": float(r.power_watts),
                "voltage_volts": float(r.voltage_volts) if r.voltage_volts else None,
                "current_amps": float(r.current_amps) if r.current_amps else None,
                "energy_kwh": float(r.energy_kwh)
            }
            for r in readings
        ]
    }
