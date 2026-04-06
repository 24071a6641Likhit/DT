"""Tests for billing service"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.billing_service import BillingService, SlabRate
from app.services.storage_service import StorageService
from app.models import Device, DailySummary


IST = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_calculate_cost_single_slab(session_factory):
    """Test cost calculation within single slab"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    # 50 kWh consumption (within first slab 0-100)
    total_cost, breakdown = billing.calculate_cost(50.0)
    
    # Cost = 50 × ₹3 = ₹150
    assert total_cost == 150.0
    assert len(breakdown) == 1
    assert breakdown[0].units == 50.0
    assert breakdown[0].rate == 3.0
    assert breakdown[0].cost == 150.0


@pytest.mark.asyncio
async def test_calculate_cost_multiple_slabs(session_factory):
    """Test cost calculation across multiple slabs"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    # 350 kWh consumption (spans 3 slabs)
    total_cost, breakdown = billing.calculate_cost(350.0)
    
    # Slab 1 (0-100): 100 × ₹3 = ₹300
    # Slab 2 (101-300): 200 × ₹7.5 = ₹1,500
    # Slab 3 (301-500): 50 × ₹12 = ₹600
    # Total: ₹2,400
    
    assert total_cost == 2400.0
    assert len(breakdown) == 3
    
    assert breakdown[0].units == 100.0
    assert breakdown[0].cost == 300.0
    
    assert breakdown[1].units == 200.0
    assert breakdown[1].cost == 1500.0
    
    assert breakdown[2].units == 50.0
    assert breakdown[2].cost == 600.0


@pytest.mark.asyncio
async def test_calculate_cost_highest_slab(session_factory):
    """Test cost calculation in highest slab (unlimited)"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    # 650 kWh consumption (reaches unlimited slab)
    total_cost, breakdown = billing.calculate_cost(650.0)
    
    # Slab 1: 100 × ₹3 = ₹300
    # Slab 2: 200 × ₹7.5 = ₹1,500
    # Slab 3: 200 × ₹12 = ₹2,400
    # Slab 4 (501+): 150 × ₹15 = ₹2,250
    # Total: ₹6,450
    
    assert total_cost == 6450.0
    assert len(breakdown) == 4
    assert breakdown[3].units == 150.0
    assert breakdown[3].rate == 15.0
    assert breakdown[3].cost == 2250.0


@pytest.mark.asyncio
async def test_get_current_month_bill(session_factory):
    """Test current month bill estimation"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    # Create device
    async with session_factory() as session:
        device = Device(name="Main Meter", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create daily summaries for current month
    now = datetime.now(IST)
    async with session_factory() as session:
        summaries = []
        # Create 10 days of data, each with 10 kWh
        for day in range(1, 11):
            summary_date = date(now.year, now.month, day)
            summaries.append(DailySummary(
                device_id=device_id,
                summary_date=summary_date,
                total_kwh=Decimal('10.0'),
                avg_power_watts=Decimal('3000'),
                peak_hour=20,
                estimated_cost_inr=Decimal('30.0')  # Will be recalculated
            ))
        session.add_all(summaries)
        await session.commit()
    
    # Get bill estimate
    estimate = await billing.get_current_month_bill(device_id)
    
    # Should have 100 kWh total (10 days × 10 kWh)
    assert estimate.total_kwh == 100.0
    # Cost: 100 × ₹3 = ₹300 (all in first slab)
    assert estimate.total_cost_inr == 300.0
    assert len(estimate.slab_breakdown) == 1
    assert estimate.billing_period_start.startswith(f"{now.year:04d}-{now.month:02d}")


@pytest.mark.asyncio
async def test_get_monthly_comparison(session_factory):
    """Test monthly comparison data"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    async with session_factory() as session:
        device = Device(name="Main", device_type="main_meter", is_active=True)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        device_id = device.id
    
    # Create data for last 3 months
    now = datetime.now(IST)
    async with session_factory() as session:
        summaries = []
        
        # Current month: 5 days × 20 kWh = 100 kWh
        for day in range(1, 6):
            summaries.append(DailySummary(
                device_id=device_id,
                summary_date=date(now.year, now.month, day),
                total_kwh=Decimal('20.0'),
                avg_power_watts=Decimal('3000'),
                peak_hour=20,
                estimated_cost_inr=Decimal('0')
            ))
        
        # Last month: 30 days × 15 kWh = 450 kWh
        last_month = now.month - 1 if now.month > 1 else 12
        last_year = now.year if now.month > 1 else now.year - 1
        for day in range(1, 31):
            try:
                summary_date = date(last_year, last_month, day)
                summaries.append(DailySummary(
                    device_id=device_id,
                    summary_date=summary_date,
                    total_kwh=Decimal('15.0'),
                    avg_power_watts=Decimal('3000'),
                    peak_hour=20,
                    estimated_cost_inr=Decimal('0')
                ))
            except ValueError:
                pass  # Skip invalid dates (e.g., Feb 30)
        
        session.add_all(summaries)
        await session.commit()
    
    # Get comparison
    comparison = await billing.get_monthly_comparison(device_id, months=3)
    
    # Should have at least 2 months of data
    assert len(comparison) >= 2
    
    # Check current month data exists
    current_month_str = f"{now.year:04d}-{now.month:02d}"
    current_data = next((m for m in comparison if m['month'] == current_month_str), None)
    assert current_data is not None
    assert current_data['total_kwh'] == 100.0


@pytest.mark.asyncio
async def test_update_slab_rates(session_factory):
    """Test updating slab rate configuration"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    # Define custom rates
    custom_rates = [
        SlabRate(min_units=0, max_units=50, rate_per_unit=2.0),
        SlabRate(min_units=51, max_units=150, rate_per_unit=5.0),
        SlabRate(min_units=151, max_units=None, rate_per_unit=10.0),
    ]
    
    billing.update_slab_rates(custom_rates)
    
    # Test with custom rates
    # 200 kWh:
    # Slab 1: 50 × ₹2 = ₹100
    # Slab 2: 100 × ₹5 = ₹500
    # Slab 3: 50 × ₹10 = ₹500
    # Total: ₹1,100
    total_cost, breakdown = billing.calculate_cost(200.0)
    
    assert total_cost == 1100.0
    assert len(breakdown) == 3


@pytest.mark.asyncio
async def test_get_slab_rates(session_factory):
    """Test getting slab rate configuration"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    rates = billing.get_slab_rates()
    
    assert len(rates) == 4  # Default has 4 slabs
    assert rates[0]['min_units'] == 0
    assert rates[0]['max_units'] == 100
    assert rates[0]['rate_per_unit'] == 3.0
    assert '0-100' in rates[0]['slab_label']
    
    # Last slab should be unlimited
    assert rates[-1]['max_units'] is None
    assert '501+' in rates[-1]['slab_label']


@pytest.mark.asyncio
async def test_calculate_cost_zero_consumption(session_factory):
    """Test cost calculation with zero consumption"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    total_cost, breakdown = billing.calculate_cost(0.0)
    
    assert total_cost == 0.0
    assert len(breakdown) == 0


@pytest.mark.asyncio
async def test_calculate_cost_fractional_units(session_factory):
    """Test cost calculation with fractional kWh"""
    storage = StorageService(session_factory)
    billing = BillingService(storage)
    
    # 42.5 kWh (within first slab)
    total_cost, breakdown = billing.calculate_cost(42.5)
    
    # Cost = 42.5 × ₹3 = ₹127.50
    assert total_cost == 127.5
    assert breakdown[0].units == 42.5
    assert breakdown[0].cost == 127.5
