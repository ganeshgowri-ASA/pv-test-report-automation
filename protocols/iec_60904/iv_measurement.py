"""
IEC 60904-1: I-V Curve Measurement for Photovoltaic Devices

This module implements I-V curve measurement using 4-wire Kelvin sensing
according to IEC 60904-1 standard.

Key Features:
- 4-wire Kelvin sensing for accurate voltage measurement
- Voltage sweep from 0V to Voc + 10%
- Current range: 0 to Isc + 10%
- Minimum 100 data points per curve
- Measurement speed: <20ms per point
- Automatic parameter extraction: Voc, Isc, Vmp, Imp, Pmax, FF
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json


class MeasurementMode(Enum):
    """Measurement sweep modes"""
    VOLTAGE_SWEEP = "voltage_sweep"
    CURRENT_SWEEP = "current_sweep"
    DUAL_SWEEP = "dual_sweep"


class WireConfiguration(Enum):
    """Wire configuration for measurement"""
    TWO_WIRE = 2
    FOUR_WIRE_KELVIN = 4


@dataclass
class IVResult:
    """
    Results from I-V curve measurement

    Attributes:
        module_serial: Module serial number
        voc: Open circuit voltage (V)
        isc: Short circuit current (A)
        vmp: Maximum power point voltage (V)
        imp: Maximum power point current (A)
        pmax: Maximum power (W)
        ff: Fill factor
        efficiency: Conversion efficiency (%)
        area: Module area (m²)
        irradiance: Irradiance during measurement (W/m²)
        temperature: Module temperature (°C)
        voltage_data: Array of voltage measurements (V)
        current_data: Array of current measurements (A)
        power_data: Array of power values (W)
        timestamp: Measurement timestamp
        measurement_time: Total measurement time (s)
        num_points: Number of data points
        wire_config: Wire configuration used
        spectral_mismatch_factor: Spectral mismatch correction factor
        metadata: Additional measurement metadata
    """
    module_serial: str
    voc: float
    isc: float
    vmp: float
    imp: float
    pmax: float
    ff: float
    efficiency: float
    area: float
    irradiance: float
    temperature: float
    voltage_data: np.ndarray
    current_data: np.ndarray
    power_data: np.ndarray
    timestamp: datetime
    measurement_time: float
    num_points: int
    wire_config: WireConfiguration
    spectral_mismatch_factor: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate measurement results"""
        if self.voc <= 0:
            raise ValueError("Open circuit voltage must be positive")
        if self.isc <= 0:
            raise ValueError("Short circuit current must be positive")
        if self.pmax <= 0:
            raise ValueError("Maximum power must be positive")
        if not 0 <= self.ff <= 1:
            raise ValueError("Fill factor must be between 0 and 1")
        if self.num_points < 100:
            raise ValueError("Minimum 100 data points required per IEC 60904-1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return {
            'module_serial': self.module_serial,
            'voc': float(self.voc),
            'isc': float(self.isc),
            'vmp': float(self.vmp),
            'imp': float(self.imp),
            'pmax': float(self.pmax),
            'ff': float(self.ff),
            'efficiency': float(self.efficiency),
            'area': float(self.area),
            'irradiance': float(self.irradiance),
            'temperature': float(self.temperature),
            'voltage_data': self.voltage_data.tolist(),
            'current_data': self.current_data.tolist(),
            'power_data': self.power_data.tolist(),
            'timestamp': self.timestamp.isoformat(),
            'measurement_time': float(self.measurement_time),
            'num_points': int(self.num_points),
            'wire_config': self.wire_config.value,
            'spectral_mismatch_factor': float(self.spectral_mismatch_factor),
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Export result as JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def get_series_resistance(self) -> float:
        """
        Calculate series resistance from I-V curve slope near Voc
        Rs = -dV/dI at Voc
        """
        # Find points near Voc (90-100% of Voc) with sufficient current range
        voc_region = (self.voltage_data >= 0.90 * self.voc) & (self.voltage_data <= self.voc)
        if np.sum(voc_region) < 3:
            return 0.0

        v_region = self.voltage_data[voc_region]
        i_region = self.current_data[voc_region]

        # Need sufficient current variation for good fit
        if np.max(i_region) - np.min(i_region) < 0.001:
            return 0.0

        try:
            # Linear fit: V = a + b*I, so Rs = -b (dV/dI)
            coeffs = np.polyfit(i_region, v_region, 1)
            rs = -coeffs[0]  # Negative of slope
            return max(0.0, min(rs, 10.0))  # Clamp to reasonable range
        except (np.linalg.LinAlgError, ValueError):
            return 0.0

    def get_shunt_resistance(self) -> float:
        """
        Calculate shunt resistance from I-V curve slope near Isc
        Rsh = dV/dI at Isc
        """
        # Find points near Isc (0-5% of Voc)
        isc_region = (self.voltage_data <= 0.05 * self.voc)
        if np.sum(isc_region) < 2:
            return float('inf')

        v_region = self.voltage_data[isc_region]
        i_region = self.current_data[isc_region]

        # Linear fit
        coeffs = np.polyfit(i_region, v_region, 1)
        rsh = coeffs[0]

        return max(0.0, rsh)  # Rsh should be positive


class IVMeasurement:
    """
    I-V Curve Measurement System (IEC 60904-1)

    Implements I-V curve measurement using 4-wire Kelvin sensing
    with automated parameter extraction and analysis.
    """

    def __init__(
        self,
        module_serial: str,
        area: float,
        wire_config: WireConfiguration = WireConfiguration.FOUR_WIRE_KELVIN,
        min_points: int = 100,
        max_measurement_time_per_point: float = 0.020,  # 20ms max per point
        voltage_overshoot: float = 0.10,  # 10% overshoot
        current_overshoot: float = 0.10   # 10% overshoot
    ):
        """
        Initialize I-V measurement system

        Args:
            module_serial: Module serial number
            area: Module area in m²
            wire_config: Wire configuration (2-wire or 4-wire Kelvin)
            min_points: Minimum number of measurement points (default: 100)
            max_measurement_time_per_point: Maximum time per point in seconds
            voltage_overshoot: Voltage range overshoot factor (default: 0.10 = 10%)
            current_overshoot: Current range overshoot factor (default: 0.10 = 10%)
        """
        self.module_serial = module_serial
        self.area = area
        self.wire_config = wire_config
        self.min_points = max(100, min_points)  # IEC 60904-1 requires min 100 points
        self.max_measurement_time_per_point = max_measurement_time_per_point
        self.voltage_overshoot = voltage_overshoot
        self.current_overshoot = current_overshoot

        # Validate 4-wire configuration for compliance
        if wire_config != WireConfiguration.FOUR_WIRE_KELVIN:
            import warnings
            warnings.warn(
                "IEC 60904-1 recommends 4-wire Kelvin sensing for accurate measurements",
                UserWarning
            )

    def measure_iv_curve(
        self,
        irradiance: float = 1000.0,
        temperature: float = 25.0,
        spectral_mismatch_factor: float = 1.0,
        num_points: Optional[int] = None,
        mode: MeasurementMode = MeasurementMode.VOLTAGE_SWEEP
    ) -> IVResult:
        """
        Perform I-V curve measurement

        Args:
            irradiance: Irradiance in W/m² (default: 1000 W/m² STC)
            temperature: Module temperature in °C (default: 25°C STC)
            spectral_mismatch_factor: Spectral mismatch correction factor
            num_points: Number of measurement points (default: min_points)
            mode: Measurement mode (voltage sweep, current sweep, or dual)

        Returns:
            IVResult object containing all measurement data and parameters
        """
        start_time = datetime.now()

        if num_points is None:
            num_points = self.min_points
        else:
            num_points = max(self.min_points, num_points)

        # Simulate I-V curve measurement
        # In production, this would interface with actual hardware
        voltage_data, current_data, measurement_time = self._perform_measurement(
            irradiance, temperature, num_points, mode
        )

        # Calculate power
        power_data = voltage_data * current_data

        # Extract parameters
        voc = self._extract_voc(voltage_data, current_data)
        isc = self._extract_isc(voltage_data, current_data)
        vmp, imp, pmax = self._extract_mpp(voltage_data, current_data, power_data)
        ff = self._calculate_fill_factor(voc, isc, pmax)
        efficiency = self._calculate_efficiency(pmax, irradiance)

        # Create result object
        result = IVResult(
            module_serial=self.module_serial,
            voc=voc,
            isc=isc,
            vmp=vmp,
            imp=imp,
            pmax=pmax,
            ff=ff,
            efficiency=efficiency,
            area=self.area,
            irradiance=irradiance,
            temperature=temperature,
            voltage_data=voltage_data,
            current_data=current_data,
            power_data=power_data,
            timestamp=start_time,
            measurement_time=measurement_time,
            num_points=num_points,
            wire_config=self.wire_config,
            spectral_mismatch_factor=spectral_mismatch_factor,
            metadata={
                'measurement_mode': mode.value,
                'voltage_overshoot': self.voltage_overshoot,
                'current_overshoot': self.current_overshoot,
                'standard': 'IEC 60904-1:2020'
            }
        )

        return result

    def _perform_measurement(
        self,
        irradiance: float,
        temperature: float,
        num_points: int,
        mode: MeasurementMode
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Perform actual I-V curve measurement

        This is a simulation. In production, this would interface with:
        - Source measure unit (SMU) for 4-wire measurements
        - Electronic load for voltage/current sweeping
        - Data acquisition system

        Returns:
            Tuple of (voltage_array, current_array, measurement_time)
        """
        import time
        start = time.time()

        # Simulate typical PV module characteristics
        # Temperature coefficients (typical for c-Si)
        temp_coeff_voc = -0.0033  # V/°C per cell
        temp_coeff_isc = 0.00055   # A/°C

        # Reference values at STC (1000 W/m², 25°C)
        voc_stc = 45.0  # V (example for 72-cell module)
        isc_stc = 9.5   # A
        vmp_stc = 37.2  # V
        imp_stc = 9.0   # A

        # Temperature correction
        delta_t = temperature - 25.0
        num_cells = 72  # Typical 72-cell module

        # Voc temperature correction (negative coefficient)
        voc_ref = voc_stc + (num_cells * temp_coeff_voc * delta_t)

        # Isc temperature correction (positive coefficient)
        isc_ref = isc_stc * (1 + temp_coeff_isc * delta_t)

        # Irradiance correction
        isc = isc_ref * (irradiance / 1000.0)

        # Voc increases logarithmically with irradiance
        # But temperature corrected Voc is the base
        thermal_voltage = 0.026 * (temperature + 273.15) / 298.15  # kT/q per cell
        if irradiance > 0:
            voc = voc_ref + num_cells * thermal_voltage * np.log(irradiance / 1000.0)
        else:
            voc = 0.0

        # Generate I-V curve with overshoot
        v_max = voc * (1 + self.voltage_overshoot) if voc > 0 else vmp_stc * 1.5
        voltage_data = np.linspace(0, v_max, num_points)

        # Single diode model parameters (realistic values)
        rs = 0.3    # Series resistance (Ω)
        rsh = 300.0  # Shunt resistance (Ω)
        n = 1.3      # Ideality factor

        # Simplified I-V curve generation using empirical model
        # More stable than full single-diode iteration
        current_data = np.zeros(num_points)

        for i, v in enumerate(voltage_data):
            if v <= 0:
                # At zero voltage, current is Isc
                current_data[i] = isc
            elif v >= voc:
                # Beyond Voc, current is zero
                current_data[i] = 0.0
            else:
                # Empirical model combining exponential and linear terms
                # I = Isc * (1 - C1*(exp(V/C2*Voc)-1)) * (1 - (V/Voc)^C3)
                c1 = 1.0 / (np.exp(1 / (n * num_cells * thermal_voltage / voc * 0.7)) - 1)
                c2 = n * num_cells * thermal_voltage / voc * 0.7
                c3 = 1.5

                # Avoid overflow in exp
                exp_arg = min(v / (c2 * voc), 20)
                exp_term = c1 * (np.exp(exp_arg) - 1)
                linear_term = 1 - (v / voc) ** c3

                i_pv = isc * (1 - exp_term) * linear_term

                # Add resistive effects
                i_shunt = v / rsh
                i_series_loss = (v - 0) / (rs + rsh) if v < voc * 0.9 else 0

                current_data[i] = max(0, i_pv - i_shunt)

        # Simulate measurement time (would be actual measurement time in production)
        measurement_time = time.time() - start

        # Ensure measurement speed compliance
        time_per_point = measurement_time / num_points
        if time_per_point > self.max_measurement_time_per_point:
            import warnings
            warnings.warn(
                f"Measurement time per point ({time_per_point*1000:.1f}ms) exceeds "
                f"specification ({self.max_measurement_time_per_point*1000:.1f}ms)",
                UserWarning
            )

        return voltage_data, current_data, measurement_time

    def _extract_voc(self, voltage: np.ndarray, current: np.ndarray) -> float:
        """Extract open circuit voltage (Voc) - IEC 60904-5"""
        # Find where current crosses zero
        zero_crossings = np.where(np.diff(np.sign(current)))[0]
        if len(zero_crossings) > 0:
            idx = zero_crossings[-1]
            # Linear interpolation for better accuracy
            if idx + 1 < len(voltage):
                v1, i1 = voltage[idx], current[idx]
                v2, i2 = voltage[idx + 1], current[idx + 1]
                voc = v1 - i1 * (v2 - v1) / (i2 - i1)
            else:
                voc = voltage[idx]
        else:
            # If no zero crossing, use voltage at minimum current
            idx = np.argmin(np.abs(current))
            voc = voltage[idx]

        return float(voc)

    def _extract_isc(self, voltage: np.ndarray, current: np.ndarray) -> float:
        """Extract short circuit current (Isc)"""
        # Current at V=0 (or nearest to 0)
        idx = np.argmin(np.abs(voltage))
        if idx > 0:
            # Linear interpolation
            v1, i1 = voltage[idx - 1], current[idx - 1]
            v2, i2 = voltage[idx], current[idx]
            if abs(v2 - v1) > 1e-10:
                isc = i1 - v1 * (i2 - i1) / (v2 - v1)
            else:
                isc = current[idx]
        else:
            isc = current[0]

        return float(isc)

    def _extract_mpp(
        self,
        voltage: np.ndarray,
        current: np.ndarray,
        power: np.ndarray
    ) -> Tuple[float, float, float]:
        """Extract maximum power point (Vmp, Imp, Pmax)"""
        # Find maximum power point
        idx_max = np.argmax(power)
        pmax = power[idx_max]
        vmp = voltage[idx_max]
        imp = current[idx_max]

        # Parabolic interpolation for better accuracy
        if 0 < idx_max < len(power) - 1:
            p1, p2, p3 = power[idx_max - 1], power[idx_max], power[idx_max + 1]
            v1, v2, v3 = voltage[idx_max - 1], voltage[idx_max], voltage[idx_max + 1]

            # Fit parabola and find vertex
            denom = (v1 - v2) * (v1 - v3) * (v2 - v3)
            if abs(denom) > 1e-10:
                a = (v3 * (p2 - p1) + v2 * (p1 - p3) + v1 * (p3 - p2)) / denom
                b = (v3**2 * (p1 - p2) + v2**2 * (p3 - p1) + v1**2 * (p2 - p3)) / denom

                if abs(a) > 1e-10:
                    vmp_refined = -b / (2 * a)
                    if v1 <= vmp_refined <= v3:
                        vmp = vmp_refined
                        # Interpolate current at refined Vmp
                        imp = np.interp(vmp, voltage, current)
                        pmax = vmp * imp

        return float(vmp), float(imp), float(pmax)

    def _calculate_fill_factor(self, voc: float, isc: float, pmax: float) -> float:
        """Calculate fill factor: FF = Pmax / (Voc × Isc)"""
        if voc * isc == 0:
            return 0.0
        ff = pmax / (voc * isc)
        return min(1.0, max(0.0, ff))  # Clamp to [0, 1]

    def _calculate_efficiency(self, pmax: float, irradiance: float) -> float:
        """Calculate conversion efficiency: η = Pmax / (Area × Irradiance) × 100%"""
        if self.area * irradiance == 0:
            return 0.0
        efficiency = (pmax / (self.area * irradiance)) * 100.0
        return float(efficiency)

    def perform_linearity_test(
        self,
        irradiance_levels: List[float],
        temperature: float = 25.0
    ) -> Dict[str, Any]:
        """
        Perform linearity test (IEC 60904-10)

        Tests linearity of Isc vs. irradiance relationship

        Args:
            irradiance_levels: List of irradiance levels to test (W/m²)
            temperature: Module temperature (°C)

        Returns:
            Dictionary with linearity test results
        """
        results = []

        for irradiance in irradiance_levels:
            iv_result = self.measure_iv_curve(
                irradiance=irradiance,
                temperature=temperature
            )
            results.append({
                'irradiance': irradiance,
                'isc': iv_result.isc,
                'voc': iv_result.voc,
                'pmax': iv_result.pmax
            })

        # Linear regression for Isc vs irradiance
        irr_array = np.array([r['irradiance'] for r in results])
        isc_array = np.array([r['isc'] for r in results])

        coeffs = np.polyfit(irr_array, isc_array, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculate R² (coefficient of determination)
        isc_fit = slope * irr_array + intercept
        ss_res = np.sum((isc_array - isc_fit) ** 2)
        ss_tot = np.sum((isc_array - np.mean(isc_array)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Linearity deviation
        max_deviation = np.max(np.abs((isc_array - isc_fit) / isc_fit)) * 100

        return {
            'standard': 'IEC 60904-10',
            'irradiance_levels': irradiance_levels,
            'results': results,
            'linearity': {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_squared),
                'max_deviation_percent': float(max_deviation)
            },
            'compliant': r_squared >= 0.99 and max_deviation <= 2.0
        }
