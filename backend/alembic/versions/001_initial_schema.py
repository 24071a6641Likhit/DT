"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-04-05 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('device_type', sa.String(20), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_devices_id', 'devices', ['id'])
    op.create_index('ix_devices_device_type', 'devices', ['device_type'])
    op.create_index('ix_devices_is_active', 'devices', ['is_active'])
    
    # Create readings table
    op.create_table(
        'readings',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=False), nullable=False),
        sa.Column('power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('voltage_volts', sa.Numeric(6, 2), nullable=True),
        sa.Column('current_amps', sa.Numeric(8, 2), nullable=True),
        sa.Column('energy_kwh', sa.Numeric(12, 3), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_readings_device_id', 'readings', ['device_id'])
    op.create_index('ix_readings_timestamp', 'readings', ['timestamp'])
    op.create_index('ix_readings_device_timestamp', 'readings', ['device_id', 'timestamp'])
    
    # Create hourly_summaries table
    op.create_table(
        'hourly_summaries',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hour_timestamp', sa.DateTime(timezone=False), nullable=False),
        sa.Column('avg_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_kwh', sa.Numeric(10, 3), nullable=False),
        sa.Column('reading_count', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('uix_hourly_device_hour', 'hourly_summaries', ['device_id', 'hour_timestamp'], unique=True)
    op.create_index('ix_hourly_timestamp', 'hourly_summaries', ['hour_timestamp'])
    
    # Create daily_summaries table
    op.create_table(
        'daily_summaries',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('total_kwh', sa.Numeric(12, 3), nullable=False),
        sa.Column('avg_power_watts', sa.Numeric(10, 2), nullable=False),
        sa.Column('peak_hour', sa.Integer, nullable=False),
        sa.Column('estimated_cost_inr', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('uix_daily_device_date', 'daily_summaries', ['device_id', 'date'], unique=True)
    op.create_index('ix_daily_date', 'daily_summaries', ['date'])
    op.create_check_constraint('check_peak_hour_range', 'daily_summaries', 'peak_hour >= 0 AND peak_hour <= 23')
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=False), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('threshold_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_alerts_timestamp', 'alerts', ['timestamp'])
    op.create_index('ix_alerts_is_acknowledged', 'alerts', ['is_acknowledged'])
    op.create_index('ix_alerts_type_timestamp', 'alerts', ['alert_type', 'timestamp'])
    op.create_check_constraint(
        'check_alert_type',
        'alerts',
        "alert_type IN ('spike', 'high_overnight', 'long_runtime', 'bill_threshold')"
    )
    op.create_check_constraint(
        'check_severity',
        'alerts',
        "severity IN ('info', 'warning', 'critical')"
    )


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('daily_summaries')
    op.drop_table('hourly_summaries')
    op.drop_table('readings')
    op.drop_table('devices')
