"""Reading model"""

from sqlalchemy import Column, DateTime, Numeric, ForeignKey, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class Reading(Base):
    """Time-series power reading from a device"""
    
    __tablename__ = 'readings'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    timestamp = Column(DateTime(timezone=False), nullable=False, index=True)
    power_watts = Column(Numeric(10, 2), nullable=False)
    voltage_volts = Column(Numeric(6, 2), nullable=True)
    current_amps = Column(Numeric(8, 2), nullable=True)
    energy_kwh = Column(Numeric(12, 3), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="readings")
    
    __table_args__ = (
        Index('ix_readings_device_timestamp', 'device_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Reading(id={self.id}, device={self.device_id}, power={self.power_watts}W)>"
