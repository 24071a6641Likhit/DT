"""Alert service for managing power consumption alerts"""

from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.storage_service import StorageService
from app.services.analysis_service import AnalysisService
from app.models import Alert


class AlertService:
    """Manages alert creation, suppression, and notification"""
    
    # Alert type thresholds
    SPIKE_THRESHOLD = 1.5  # 50% above baseline
    OVERLOAD_THRESHOLD_WATTS = 6400.0  # 80% of 8kW limit
    HIGH_CONSUMPTION_THRESHOLD_KWH = 20.0  # kWh per hour
    
    # Alert suppression windows (minutes)
    SPIKE_SUPPRESSION_MINUTES = 15
    OVERLOAD_SUPPRESSION_MINUTES = 10
    HIGH_CONSUMPTION_SUPPRESSION_MINUTES = 60
    
    def __init__(self, storage: StorageService, analysis: AnalysisService):
        self.storage = storage
        self.analysis = analysis
        self.ist = ZoneInfo("Asia/Kolkata")
    
    async def check_and_create_alerts(
        self,
        device_id: str,
        device_name: str,
        current_power: Decimal
    ) -> List[Alert]:
        """
        Check for alert conditions and create alerts if needed.
        
        Checks:
        1. Power spike (sustained increase above baseline)
        2. Overload (approaching circuit limit)
        
        Applies suppression logic to prevent alert fatigue.
        
        Args:
            device_id: Device to check
            device_name: Device name for alert message
            current_power: Current power reading in watts
            
        Returns:
            List of newly created alerts (may be empty)
        """
        created_alerts = []
        
        # Check for spike
        spike_alert = await self._check_spike_alert(device_id, device_name, current_power)
        if spike_alert:
            created_alerts.append(spike_alert)
        
        # Check for overload
        overload_alert = await self._check_overload_alert(device_id, device_name, current_power)
        if overload_alert:
            created_alerts.append(overload_alert)
        
        return created_alerts
    
    async def _check_spike_alert(
        self,
        device_id: str,
        device_name: str,
        current_power: Decimal
    ) -> Optional[Alert]:
        """
        Check for sustained power spike and create alert if needed.
        
        Returns:
            Alert object if spike detected and not suppressed, else None
        """
        # Check if spike is suppressed
        if await self._is_suppressed(device_id, "spike", self.SPIKE_SUPPRESSION_MINUTES):
            return None
        
        # Detect spike using analysis service
        is_spike, baseline = await self.analysis.detect_spike(
            device_id,
            current_power,
            spike_threshold=self.SPIKE_THRESHOLD
        )
        
        if not is_spike:
            return None
        
        # Calculate increase percentage
        increase_pct = ((current_power - baseline) / baseline * 100) if baseline else Decimal('0')
        
        # Create alert
        alert = await self.storage.create_alert(
            device_id=device_id,
            alert_type="spike",
            severity="warning",
            message=(
                f"{device_name}: Power spike detected. "
                f"Current: {current_power:.0f}W, "
                f"Baseline: {baseline:.0f}W "
                f"({increase_pct:.0f}% increase)"
            ),
            threshold_value=float(baseline * Decimal(str(self.SPIKE_THRESHOLD))),
            actual_value=float(current_power)
        )
        
        return alert
    
    async def _check_overload_alert(
        self,
        device_id: str,
        device_name: str,
        current_power: Decimal
    ) -> Optional[Alert]:
        """
        Check for circuit overload condition.
        
        Returns:
            Alert object if overload detected and not suppressed, else None
        """
        threshold = Decimal(str(self.OVERLOAD_THRESHOLD_WATTS))
        
        if current_power <= threshold:
            return None
        
        # Check if overload is suppressed
        if await self._is_suppressed(device_id, "overload", self.OVERLOAD_SUPPRESSION_MINUTES):
            return None
        
        # Calculate percentage of limit
        limit = Decimal('8000')  # 8kW circuit limit
        pct_of_limit = (current_power / limit * 100)
        
        # Determine severity
        severity = "critical" if current_power > Decimal('7200') else "warning"
        
        # Create alert
        alert = await self.storage.create_alert(
            device_id=device_id,
            alert_type="overload",
            severity=severity,
            message=(
                f"{device_name}: High power consumption. "
                f"Current: {current_power:.0f}W "
                f"({pct_of_limit:.0f}% of 8kW limit)"
            ),
            threshold_value=float(threshold),
            actual_value=float(current_power)
        )
        
        return alert
    
    async def check_high_consumption_alert(
        self,
        device_id: str,
        device_name: str,
        hourly_kwh: Decimal
    ) -> Optional[Alert]:
        """
        Check for high consumption in an hour.
        
        Called by background task after hourly summary is created.
        
        Args:
            device_id: Device to check
            device_name: Device name for alert message
            hourly_kwh: Total kWh consumed in the hour
            
        Returns:
            Alert object if high consumption detected and not suppressed, else None
        """
        threshold = Decimal(str(self.HIGH_CONSUMPTION_THRESHOLD_KWH))
        
        if hourly_kwh <= threshold:
            return None
        
        # Check if suppressed
        if await self._is_suppressed(device_id, "high_consumption", self.HIGH_CONSUMPTION_SUPPRESSION_MINUTES):
            return None
        
        # Create alert
        alert = await self.storage.create_alert(
            device_id=device_id,
            alert_type="high_consumption",
            severity="info",
            message=(
                f"{device_name}: High hourly consumption. "
                f"Used {hourly_kwh:.1f} kWh in the last hour "
                f"(threshold: {threshold:.1f} kWh)"
            ),
            threshold_value=float(threshold),
            actual_value=float(hourly_kwh)
        )
        
        return alert
    
    async def _is_suppressed(
        self,
        device_id: str,
        alert_type: str,
        suppression_minutes: int
    ) -> bool:
        """
        Check if alerts of this type are currently suppressed for this device.
        
        Suppression prevents alert fatigue by not creating duplicate alerts
        for the same condition within a time window.
        
        Args:
            device_id: Device to check
            alert_type: Type of alert (spike, overload, etc.)
            suppression_minutes: Suppression window in minutes
            
        Returns:
            True if alerts are suppressed, False if we can create a new alert
        """
        # DB stores timestamps as naive (timezone=False); use naive IST datetime
        cutoff = datetime.now(self.ist).replace(tzinfo=None) - timedelta(minutes=suppression_minutes)
        
        # Get recent alerts of this type for this device
        recent_alerts = await self.storage.get_alerts(
            device_id=device_id,
            alert_type=alert_type,
            since=cutoff,
            limit=1
        )
        
        # If any recent alerts exist, suppress new alerts
        return len(recent_alerts) > 0
    
    async def acknowledge_alert(self, alert_id: int) -> Optional[Alert]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of alert to acknowledge
            
        Returns:
            Updated alert object or None if not found
        """
        return await self.storage.acknowledge_alert(alert_id)
    
    async def get_active_alerts(
        self,
        device_id: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Alert]:
        """
        Get unacknowledged alerts.
        
        Args:
            device_id: Optional filter by device
            severity: Optional filter by severity (info, warning, critical)
            
        Returns:
            List of unacknowledged alerts, most recent first
        """
        return await self.storage.get_alerts(
            device_id=device_id,
            is_acknowledged=False,
            severity=severity
        )
    
    async def get_alert_count(self) -> int:
        """
        Get count of unacknowledged alerts.
        
        Returns:
            Number of unacknowledged alerts
        """
        return await self.storage.get_unacknowledged_alert_count()
