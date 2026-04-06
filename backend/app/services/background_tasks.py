"""
Background task scheduler for periodic summary generation.
Runs hourly and daily aggregation tasks.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import async_sessionmaker
import logging

from .storage_service import StorageService
from .analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class BackgroundTaskScheduler:
    """Manages periodic background tasks for summary generation."""
    
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory
        self.storage = StorageService(session_factory)
        self.analysis = AnalysisService(self.storage)  # FIX: Pass StorageService, not session_factory
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """Start the background task scheduler."""
        # Run hourly summary at the top of each hour
        self.scheduler.add_job(
            self._generate_hourly_summaries,
            CronTrigger(minute=0),  # Every hour at :00
            id='hourly_summaries',
            max_instances=1,
            replace_existing=True
        )
        
        # Run daily summary at midnight
        self.scheduler.add_job(
            self._generate_daily_summaries,
            CronTrigger(hour=0, minute=5),  # Every day at 00:05
            id='daily_summaries',
            max_instances=1,
            replace_existing=True
        )
        
        # Run data cleanup weekly (keep last 7 days of raw readings)
        self.scheduler.add_job(
            self._cleanup_old_readings,
            CronTrigger(day_of_week='mon', hour=2, minute=0),  # Monday 2 AM
            id='cleanup_readings',
            max_instances=1,
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Background task scheduler started")
        
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.scheduler.shutdown(wait=True)
        logger.info("Background task scheduler stopped")
        
    async def _generate_hourly_summaries(self):
        """Generate hourly summaries for the previous hour."""
        try:
            # Get the previous hour (e.g., if now is 14:00, generate for 13:00-14:00)
            now = datetime.now()
            hour_start = (now - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            logger.info(f"Generating hourly summaries for {hour_start} to {hour_end}")
            
            devices = await self.storage.get_devices()
            
            for device in devices:
                try:
                    stats = await self.analysis.calculate_hourly_stats(
                        device.id,
                        hour_start
                    )
                    
                    if stats:
                        # FIX: Use correct parameter names matching storage_service.create_hourly_summary
                        await self.storage.create_hourly_summary(
                            device_id=device.id,
                            hour_timestamp=hour_start,
                            avg_power=float(stats['avg_power']),
                            max_power=float(stats['max_power']),
                            min_power=float(stats['min_power']),
                            total_kwh=float(stats['total_kwh']),
                            reading_count=stats['reading_count']
                        )
                        logger.info(f"Created hourly summary for {device.name} at {hour_start}")
                    else:
                        logger.warning(f"No data for {device.name} in hour {hour_start}")
                        
                except Exception as e:
                    logger.error(f"Error generating hourly summary for {device.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in hourly summary generation: {e}")
            
    async def _generate_daily_summaries(self):
        """Generate daily summaries for the previous day."""
        try:
            # Get yesterday's date
            now = datetime.now()
            yesterday = (now - timedelta(days=1)).date()
            
            logger.info(f"Generating daily summaries for {yesterday}")
            
            devices = await self.storage.get_devices()
            
            for device in devices:
                try:
                    stats = await self.analysis.calculate_daily_stats(
                        device.id,
                        yesterday
                    )
                    
                    if stats:
                        # FIX: Use correct parameter names matching storage_service.create_daily_summary
                        await self.storage.create_daily_summary(
                            device_id=device.id,
                            summary_date=yesterday,
                            total_kwh=float(stats['total_kwh']),
                            avg_power=float(stats['avg_power']),
                            peak_hour=stats['peak_hour'],
                            estimated_cost=None  # Cost calculated separately if needed
                        )
                        logger.info(f"Created daily summary for {device.name} on {yesterday}")
                    else:
                        logger.warning(f"No data for {device.name} on {yesterday}")
                        
                except Exception as e:
                    logger.error(f"Error generating daily summary for {device.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in daily summary generation: {e}")
            
    async def _cleanup_old_readings(self):
        """Delete raw readings older than 7 days."""
        try:
            # FIX: delete_old_readings expects days as int, not datetime
            deleted_count = await self.storage.delete_old_readings(days=7)
            logger.info(f"Deleted {deleted_count} old readings (older than 7 days)")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
