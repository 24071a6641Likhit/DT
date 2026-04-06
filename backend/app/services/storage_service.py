"""Storage service - database write and read operations"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Device, Reading, HourlySummary, DailySummary, Alert
from app.simulator.energy_simulator import SimulatedReading

logger = logging.getLogger(__name__)


class StorageService:
    """Handles all database write and read operations"""
    
    def __init__(self, session_factory):
        """
        Initialize storage service
        
        Args:
            session_factory: Callable that returns AsyncSession
        """
        self.session_factory = session_factory
    
    async def write_readings_batch(self, readings: List[SimulatedReading]) -> None:
        """
        Write multiple readings in single transaction
        
        Args:
            readings: List of simulated readings
        
        Raises:
            Exception: If database write fails
        """
        async with self.session_factory() as session:
            try:
                reading_models = []
                for r in readings:
                    # Get cumulative energy from simulator (will be updated in next iteration)
                    reading_model = Reading(
                        device_id=r.device_id,
                        timestamp=r.timestamp,
                        power_watts=Decimal(str(r.power_watts)),
                        voltage_volts=Decimal(str(r.voltage_volts)) if r.voltage_volts else None,
                        current_amps=Decimal(str(r.current_amps)) if r.current_amps else None,
                        energy_kwh=Decimal("0.0"),  # Will be calculated in summary jobs
                    )
                    reading_models.append(reading_model)
                
                session.add_all(reading_models)
                await session.commit()
                logger.debug(f"Wrote {len(reading_models)} readings to database")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to write readings: {e}", exc_info=True)
                raise
    
    async def get_devices(self, active_only: bool = True) -> List[Device]:
        """
        Get all devices
        
        Args:
            active_only: If True, return only active devices
        
        Returns:
            List of Device objects
        """
        async with self.session_factory() as session:
            stmt = select(Device)
            if active_only:
                stmt = stmt.where(Device.is_active == True)
            stmt = stmt.order_by(Device.device_type, Device.name)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_device_by_id(self, device_id: UUID) -> Optional[Device]:
        """Get single device by ID"""
        async with self.session_factory() as session:
            stmt = select(Device).where(Device.id == device_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def update_device(
        self,
        device_id: UUID,
        name: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[Device]:
        """Update device metadata"""
        async with self.session_factory() as session:
            try:
                stmt = select(Device).where(Device.id == device_id)
                result = await session.execute(stmt)
                device = result.scalar_one_or_none()
                
                if not device:
                    return None
                
                if name is not None:
                    device.name = name
                if location is not None:
                    device.location = location
                
                device.updated_at = datetime.now(ZoneInfo("Asia/Kolkata"))
                
                await session.commit()
                await session.refresh(device)
                return device
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update device: {e}")
                raise
    
    async def get_latest_readings_all_devices(self) -> Dict[UUID, Reading]:
        """
        Get most recent reading for each active device
        
        Returns:
            Dict mapping device_id to Reading (with device relationship eagerly loaded)
        """
        async with self.session_factory() as session:
            # Subquery: max timestamp per device
            subq = (
                select(
                    Reading.device_id,
                    func.max(Reading.timestamp).label('max_ts')
                )
                .group_by(Reading.device_id)
                .subquery()
            )
            
            # Join to get full reading with device info
            # FIX: Use selectinload to eagerly load device relationship
            stmt = (
                select(Reading)
                .options(selectinload(Reading.device))
                .join(
                    subq,
                    and_(
                        Reading.device_id == subq.c.device_id,
                        Reading.timestamp == subq.c.max_ts
                    )
                )
                .join(Device)
            )
            
            result = await session.execute(stmt)
            readings = result.scalars().all()
            
            return {r.device_id: r for r in readings}
    
    async def get_recent_readings(
        self,
        device_id: UUID,
        minutes: int
    ) -> List[Reading]:
        """
        Get readings for device within last N minutes
        
        Args:
            device_id: Device UUID
            minutes: Number of minutes to look back
        
        Returns:
            List of Reading objects, ordered by timestamp DESC
        """
        async with self.session_factory() as session:
            cutoff_time = datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(minutes=minutes)
            
            stmt = (
                select(Reading)
                .where(Reading.device_id == device_id)
                .where(Reading.timestamp >= cutoff_time)
                .order_by(Reading.timestamp.desc())
            )
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_readings_range(
        self,
        device_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Reading]:
        """Get readings within time range"""
        async with self.session_factory() as session:
            stmt = (
                select(Reading)
                .where(Reading.device_id == device_id)
                .where(Reading.timestamp >= start_time)
                .where(Reading.timestamp <= end_time)
                .order_by(Reading.timestamp.asc())
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def create_alert(
        self,
        device_id: Optional[UUID],
        alert_type: str,
        severity: str,
        message: str,
        threshold_value: Optional[float],
        actual_value: Optional[float]
    ) -> Alert:
        """Create new alert"""
        async with self.session_factory() as session:
            try:
                alert = Alert(
                    device_id=device_id,
                    timestamp=datetime.now(ZoneInfo("Asia/Kolkata")),
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    threshold_value=Decimal(str(threshold_value)) if threshold_value else None,
                    actual_value=Decimal(str(actual_value)) if actual_value else None,
                    is_acknowledged=False
                )
                session.add(alert)
                await session.commit()
                await session.refresh(alert)
                return alert
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create alert: {e}")
                raise
    
    async def get_alerts(
        self,
        device_id: Optional[UUID] = None,
        is_acknowledged: Optional[bool] = None,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[datetime] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts with optional filtering"""
        async with self.session_factory() as session:
            stmt = select(Alert)
            
            if device_id is not None:
                stmt = stmt.where(Alert.device_id == device_id)
            if is_acknowledged is not None:
                stmt = stmt.where(Alert.is_acknowledged == is_acknowledged)
            if alert_type:
                stmt = stmt.where(Alert.alert_type == alert_type)
            if severity:
                stmt = stmt.where(Alert.severity == severity)
            if since:
                stmt = stmt.where(Alert.timestamp >= since)
            if start_date:
                stmt = stmt.where(Alert.timestamp >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                stmt = stmt.where(Alert.timestamp <= datetime.combine(end_date, datetime.max.time()))
            
            stmt = stmt.order_by(Alert.timestamp.desc()).limit(limit)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_unacknowledged_alert_count(self) -> int:
        """Get count of unacknowledged alerts"""
        async with self.session_factory() as session:
            stmt = select(func.count()).select_from(Alert).where(Alert.is_acknowledged == False)
            result = await session.execute(stmt)
            return result.scalar()
    
    async def acknowledge_alert(self, alert_id: int) -> Optional[Alert]:
        """Mark alert as acknowledged"""
        async with self.session_factory() as session:
            try:
                stmt = select(Alert).where(Alert.id == alert_id)
                result = await session.execute(stmt)
                alert = result.scalar_one_or_none()
                
                if not alert:
                    return None
                
                alert.is_acknowledged = True
                alert.acknowledged_at = datetime.now(ZoneInfo("Asia/Kolkata"))
                
                await session.commit()
                await session.refresh(alert)
                return alert
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to acknowledge alert: {e}")
                raise
    
    async def create_hourly_summary(
        self,
        device_id: UUID,
        hour_timestamp: datetime,
        avg_power: float,
        max_power: float,
        min_power: float,
        total_kwh: float,
        reading_count: int
    ) -> HourlySummary:
        """Create hourly summary record"""
        async with self.session_factory() as session:
            try:
                summary = HourlySummary(
                    device_id=device_id,
                    hour_timestamp=hour_timestamp,
                    avg_power_watts=Decimal(str(avg_power)),
                    max_power_watts=Decimal(str(max_power)),
                    min_power_watts=Decimal(str(min_power)),
                    total_kwh=Decimal(str(total_kwh)),
                    reading_count=reading_count
                )
                session.add(summary)
                await session.commit()
                await session.refresh(summary)
                return summary
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create hourly summary: {e}")
                raise
    
    async def get_hourly_summaries(
        self,
        device_id: Optional[UUID],
        start_date: date,
        end_date: date
    ) -> List[HourlySummary]:
        """Get hourly summaries within date range"""
        async with self.session_factory() as session:
            stmt = (
                select(HourlySummary)
                .where(HourlySummary.hour_timestamp >= datetime.combine(start_date, datetime.min.time()))
                .where(HourlySummary.hour_timestamp <= datetime.combine(end_date, datetime.max.time()))
            )
            if device_id:
                stmt = stmt.where(HourlySummary.device_id == device_id)
            
            stmt = stmt.order_by(HourlySummary.hour_timestamp.asc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def create_daily_summary(
        self,
        device_id: UUID,
        summary_date: date,
        total_kwh: float,
        avg_power: float,
        peak_hour: int,
        estimated_cost: Optional[float]
    ) -> DailySummary:
        """Create daily summary record"""
        async with self.session_factory() as session:
            try:
                summary = DailySummary(
                    device_id=device_id,
                    date=summary_date,
                    total_kwh=Decimal(str(total_kwh)),
                    avg_power_watts=Decimal(str(avg_power)),
                    peak_hour=peak_hour,
                    estimated_cost_inr=Decimal(str(estimated_cost)) if estimated_cost else None
                )
                session.add(summary)
                await session.commit()
                await session.refresh(summary)
                return summary
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create daily summary: {e}")
                raise
    
    async def get_daily_summaries(
        self,
        device_id: Optional[UUID],
        start_date: date,
        end_date: date
    ) -> List[DailySummary]:
        """Get daily summaries within date range"""
        async with self.session_factory() as session:
            stmt = (
                select(DailySummary)
                .where(DailySummary.date >= start_date)
                .where(DailySummary.date <= end_date)
            )
            if device_id:
                stmt = stmt.where(DailySummary.device_id == device_id)
            
            stmt = stmt.order_by(DailySummary.date.asc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_daily_summaries_range(
        self,
        device_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[DailySummary]:
        """Get daily summaries for a device within date range (alias for billing/historical)"""
        return await self.get_daily_summaries(device_id, start_date, end_date)
    
    async def get_daily_summary(
        self,
        device_id: UUID,
        target_date: date
    ) -> Optional[DailySummary]:
        """Get single daily summary for a device on a specific date"""
        async with self.session_factory() as session:
            stmt = (
                select(DailySummary)
                .where(DailySummary.device_id == device_id)
                .where(DailySummary.date == target_date)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_hourly_summaries_for_day(
        self,
        device_id: UUID,
        target_date: date
    ) -> List[HourlySummary]:
        """Get all hourly summaries for a device on a specific day"""
        async with self.session_factory() as session:
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date, datetime.max.time())
            
            stmt = (
                select(HourlySummary)
                .where(HourlySummary.device_id == device_id)
                .where(HourlySummary.hour_timestamp >= start_time)
                .where(HourlySummary.hour_timestamp <= end_time)
                .order_by(HourlySummary.hour_timestamp.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def delete_old_readings(self, days: int) -> int:
        """Delete readings older than N days"""
        async with self.session_factory() as session:
            try:
                cutoff_date = datetime.now(ZoneInfo("Asia/Kolkata")) - timedelta(days=days)
                
                stmt = delete(Reading).where(Reading.timestamp < cutoff_date)
                result = await session.execute(stmt)
                await session.commit()
                
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} readings older than {cutoff_date}")
                return deleted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete old readings: {e}")
                raise
