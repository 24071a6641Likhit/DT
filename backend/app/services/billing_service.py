"""Billing service for electricity cost calculation"""

from typing import List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal
from datetime import date, datetime
from calendar import monthrange
from zoneinfo import ZoneInfo

from app.services.storage_service import StorageService


@dataclass
class SlabRate:
    """Electricity slab rate configuration"""
    min_units: int
    max_units: Optional[int]  # None for last slab (unlimited)
    rate_per_unit: float  # ₹ per kWh
    
    def slab_label(self) -> str:
        """Get human-readable slab label"""
        if self.max_units is None:
            return f"{self.min_units}+ units"
        return f"{self.min_units}-{self.max_units} units"


@dataclass
class SlabBreakdown:
    """Breakdown of cost for one slab"""
    slab: str
    units: float
    rate: float
    cost: float


@dataclass
class BillEstimate:
    """Complete bill estimate with slab breakdown"""
    billing_period_start: str  # ISO date
    billing_period_end: str    # ISO date
    total_kwh: float
    total_cost_inr: float
    slab_breakdown: List[dict]  # List of SlabBreakdown as dicts


class BillingService:
    """Calculate electricity costs using Maharashtra slab rates"""
    
    # Default Maharashtra residential slab rates (configurable)
    DEFAULT_SLAB_RATES = [
        SlabRate(min_units=0, max_units=100, rate_per_unit=3.0),
        SlabRate(min_units=101, max_units=300, rate_per_unit=7.5),
        SlabRate(min_units=301, max_units=500, rate_per_unit=12.0),
        SlabRate(min_units=501, max_units=None, rate_per_unit=15.0),
    ]
    
    def __init__(
        self,
        storage: StorageService,
        slab_rates: Optional[List[SlabRate]] = None
    ):
        """
        Initialize billing service.
        
        Args:
            storage: Storage service for querying consumption data
            slab_rates: Optional custom slab rates (defaults to Maharashtra rates)
        """
        self.storage = storage
        self.slab_rates = slab_rates or self.DEFAULT_SLAB_RATES
        self.ist = ZoneInfo("Asia/Kolkata")
    
    def calculate_cost(self, total_kwh: float) -> tuple[float, List[SlabBreakdown]]:
        """
        Calculate total cost and slab breakdown for given consumption.
        
        Example:
        - 350 kWh consumed
        - Slab 1 (0-100): 100 units × ₹3 = ₹300
        - Slab 2 (101-300): 200 units × ₹7.5 = ₹1,500
        - Slab 3 (301-500): 50 units × ₹12 = ₹600
        - Total: ₹2,400
        
        Args:
            total_kwh: Total consumption in kWh
            
        Returns:
            Tuple of (total_cost, breakdown_list)
        """
        remaining_units = total_kwh
        total_cost = 0.0
        breakdown = []
        
        for slab in self.slab_rates:
            if remaining_units <= 0:
                break
            
            # Calculate units consumed in this slab
            # For inclusive ranges: 0-100 has 101 units, 101-300 has 200 units
            slab_capacity = (
                (slab.max_units - slab.min_units + 1)
                if slab.max_units is not None
                else float('inf')
            )
            
            units_in_slab = min(remaining_units, slab_capacity)
            cost_in_slab = units_in_slab * slab.rate_per_unit
            
            breakdown.append(SlabBreakdown(
                slab=slab.slab_label(),
                units=round(units_in_slab, 2),
                rate=slab.rate_per_unit,
                cost=round(cost_in_slab, 2)
            ))
            
            total_cost += cost_in_slab
            remaining_units -= units_in_slab
        
        return round(total_cost, 2), breakdown
    
    async def get_current_month_bill(self, main_meter_id: str) -> BillEstimate:
        """
        Get bill estimate for current month.
        
        Args:
            main_meter_id: Main meter device ID
            
        Returns:
            BillEstimate with period, consumption, cost, and breakdown
        """
        # Get current month date range
        now = datetime.now(self.ist)
        start_date = date(now.year, now.month, 1)
        _, last_day = monthrange(now.year, now.month)
        end_date = date(now.year, now.month, last_day)
        
        # Get daily summaries for the month
        summaries = await self.storage.get_daily_summaries_range(
            main_meter_id,
            start_date,
            end_date
        )
        
        # Calculate total consumption
        total_kwh = float(sum(s.total_kwh for s in summaries))
        
        # Calculate cost and breakdown
        total_cost, breakdown = self.calculate_cost(total_kwh)
        
        return BillEstimate(
            billing_period_start=start_date.isoformat(),
            billing_period_end=end_date.isoformat(),
            total_kwh=round(total_kwh, 2),
            total_cost_inr=total_cost,
            slab_breakdown=[asdict(b) for b in breakdown]
        )
    
    async def get_monthly_comparison(
        self,
        main_meter_id: str,
        months: int = 6
    ) -> List[dict]:
        """
        Get last N months consumption and cost comparison.
        
        Args:
            main_meter_id: Main meter device ID
            months: Number of months to include (default 6)
            
        Returns:
            List of monthly summaries with month, total_kwh, total_cost_inr
        """
        monthly_data = []
        now = datetime.now(self.ist)
        
        for i in range(months):
            # Calculate month offset
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            
            # Get month date range
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Don't query future months
            if start_date > now.date():
                continue
            
            # Get daily summaries for the month
            summaries = await self.storage.get_daily_summaries_range(
                main_meter_id,
                start_date,
                end_date
            )
            
            # Calculate total
            total_kwh = float(sum(s.total_kwh for s in summaries))
            total_cost, _ = self.calculate_cost(total_kwh)
            
            monthly_data.append({
                'month': f"{year:04d}-{month:02d}",
                'total_kwh': round(total_kwh, 2),
                'total_cost_inr': total_cost
            })
        
        # Return in chronological order (oldest first)
        return list(reversed(monthly_data))
    
    async def estimate_daily_cost(
        self,
        main_meter_id: str,
        target_date: date
    ) -> float:
        """
        Get cost estimate for a specific day.
        
        Args:
            main_meter_id: Main meter device ID
            target_date: Date to calculate cost for
            
        Returns:
            Estimated cost in ₹ for the day
        """
        # Get daily summary
        summary = await self.storage.get_daily_summary(main_meter_id, target_date)
        
        if summary is None:
            return 0.0
        
        # For daily cost, we use simplified average rate calculation
        # (actual billing is cumulative monthly, but this gives daily estimate)
        total_cost, _ = self.calculate_cost(float(summary.total_kwh))
        
        return total_cost
    
    def update_slab_rates(self, new_rates: List[SlabRate]) -> None:
        """
        Update slab rate configuration.
        
        Args:
            new_rates: New slab rate list
        """
        # Validate rates are sorted by min_units
        for i in range(len(new_rates) - 1):
            if new_rates[i].min_units >= new_rates[i + 1].min_units:
                raise ValueError("Slab rates must be sorted by min_units")
        
        # Validate last slab has no max
        if new_rates[-1].max_units is not None:
            raise ValueError("Last slab must have max_units=None")
        
        self.slab_rates = new_rates
    
    def get_slab_rates(self) -> List[dict]:
        """
        Get current slab rate configuration.
        
        Returns:
            List of slab rate dicts
        """
        return [
            {
                'min_units': slab.min_units,
                'max_units': slab.max_units,
                'rate_per_unit': slab.rate_per_unit,
                'slab_label': slab.slab_label()
            }
            for slab in self.slab_rates
        ]
