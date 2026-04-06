"""Energy consumption simulator

Generates realistic power consumption data for:
- 1 main building meter
- 3 smart plug appliances (AC, Geyser, Water Pump)

Uses probabilistic state machines with time-of-day patterns.
"""

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from zoneinfo import ZoneInfo
from decimal import Decimal


@dataclass
class SimulatedReading:
    """Single simulated power reading"""
    device_id: UUID
    device_name: str
    timestamp: datetime
    power_watts: float
    voltage_volts: Optional[float] = None
    current_amps: Optional[float] = None
    state: Optional[bool] = None  # on/off for smart plugs


class ApplianceSimulator:
    """Base class for appliance simulation with probabilistic state machine"""
    
    def __init__(self, device_id: UUID, device_name: str, base_power_watts: float, power_variance: float):
        self.device_id = device_id
        self.device_name = device_name
        self.base_power_watts = base_power_watts
        self.power_variance = power_variance
        self.is_on = False
        # FIX: Use naive datetime for consistency
        self.last_state_change = datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    
    def should_be_on(self, current_time: datetime) -> bool:
        """Override in subclasses - determines if appliance should be on"""
        raise NotImplementedError
    
    def generate_power(self) -> float:
        """Generate power reading with gaussian noise"""
        if not self.is_on:
            return 0.0
        
        # Add gaussian noise (±power_variance)
        noise = random.gauss(0, self.power_variance / 3)  # 99.7% within ±variance
        power = self.base_power_watts + noise
        
        return max(0.0, power)
    
    def generate_reading(self, current_time: datetime) -> SimulatedReading:
        """Generate one reading for current moment"""
        # Update state based on time-of-day probability
        should_be_on = self.should_be_on(current_time)
        
        # State transitions with some hysteresis (don't flip every second)
        time_since_change = (current_time - self.last_state_change).total_seconds()
        
        if should_be_on and not self.is_on and time_since_change > 60:
            # Turn on if should be on and was off for >1 minute
            if random.random() < 0.3:  # 30% chance to turn on each poll
                self.is_on = True
                self.last_state_change = current_time
        elif not should_be_on and self.is_on and time_since_change > 60:
            # Turn off if should be off and was on for >1 minute
            if random.random() < 0.5:  # 50% chance to turn off each poll
                self.is_on = False
                self.last_state_change = current_time
        
        power = self.generate_power()
        
        return SimulatedReading(
            device_id=self.device_id,
            device_name=self.device_name,
            timestamp=current_time,
            power_watts=round(power, 2),
            state=self.is_on
        )


class ACSimulator(ApplianceSimulator):
    """Air Conditioner - High power, peak usage 18:00-23:00"""
    
    def __init__(self, device_id: UUID, device_name: str):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            base_power_watts=1500.0,
            power_variance=150.0
        )
        self.peak_hours = [18, 19, 20, 21, 22, 23]
        self.off_peak_hours = [0, 1, 2, 3, 4, 5]
    
    def should_be_on(self, current_time: datetime) -> bool:
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5
        
        if hour in self.peak_hours:
            # High probability during evening hours
            prob = 0.95 if is_weekend else 0.80
            return random.random() < prob
        elif hour in self.off_peak_hours:
            # Very low probability at night
            return random.random() < 0.05
        else:
            # Moderate probability during day
            prob = 0.50 if is_weekend else 0.35
            return random.random() < prob


class GeyserSimulator(ApplianceSimulator):
    """Water Geyser - Medium-high power, peak usage morning and evening"""
    
    def __init__(self, device_id: UUID, device_name: str):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            base_power_watts=2000.0,
            power_variance=100.0
        )
        self.morning_peak = [6, 7, 8, 9]
        self.evening_peak = [18, 19, 20, 21]
    
    def should_be_on(self, current_time: datetime) -> bool:
        hour = current_time.hour
        
        if hour in self.morning_peak or hour in self.evening_peak:
            # High probability during bathing times
            return random.random() < 0.85
        else:
            # Low probability rest of day
            return random.random() < 0.10


class PumpSimulator(ApplianceSimulator):
    """Water Pump - Medium power, sporadic usage throughout day"""
    
    def __init__(self, device_id: UUID, device_name: str):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            base_power_watts=750.0,
            power_variance=50.0
        )
    
    def should_be_on(self, current_time: datetime) -> bool:
        hour = current_time.hour
        
        # Higher usage during morning and evening
        if hour in [6, 7, 8, 9, 10]:
            return random.random() < 0.45
        elif hour in [17, 18, 19, 20, 21]:
            return random.random() < 0.45
        elif hour in [0, 1, 2, 3, 4, 5]:
            # Rare night usage
            return random.random() < 0.05
        else:
            # Moderate daytime usage
            return random.random() < 0.20


class MainMeterSimulator:
    """Main building meter - sums all appliances + background load"""
    
    def __init__(self, device_id: UUID, device_name: str):
        self.device_id = device_id
        self.device_name = device_name
        self.spike_active = False
        self.spike_start_time = None
        self.spike_multiplier = 1.0
    
    def _calculate_background(self, current_time: datetime) -> float:
        """Calculate background load (lights, fans, misc)"""
        hour = current_time.hour
        
        # Background varies by time of day
        if hour in [18, 19, 20, 21, 22, 23]:
            base = 500.0  # High evening usage (lights on)
        elif hour in [6, 7, 8, 9]:
            base = 400.0  # Moderate morning usage
        elif hour in [0, 1, 2, 3, 4, 5]:
            base = 200.0  # Minimal night usage
        else:
            base = 350.0  # Normal daytime
        
        # Add random variance
        variance = random.gauss(0, 50)
        return max(150, base + variance)
    
    def _check_spike_trigger(self, current_time: datetime) -> None:
        """Randomly trigger consumption spikes (5% chance)"""
        if self.spike_active:
            # Check if spike should end (15-30 second duration)
            if self.spike_start_time:
                duration = (current_time - self.spike_start_time).total_seconds()
                if duration > random.uniform(15, 30):
                    self.spike_active = False
                    self.spike_start_time = None
                    self.spike_multiplier = 1.0
        else:
            # 5% chance to start spike
            if random.random() < 0.05:
                self.spike_active = True
                self.spike_start_time = current_time
                self.spike_multiplier = random.uniform(1.6, 2.0)  # 60-100% spike
    
    def generate_reading(
        self,
        appliance_readings: List[SimulatedReading],
        current_time: datetime
    ) -> SimulatedReading:
        """Generate main meter reading (sum of all loads)"""
        # Sum all appliance power
        total_appliance_power = sum(r.power_watts for r in appliance_readings)
        
        # Add background load
        background = self._calculate_background(current_time)
        
        # Check for spike events
        self._check_spike_trigger(current_time)
        
        # Total power
        total_power = total_appliance_power + background
        
        # Apply spike if active
        if self.spike_active:
            total_power *= self.spike_multiplier
        
        # Add measurement jitter (±3%)
        jitter = random.gauss(0, total_power * 0.015)
        final_power = max(0, total_power + jitter)
        
        # Calculate voltage and current
        voltage = random.gauss(230.0, 2.0)  # 230V ±2V
        current = final_power / voltage if voltage > 0 else 0
        
        return SimulatedReading(
            device_id=self.device_id,
            device_name=self.device_name,
            timestamp=current_time,
            power_watts=round(final_power, 2),
            voltage_volts=round(voltage, 2),
            current_amps=round(current, 2),
            state=None
        )


class EnergySimulator:
    """Main simulator coordinating all devices"""
    
    def __init__(self, devices: List[Dict]):
        """
        Initialize simulator with device configuration
        
        Args:
            devices: List of dicts with 'id', 'name', 'device_type'
        """
        # Find devices by type
        main_meter = next(d for d in devices if d['device_type'] == 'main_meter')
        smart_plugs = [d for d in devices if d['device_type'] == 'smart_plug']
        
        # Initialize main meter
        self.main_meter = MainMeterSimulator(
            device_id=main_meter['id'],
            device_name=main_meter['name']
        )
        
        # Initialize appliances (map by name)
        self.appliances = []
        for device in smart_plugs:
            name_lower = device['name'].lower()
            if 'ac' in name_lower:
                simulator = ACSimulator(device['id'], device['name'])
            elif 'geyser' in name_lower:
                simulator = GeyserSimulator(device['id'], device['name'])
            elif 'pump' in name_lower:
                simulator = PumpSimulator(device['id'], device['name'])
            else:
                # Default generic appliance
                simulator = ApplianceSimulator(
                    device_id=device['id'],
                    device_name=device['name'],
                    base_power_watts=1000.0,
                    power_variance=100.0
                )
            self.appliances.append(simulator)
        
        # Track cumulative energy
        self.cumulative_energy: Dict[UUID, float] = {}
        self.last_reading_time = None
    
    def generate_readings(self) -> List[SimulatedReading]:
        """Generate one reading per device for current moment"""
        # FIX: Use naive datetime since DB stores timezone=False
        # Create timezone-aware then strip for DB compatibility
        current_time = datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        
        # Generate appliance readings
        appliance_readings = [
            appliance.generate_reading(current_time)
            for appliance in self.appliances
        ]
        
        # Generate main meter reading (depends on appliances)
        main_reading = self.main_meter.generate_reading(
            appliance_readings,
            current_time
        )
        
        # Update cumulative energy (kWh)
        if self.last_reading_time:
            time_delta_hours = (current_time - self.last_reading_time).total_seconds() / 3600
            
            for reading in [main_reading] + appliance_readings:
                if reading.device_id not in self.cumulative_energy:
                    self.cumulative_energy[reading.device_id] = 0.0
                
                # kWh = kW * hours
                kwh_increment = (reading.power_watts / 1000) * time_delta_hours
                self.cumulative_energy[reading.device_id] += kwh_increment
        else:
            # First reading - initialize energy to 0
            for reading in [main_reading] + appliance_readings:
                self.cumulative_energy[reading.device_id] = 0.0
        
        self.last_reading_time = current_time
        
        return [main_reading] + appliance_readings
    
    def get_cumulative_energy(self, device_id: UUID) -> float:
        """Get cumulative energy for a device"""
        return self.cumulative_energy.get(device_id, 0.0)
