"""Summary models"""

from sqlalchemy import Column, Integer, Date, DateTime, Numeric, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class HourlySummary(Base):
    """Hourly aggregated statistics per device"""
    
    __tablename__ = 'hourly_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False
    )
    hour_timestamp = Column(DateTime(timezone=False), nullable=False)
    avg_power_watts = Column(Numeric(10, 2), nullable=False)
    max_power_watts = Column(Numeric(10, 2), nullable=False)
    min_power_watts = Column(Numeric(10, 2), nullable=False)
    total_kwh = Column(Numeric(10, 3), nullable=False)
    reading_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="hourly_summaries")
    
    __table_args__ = (
        Index('uix_hourly_device_hour', 'device_id', 'hour_timestamp', unique=True),
        Index('ix_hourly_timestamp', 'hour_timestamp'),
    )
    
    def __repr__(self):
        return f"<HourlySummary(device={self.device_id}, hour={self.hour_timestamp})>"


class DailySummary(Base):
    """Daily aggregated statistics per device"""
    
    __tablename__ = 'daily_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False
    )
    date = Column(Date, nullable=False)
    total_kwh = Column(Numeric(12, 3), nullable=False)
    avg_power_watts = Column(Numeric(10, 2), nullable=False)
    peak_hour = Column(
        Integer,
        nullable=False
    )
    estimated_cost_inr = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="daily_summaries")
    
    __table_args__ = (
        Index('uix_daily_device_date', 'device_id', 'date', unique=True),
        Index('ix_daily_date', 'date'),
        CheckConstraint('peak_hour >= 0 AND peak_hour <= 23', name='check_peak_hour_range'),
    )
    
    def __repr__(self):
        return f"<DailySummary(device={self.device_id}, date={self.date})>"
