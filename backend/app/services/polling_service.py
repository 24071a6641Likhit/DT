"""Polling service - schedules and executes data collection every 5 seconds"""

import logging
from typing import List, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.simulator.energy_simulator import EnergySimulator, SimulatedReading

logger = logging.getLogger(__name__)


class PollingService:
    """Manages scheduled polling of simulator"""
    
    def __init__(
        self,
        simulator: EnergySimulator,
        callback: Callable[[List[SimulatedReading]], None],
        interval_seconds: int = 5
    ):
        """
        Initialize polling service
        
        Args:
            simulator: Energy simulator instance
            callback: Async function to call with readings (e.g., storage service)
            interval_seconds: Polling interval in seconds
        """
        self.simulator = simulator
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
        self.consecutive_failures = 0
        self.max_consecutive_failures = 10
    
    def start(self):
        """Start polling job"""
        self.scheduler.add_job(
            self._poll_and_process,
            trigger=IntervalTrigger(seconds=self.interval_seconds),
            id='main_poller',
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        self.scheduler.start()
        logger.info(f"Polling service started (interval: {self.interval_seconds}s)")
    
    def stop(self):
        """Stop polling job"""
        self.scheduler.shutdown(wait=True)
        logger.info("Polling service stopped")
    
    def is_running(self) -> bool:
        """Check if polling service is running"""
        return self.scheduler.running
    
    async def _poll_and_process(self):
        """Single poll cycle - called every N seconds"""
        try:
            # Generate readings from simulator
            readings = self.simulator.generate_readings()
            logger.debug(f"Generated {len(readings)} readings")
            
            # Call callback (e.g., storage service)
            await self.callback(readings)
            
            # Reset failure counter on success
            self.consecutive_failures = 0
            
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(
                f"Poll cycle failed (attempt {self.consecutive_failures}): {e}",
                exc_info=True
            )
            
            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.critical(
                    f"Polling failed {self.consecutive_failures} consecutive times. "
                    "Continuing to retry..."
                )
            
            # Don't re-raise - continue polling on next cycle
    
    def get_status(self) -> dict:
        """Get polling service status"""
        return {
            'running': self.scheduler.running,
            'interval_seconds': self.interval_seconds,
            'consecutive_failures': self.consecutive_failures,
            'next_run_time': str(self.scheduler.get_job('main_poller').next_run_time) if self.scheduler.get_job('main_poller') else None
        }
