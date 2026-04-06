"""Settings API routes"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import get_billing_service
from app.services import BillingService
from app.services.billing_service import SlabRate

router = APIRouter()


class SlabRateUpdate(BaseModel):
    """Slab rate update request"""
    min_units: int
    max_units: Optional[int]  # None for unlimited
    rate_per_unit: float


@router.get("/settings")
async def get_settings(
    billing: BillingService = Depends(get_billing_service)
):
    """
    Get all configurable settings
    
    Returns:
        Current system settings
    """
    rates = billing.get_slab_rates()
    
    return {
        "spike_threshold": 1.5,  # From AlertService.SPIKE_THRESHOLD
        "polling_interval_seconds": 5,
        "data_retention_days": 90,
        "slab_rates": rates
    }


@router.put("/settings/slab-rates")
async def update_slab_rates(
    rates: List[SlabRateUpdate],
    billing: BillingService = Depends(get_billing_service)
):
    """
    Update electricity slab rates
    
    Args:
        rates: List of new slab rates
        
    Returns:
        Updated slab rates
    """
    # Convert to SlabRate objects
    new_rates = [
        SlabRate(
            min_units=r.min_units,
            max_units=r.max_units,
            rate_per_unit=r.rate_per_unit
        )
        for r in rates
    ]
    
    try:
        billing.update_slab_rates(new_rates)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "slab_rates": billing.get_slab_rates()
    }
