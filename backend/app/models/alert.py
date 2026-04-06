"""Alert model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class Alert(Base):
    """System alert or notification"""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey('devices.id', ondelete='SET NULL'),
        nullable=True
    )
    timestamp = Column(DateTime(timezone=False), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=True)
    actual_value = Column(Numeric(10, 2), nullable=True)
    is_acknowledged = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_at = Column(DateTime(timezone=False), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    
    __table_args__ = (
        Index('ix_alerts_type_timestamp', 'alert_type', 'timestamp'),
        CheckConstraint(
            "alert_type IN ('spike', 'overload', 'high_consumption', 'high_overnight', 'long_runtime', 'bill_threshold')",
            name='check_alert_type'
        ),
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name='check_severity'
        ),
    )
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity})>"
