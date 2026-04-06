"""Billing API routes"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import date

from app.api.dependencies import get_billing_service, get_storage_service
from app.services import BillingService, StorageService

router = APIRouter()


@router.get("/billing/current-month")
async def get_current_month_bill(
    billing: BillingService = Depends(get_billing_service),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get billing estimate for current month
    
    Returns:
        Bill estimate with period, consumption, cost, and slab breakdown
    """
    # Get main meter device
    devices = await storage.get_devices(active_only=True)
    main_meter = next((d for d in devices if d.device_type == "main_meter"), None)
    
    if not main_meter:
        raise HTTPException(status_code=404, detail="Main meter not found")
    
    estimate = await billing.get_current_month_bill(str(main_meter.id))
    
    return {
        "billing_period_start": estimate.billing_period_start,
        "billing_period_end": estimate.billing_period_end,
        "total_kwh": estimate.total_kwh,
        "total_cost_inr": estimate.total_cost_inr,
        "slab_breakdown": estimate.slab_breakdown
    }


@router.get("/billing/monthly-comparison")
async def get_monthly_comparison(
    months: int = 6,
    billing: BillingService = Depends(get_billing_service),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get last N months comparison
    
    Args:
        months: Number of months to include (default 6)
        
    Returns:
        List of monthly summaries
    """
    # Get main meter
    devices = await storage.get_devices(active_only=True)
    main_meter = next((d for d in devices if d.device_type == "main_meter"), None)
    
    if not main_meter:
        raise HTTPException(status_code=404, detail="Main meter not found")
    
    comparison = await billing.get_monthly_comparison(str(main_meter.id), months=months)
    
    return {
        "months": comparison
    }


@router.get("/billing/rates")
async def get_slab_rates(
    billing: BillingService = Depends(get_billing_service)
):
    """
    Get current electricity slab rates
    
    Returns:
        List of slab rate configurations
    """
    rates = billing.get_slab_rates()
    
    return {
        "slab_rates": rates
    }
