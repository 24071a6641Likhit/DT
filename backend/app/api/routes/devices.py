"""Device management API routes"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_storage_service
from app.services import StorageService

router = APIRouter()


class DeviceUpdate(BaseModel):
    """Device update request"""
    name: Optional[str] = None
    location: Optional[str] = None


@router.get("/devices")
async def get_devices(
    active_only: bool = False,
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get all devices
    
    Args:
        active_only: If true, return only active devices
        
    Returns:
        List of devices
    """
    devices = await storage.get_devices(active_only=active_only)
    
    return {
        "devices": [
            {
                "id": str(d.id),
                "name": d.name,
                "device_type": d.device_type,
                "location": d.location,
                "is_active": d.is_active,
                "created_at": d.created_at.isoformat()
            }
            for d in devices
        ]
    }


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get specific device details
    
    Args:
        device_id: Device UUID
        
    Returns:
        Device details
    """
    # Get device by querying all and filtering (storage service doesn't have get_by_id yet)
    devices = await storage.get_devices(active_only=False)
    device = next((d for d in devices if str(d.id) == device_id), None)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "id": str(device.id),
        "name": device.name,
        "device_type": device.device_type,
        "location": device.location,
        "is_active": device.is_active,
        "created_at": device.created_at.isoformat()
    }


@router.patch("/devices/{device_id}")
async def update_device(
    device_id: str,
    update: DeviceUpdate,
    storage: StorageService = Depends(get_storage_service)
):
    """
    Update device metadata
    
    Args:
        device_id: Device UUID
        update: Fields to update
        
    Returns:
        Updated device
    """
    updated_device = await storage.update_device(
        device_id,
        name=update.name,
        location=update.location
    )
    
    if not updated_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "id": str(updated_device.id),
        "name": updated_device.name,
        "device_type": updated_device.device_type,
        "location": updated_device.location,
        "is_active": updated_device.is_active,
        "created_at": updated_device.created_at.isoformat()
    }
