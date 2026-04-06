"""Fix alert type constraint

Revision ID: 003
Revises: 002
Create Date: 2026-04-06 01:50:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint('check_alert_type', 'alerts', type_='check')
    
    # Add the new constraint with overload and high_consumption
    op.create_check_constraint(
        'check_alert_type',
        'alerts',
        "alert_type IN ('spike', 'overload', 'high_consumption', 'high_overnight', 'long_runtime', 'bill_threshold')"
    )
    
    print("\n✓ Alert type constraint updated to include 'overload' and 'high_consumption'")


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint('check_alert_type', 'alerts', type_='check')
    
    # Restore the old constraint
    op.create_check_constraint(
        'check_alert_type',
        'alerts',
        "alert_type IN ('spike', 'high_overnight', 'long_runtime', 'bill_threshold')"
    )
