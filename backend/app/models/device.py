"""Device model"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.config.database import Base


class Device(Base):
    """Hardware device (main meter or smart plug)"""
    
    __tablename__ = 'devices'
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(String(100), nullable=False)
    device_type = Column(
        String(20),
        nullable=False,
        index=True
    )  # 'main_meter' or 'smart_plug'
    location = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    readings = relationship("Reading", back_populates="device", lazy="select", cascade="all, delete-orphan")
    hourly_summaries = relationship("HourlySummary", back_populates="device", lazy="select", cascade="all, delete-orphan")
    daily_summaries = relationship("DailySummary", back_populates="device", lazy="select", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", lazy="select")
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, type={self.device_type})>"
