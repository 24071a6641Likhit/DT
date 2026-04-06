"""Seed initial devices

Revision ID: 002
Revises: 001
Create Date: 2026-04-05 14:00:00

"""
from alembic import op
import uuid

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Generate UUIDs for devices
    main_meter_id = uuid.uuid4()
    ac_id = uuid.uuid4()
    geyser_id = uuid.uuid4()
    pump_id = uuid.uuid4()
    
    # Insert seed devices
    op.execute(f"""
        INSERT INTO devices (id, name, device_type, location, is_active)
        VALUES
            ('{main_meter_id}', 'Main Building Meter', 'main_meter', 'Distribution Panel', true),
            ('{ac_id}', 'AC Unit', 'smart_plug', 'Floor 1, Common Room', true),
            ('{geyser_id}', 'Water Geyser', 'smart_plug', 'Floor 2, Bathroom Block', true),
            ('{pump_id}', 'Water Pump', 'smart_plug', 'Ground Floor, Pump Room', true)
    """)
    
    # Write device IDs to a config file for application use
    import os
    config_path = os.path.join(os.path.dirname(__file__), '../../device_ids.txt')
    with open(config_path, 'w') as f:
        f.write(f"MAIN_METER_ID={main_meter_id}\n")
        f.write(f"AC_ID={ac_id}\n")
        f.write(f"GEYSER_ID={geyser_id}\n")
        f.write(f"PUMP_ID={pump_id}\n")
    
    print(f"\n✓ Seed devices created")
    print(f"  Main Meter: {main_meter_id}")
    print(f"  AC Unit: {ac_id}")
    print(f"  Geyser: {geyser_id}")
    print(f"  Pump: {pump_id}")
    print(f"  Device IDs saved to: {config_path}\n")


def downgrade() -> None:
    op.execute("DELETE FROM devices")
    
    # Remove config file
    import os
    config_path = os.path.join(os.path.dirname(__file__), '../../device_ids.txt')
    if os.path.exists(config_path):
        os.remove(config_path)
