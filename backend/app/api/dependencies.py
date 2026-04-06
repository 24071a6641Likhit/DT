"""Dependency injection for API routes"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.database import get_async_session
from app.services import (
    StorageService,
    AnalysisService,
    AlertService,
    BillingService
)


async def get_storage_service() -> StorageService:
    """Get storage service instance"""
    session_factory = get_async_session()
    return StorageService(session_factory)


async def get_analysis_service() -> AnalysisService:
    """Get analysis service instance"""
    storage = await get_storage_service()
    return AnalysisService(storage)


async def get_alert_service() -> AlertService:
    """Get alert service instance"""
    storage = await get_storage_service()
    analysis = await get_analysis_service()
    return AlertService(storage, analysis)


async def get_billing_service() -> BillingService:
    """Get billing service instance"""
    storage = await get_storage_service()
    return BillingService(storage)
