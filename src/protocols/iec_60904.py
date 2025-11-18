"""
IEC 60904 - Photovoltaic Devices - I-V Characteristics Measurement

This module implements IEC 60904-1 (Measurement of photovoltaic current-voltage characteristics)
and related standards for PV device characterization.

Standard Reference Conditions (STC):
- Irradiance: 1000 W/m²
- Spectrum: AM1.5 global
- Cell temperature: 25°C

Key Parameters Calculated:
- Short-circuit current (Isc)
- Open-circuit voltage (Voc)
- Maximum power point (Pmp, Vmp, Imp)
- Fill factor (FF)
- Efficiency (η)
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

from .base_protocol import (
    BaseProtocol, ProtocolResult, Uncertainty, TestStatus, DataQuality
)


@dataclass
class IVCurveData:
    """Container for I-V curve measurement data"""
    voltage: np.ndarray
    current: np.ndarray
    irradiance: float
    temperature: float
    area: float  # Module area in m²
    timestamp: str


class IEC60904(BaseProtocol):
    """
    IEC 60904 I-V Characteristics Measurement Protocol

    Implements measurement and analysis of photovoltaic current-voltage
    characteristics according to IEC 60904-1 standard.
    """

    # Standard Test Conditions
    STC_IRRADIANCE = 1000.0  # W/m²
    STC_TEMPERATURE = 25.0    # °C
    STC_SPECTRUM = "AM1.5G"

    def __init__(self):
        """Initialize IEC 60904 protocol handler"""
        super().__init__("IEC 60904-1", "2020")

        # Default uncertainty sources (can be updated based on equipment)
        self.uncertainty_sources = {
            'voltage_measurement': 0.002,      # 0.2% of reading
            'current_measurement': 0.005,      # 0.5% of reading
            'irradiance_measurement': 0.02,    # 2% of reading
            'temperature_measurement': 0.5,    # ±0.5°C
            'spectral_mismatch': 0.02,        # 2%
            'area_measurement': 0.01,          # 1%
            'non_uniformity': 0.02            # 2%
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate I-V curve data meets minimum requirements

        Args:
            data: Dictionary containing I-V curve data

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['voltage', 'current', 'irradiance', 'temperature', 'area']

        # Check all required fields present
        for field in required_fields:
            if field not in data:
                print(f"Error: Missing required field '{field}'")
                return False

        # Convert to numpy arrays
        voltage = np.array(data['voltage'])
        current = np.array(data['current'])

        # Check arrays have same length
        if len(voltage) != len(current):
            print("Error: Voltage and current arrays must have same length")
            return False

        # Check minimum number of points
        if len(voltage) < 10:
            print("Warning: I-V curve should have at least 10 measurement points")
            return False

        # Check for monotonic voltage increase
        if not np.all(np.diff(voltage) >= 0):
            print("Warning: Voltage values should be monotonically increasing")

        # Check for reasonable ranges
        if not self.check_data_range(data['irradiance'], 100, 1500, "Irradiance (W/m²)"):
            return False

        if not self.check_data_range(data['temperature'], -40, 85, "Temperature (°C)"):
            return False

        # Check current decreases with voltage
        if current[0] < current[-1]:
            print("Warning: Current should decrease from Isc to 0")

        return True

    def calculate(self, data: Dict[str, Any]) -> ProtocolResult:
        """
        Calculate I-V characteristics and key parameters

        Args:
            data: Dictionary with I-V curve data

        Returns:
            ProtocolResult with all I-V parameters
        """
        # Validate data
        if not self.validate_data(data):
            result = self.create_result(status=TestStatus.FAIL)
            result.notes = "Data validation failed"
            return result

        # Create result object
        result = self.create_result(status=TestStatus.PASS)

        # Extract data
        voltage = np.array(data['voltage'])
        current = np.array(data['current'])
        irradiance = data['irradiance']
        temperature = data['temperature']
        area = data['area']

        # Store metadata
        result.metadata.update({
            'irradiance': irradiance,
            'temperature': temperature,
            'module_area_m2': area,
            'number_of_points': len(voltage),
            'spectrum': data.get('spectrum', 'Unknown')
        })

        # Calculate key parameters
        isc = self._calculate_isc(voltage, current)
        voc = self._calculate_voc(voltage, current)
        pmp, vmp, imp = self._calculate_mpp(voltage, current)
        ff = self._calculate_fill_factor(isc.value, voc.value, pmp.value)
        efficiency = self._calculate_efficiency(pmp.value, irradiance, area)

        # Add measurements to result
        result.add_measurement('Isc', isc)
        result.add_measurement('Voc', voc)
        result.add_measurement('Pmp', pmp)
        result.add_measurement('Vmp', vmp)
        result.add_measurement('Imp', imp)
        result.add_measurement('FF', ff)
        result.add_measurement('Efficiency', efficiency)

        # Calculate series and shunt resistance
        rs = self._calculate_series_resistance(voltage, current, voc.value, isc.value)
        rsh = self._calculate_shunt_resistance(voltage, current)

        result.add_measurement('Rs', rs)
        result.add_measurement('Rsh', rsh)

        # Perform STC correction if needed
        if abs(irradiance - self.STC_IRRADIANCE) > 50 or abs(temperature - self.STC_TEMPERATURE) > 2:
            stc_params = self._correct_to_stc(
                result.measurements, irradiance, temperature, data.get('temp_coefficients', {})
            )
            result.measurements['STC_corrected'] = stc_params

        # Assess data quality
        result.data_quality = self.assess_data_quality(pmp)

        # Apply pass/fail criteria
        self._apply_pass_fail_criteria(result)

        return result

    def _calculate_isc(self, voltage: np.ndarray, current: np.ndarray) -> Uncertainty:
        """
        Calculate short-circuit current with uncertainty

        Args:
            voltage: Voltage array
            current: Current array

        Returns:
            Uncertainty object with Isc value
        """
        # Interpolate to V=0
        isc_value = np.interp(0.0, voltage, current)

        # Calculate uncertainty
        uncertainty_sources = {
            'current_meter': abs(isc_value) * self.uncertainty_sources['current_measurement'],
            'extrapolation': abs(isc_value) * 0.001  # 0.1% for interpolation
        }

        std_uncertainty = self.combine_uncertainties(uncertainty_sources)

        return Uncertainty(
            value=isc_value,
            standard_uncertainty=std_uncertainty,
            sources=uncertainty_sources
        )

    def _calculate_voc(self, voltage: np.ndarray, current: np.ndarray) -> Uncertainty:
        """
        Calculate open-circuit voltage with uncertainty

        Args:
            voltage: Voltage array
            current: Current array

        Returns:
            Uncertainty object with Voc value
        """
        # Interpolate to I=0
        voc_value = np.interp(0.0, current[::-1], voltage[::-1])

        # Calculate uncertainty
        uncertainty_sources = {
            'voltage_meter': abs(voc_value) * self.uncertainty_sources['voltage_measurement'],
            'extrapolation': abs(voc_value) * 0.001  # 0.1% for interpolation
        }

        std_uncertainty = self.combine_uncertainties(uncertainty_sources)

        return Uncertainty(
            value=voc_value,
            standard_uncertainty=std_uncertainty,
            sources=uncertainty_sources
        )

    def _calculate_mpp(self, voltage: np.ndarray, current: np.ndarray) -> Tuple[Uncertainty, Uncertainty, Uncertainty]:
        """
        Calculate maximum power point parameters

        Args:
            voltage: Voltage array
            current: Current array

        Returns:
            Tuple of (Pmp, Vmp, Imp) as Uncertainty objects
        """
        # Calculate power
        power = voltage * current

        # Find maximum power point
        max_idx = np.argmax(power)
        pmp_value = power[max_idx]
        vmp_value = voltage[max_idx]
        imp_value = current[max_idx]

        # Calculate uncertainties
        pmp_sources = {
            'voltage_meter': abs(vmp_value * imp_value) * self.uncertainty_sources['voltage_measurement'],
            'current_meter': abs(vmp_value * imp_value) * self.uncertainty_sources['current_measurement'],
            'discretization': abs(pmp_value) * 0.005  # 0.5% for sampling resolution
        }

        vmp_sources = {
            'voltage_meter': abs(vmp_value) * self.uncertainty_sources['voltage_measurement'],
        }

        imp_sources = {
            'current_meter': abs(imp_value) * self.uncertainty_sources['current_measurement'],
        }

        pmp = Uncertainty(
            value=pmp_value,
            standard_uncertainty=self.combine_uncertainties(pmp_sources),
            sources=pmp_sources
        )

        vmp = Uncertainty(
            value=vmp_value,
            standard_uncertainty=self.combine_uncertainties(vmp_sources),
            sources=vmp_sources
        )

        imp = Uncertainty(
            value=imp_value,
            standard_uncertainty=self.combine_uncertainties(imp_sources),
            sources=imp_sources
        )

        return pmp, vmp, imp

    def _calculate_fill_factor(self, isc: float, voc: float, pmp: float) -> Uncertainty:
        """
        Calculate fill factor

        FF = Pmp / (Isc × Voc)

        Args:
            isc: Short-circuit current
            voc: Open-circuit voltage
            pmp: Maximum power

        Returns:
            Uncertainty object with fill factor
        """
        if isc == 0 or voc == 0:
            raise ValueError("Isc and Voc must be non-zero")

        ff_value = pmp / (isc * voc)

        # Propagate uncertainties
        rel_unc_isc = self.uncertainty_sources['current_measurement']
        rel_unc_voc = self.uncertainty_sources['voltage_measurement']
        rel_unc_pmp = 0.007  # Combined from Pmp calculation

        rel_unc_ff = np.sqrt(rel_unc_pmp**2 + rel_unc_isc**2 + rel_unc_voc**2)
        std_uncertainty = ff_value * rel_unc_ff

        return Uncertainty(
            value=ff_value,
            standard_uncertainty=std_uncertainty,
            sources={'combined': std_uncertainty}
        )

    def _calculate_efficiency(self, pmp: float, irradiance: float, area: float) -> Uncertainty:
        """
        Calculate conversion efficiency

        η = Pmp / (Irradiance × Area) × 100%

        Args:
            pmp: Maximum power (W)
            irradiance: Incident irradiance (W/m²)
            area: Module area (m²)

        Returns:
            Uncertainty object with efficiency (%)
        """
        if irradiance == 0 or area == 0:
            raise ValueError("Irradiance and area must be non-zero")

        efficiency_value = (pmp / (irradiance * area)) * 100

        # Propagate uncertainties
        rel_unc_pmp = 0.007
        rel_unc_irr = self.uncertainty_sources['irradiance_measurement']
        rel_unc_area = self.uncertainty_sources['area_measurement']

        rel_unc_eff = np.sqrt(rel_unc_pmp**2 + rel_unc_irr**2 + rel_unc_area**2)
        std_uncertainty = efficiency_value * rel_unc_eff

        return Uncertainty(
            value=efficiency_value,
            standard_uncertainty=std_uncertainty,
            sources={
                'power': efficiency_value * rel_unc_pmp,
                'irradiance': efficiency_value * rel_unc_irr,
                'area': efficiency_value * rel_unc_area
            }
        )

    def _calculate_series_resistance(self, voltage: np.ndarray, current: np.ndarray,
                                     voc: float, isc: float) -> Uncertainty:
        """
        Calculate series resistance from I-V curve slope near Voc

        Args:
            voltage: Voltage array
            current: Current array
            voc: Open-circuit voltage
            isc: Short-circuit current

        Returns:
            Uncertainty object with Rs value (Ω)
        """
        # Use points near Voc (90-100% of Voc)
        mask = voltage > 0.9 * voc
        if np.sum(mask) < 3:
            mask = voltage > 0.8 * voc

        v_region = voltage[mask]
        i_region = current[mask]

        if len(v_region) < 3:
            # Insufficient data, return estimate
            rs_estimate = -voc / (100 * isc) if isc != 0 else 0
            return Uncertainty(value=rs_estimate, standard_uncertainty=rs_estimate * 0.5)

        # Calculate slope dV/dI
        regression = self.calculate_linear_regression(i_region, v_region)
        rs_value = abs(regression['slope'])

        # Uncertainty from regression
        std_uncertainty = regression['slope_uncertainty']

        return Uncertainty(
            value=rs_value,
            standard_uncertainty=std_uncertainty,
            sources={'regression': std_uncertainty}
        )

    def _calculate_shunt_resistance(self, voltage: np.ndarray, current: np.ndarray) -> Uncertainty:
        """
        Calculate shunt resistance from I-V curve slope near Isc

        Args:
            voltage: Voltage array
            current: Current array

        Returns:
            Uncertainty object with Rsh value (Ω)
        """
        # Use points near Isc (0-10% of Voc)
        voc_estimate = voltage[-1]
        mask = voltage < 0.1 * voc_estimate

        v_region = voltage[mask]
        i_region = current[mask]

        if len(v_region) < 3:
            # Insufficient data, return large resistance
            return Uncertainty(value=1e6, standard_uncertainty=1e5)

        # Calculate slope dV/dI
        regression = self.calculate_linear_regression(i_region, v_region)
        rsh_value = abs(regression['slope'])

        # Uncertainty from regression
        std_uncertainty = regression['slope_uncertainty']

        return Uncertainty(
            value=rsh_value,
            standard_uncertainty=std_uncertainty,
            sources={'regression': std_uncertainty}
        )

    def _correct_to_stc(self, measurements: Dict[str, Any], irradiance: float,
                       temperature: float, temp_coeffs: Dict[str, float]) -> Dict[str, float]:
        """
        Correct measurements to Standard Test Conditions

        Args:
            measurements: Dictionary of measured parameters
            irradiance: Measured irradiance (W/m²)
            temperature: Measured temperature (°C)
            temp_coeffs: Temperature coefficients dictionary

        Returns:
            Dictionary of STC-corrected parameters
        """
        # Default temperature coefficients if not provided
        alpha = temp_coeffs.get('alpha_isc', 0.05)  # %/°C for Isc
        beta = temp_coeffs.get('beta_voc', -0.30)   # %/°C for Voc
        gamma = temp_coeffs.get('gamma_pmp', -0.40) # %/°C for Pmp

        # Extract measured values
        isc = measurements['Isc'].value
        voc = measurements['Voc'].value
        pmp = measurements['Pmp'].value

        # Temperature correction
        delta_t = temperature - self.STC_TEMPERATURE

        isc_stc_temp = isc * (1 - (alpha / 100) * delta_t)
        voc_stc_temp = voc * (1 - (beta / 100) * delta_t)
        pmp_stc_temp = pmp * (1 - (gamma / 100) * delta_t)

        # Irradiance correction
        irr_ratio = self.STC_IRRADIANCE / irradiance

        isc_stc = isc_stc_temp * irr_ratio
        voc_stc = voc_stc_temp + 0.0023 * self.STC_TEMPERATURE * np.log(irr_ratio)  # Logarithmic correction
        pmp_stc = pmp_stc_temp * irr_ratio

        return {
            'Isc_STC': isc_stc,
            'Voc_STC': voc_stc,
            'Pmp_STC': pmp_stc,
            'FF_STC': pmp_stc / (isc_stc * voc_stc) if (isc_stc * voc_stc) > 0 else 0
        }

    def _apply_pass_fail_criteria(self, result: ProtocolResult):
        """
        Apply pass/fail criteria to measurements

        Args:
            result: ProtocolResult to update
        """
        # Check data quality
        pmp = result.measurements['Pmp']
        if isinstance(pmp, Uncertainty):
            result.add_criterion('data_quality_acceptable',
                               pmp.relative_uncertainty < 5.0)

        # Check fill factor is reasonable (typical range 65-85%)
        ff = result.measurements['FF']
        if isinstance(ff, Uncertainty):
            result.add_criterion('fill_factor_acceptable',
                               0.50 < ff.value < 0.90)

        # Check series resistance not too high
        rs = result.measurements['Rs']
        if isinstance(rs, Uncertainty):
            # Rs should typically be < 5 Ω for good modules
            result.add_criterion('series_resistance_acceptable',
                               rs.value < 10.0)

        # Check shunt resistance is high enough
        rsh = result.measurements['Rsh']
        if isinstance(rsh, Uncertainty):
            # Rsh should typically be > 100 Ω
            result.add_criterion('shunt_resistance_acceptable',
                               rsh.value > 50.0)
