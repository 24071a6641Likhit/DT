"""Alert management API routes"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.api.dependencies import get_alert_service
from app.services import AlertService

router = APIRouter()


@router.get("/alerts")
async def get_alerts(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    is_acknowledged: bool = False,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get alerts with optional filtering
    
    Args:
        device_id: Optional filter by device
        severity: Optional filter by severity (info, warning, critical)
        is_acknowledged: If False (default), return only unacknowledged alerts
        
    Returns:
        List of alerts
    """
    if is_acknowledged:
        # Need to implement getting all alerts in storage service
        # For now, just get active (unacknowledged) alerts
        alerts = await alert_service.get_active_alerts(device_id=device_id, severity=severity)
    else:
        alerts = await alert_service.get_active_alerts(device_id=device_id, severity=severity)
    
    return {
        "alerts": [
            {
                "id": a.id,
                "device_id": str(a.device_id) if a.device_id else None,
                "timestamp": a.timestamp.isoformat(),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "threshold_value": float(a.threshold_value) if a.threshold_value else None,
                "actual_value": float(a.actual_value) if a.actual_value else None,
                "is_acknowledged": a.is_acknowledged,
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None
            }
            for a in alerts
        ]
    }


@router.get("/alerts/count")
async def get_alert_count(
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get count of unacknowledged alerts
    
    Returns:
        Count of active alerts
    """
    count = await alert_service.get_alert_count()
    
    return {
        "unacknowledged_count": count
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Acknowledge an alert
    
    Args:
        alert_id: Alert ID to acknowledge
        
    Returns:
        Updated alert
    """
    alert = await alert_service.acknowledge_alert(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "id": alert.id,
        "device_id": str(alert.device_id) if alert.device_id else None,
        "timestamp": alert.timestamp.isoformat(),
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "is_acknowledged": alert.is_acknowledged,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
    }
