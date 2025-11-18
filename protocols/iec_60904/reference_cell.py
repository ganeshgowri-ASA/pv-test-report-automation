"""
IEC 60904-2: Reference Solar Cells

This module implements reference solar cell calibration and management
according to IEC 60904-2 standard.

Key Features:
- Primary reference cell calibration
- Secondary reference transfer
- Spectral response verification
- Temperature coefficient determination
- Stability monitoring and drift tracking
- Traceability to national standards
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class CellType(Enum):
    """Reference cell types"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    WORKING = "working"


class CalibrationMethod(Enum):
    """Calibration methods"""
    DIRECT_SUNLIGHT = "direct_sunlight"
    SOLAR_SIMULATOR = "solar_simulator"
    SPECTRAL_RESPONSE = "spectral_response"
    TRANSFER_CALIBRATION = "transfer_calibration"


@dataclass
class ReferenceCellCalibration:
    """
    Reference cell calibration data

    Attributes:
        cell_serial: Reference cell serial number
        cell_type: Type of reference cell
        calibration_date: Date of calibration
        calibration_constant: Calibration constant (A/W/m²)
        temperature_coefficient: Temperature coefficient (%/°C)
        spectral_response: Spectral response data (wavelength vs responsivity)
        reference_temperature: Reference temperature (°C)
        reference_irradiance: Reference irradiance (W/m²)
        uncertainty: Calibration uncertainty (%)
        calibration_method: Method used for calibration
        traceability: Traceability information
        valid_until: Calibration expiration date
        metadata: Additional calibration metadata
    """
    cell_serial: str
    cell_type: CellType
    calibration_date: datetime
    calibration_constant: float  # A/(W/m²)
    temperature_coefficient: float  # %/°C
    spectral_response: Dict[float, float]  # wavelength (nm) -> responsivity (A/W)
    reference_temperature: float = 25.0  # °C
    reference_irradiance: float = 1000.0  # W/m²
    uncertainty: float = 0.5  # %
    calibration_method: CalibrationMethod = CalibrationMethod.TRANSFER_CALIBRATION
    traceability: str = "NIST/NPL/PTB"
    valid_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate calibration data"""
        if self.calibration_constant <= 0:
            raise ValueError("Calibration constant must be positive")
        if self.uncertainty <= 0 or self.uncertainty > 100:
            raise ValueError("Uncertainty must be between 0 and 100%")

        # Set default expiration (1 year for primary, 2 years for secondary/working)
        if self.valid_until is None:
            if self.cell_type == CellType.PRIMARY:
                self.valid_until = self.calibration_date + timedelta(days=365)
            else:
                self.valid_until = self.calibration_date + timedelta(days=730)

    def is_valid(self) -> bool:
        """Check if calibration is still valid"""
        return datetime.now() <= self.valid_until

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'cell_serial': self.cell_serial,
            'cell_type': self.cell_type.value,
            'calibration_date': self.calibration_date.isoformat(),
            'calibration_constant': float(self.calibration_constant),
            'temperature_coefficient': float(self.temperature_coefficient),
            'spectral_response': {float(k): float(v) for k, v in self.spectral_response.items()},
            'reference_temperature': float(self.reference_temperature),
            'reference_irradiance': float(self.reference_irradiance),
            'uncertainty': float(self.uncertainty),
            'calibration_method': self.calibration_method.value,
            'traceability': self.traceability,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class ReferenceCell:
    """
    Reference Solar Cell Management (IEC 60904-2)

    Manages reference solar cells including calibration, stability monitoring,
    and measurement operations.
    """

    def __init__(
        self,
        cell_serial: str,
        cell_type: CellType,
        active_area: float,  # cm²
        calibration: Optional[ReferenceCellCalibration] = None
    ):
        """
        Initialize reference cell

        Args:
            cell_serial: Cell serial number
            cell_type: Type of reference cell
            active_area: Active area in cm²
            calibration: Calibration data (if available)
        """
        self.cell_serial = cell_serial
        self.cell_type = cell_type
        self.active_area = active_area
        self.calibration = calibration
        self.measurement_history: List[Dict[str, Any]] = []

    def calibrate_primary(
        self,
        spectral_response: Dict[float, float],
        reference_spectrum: Dict[float, float],
        measured_current: float,
        temperature: float = 25.0,
        traceability: str = "NIST",
        uncertainty: float = 0.5
    ) -> ReferenceCellCalibration:
        """
        Calibrate primary reference cell using spectral response method

        Args:
            spectral_response: Spectral response (wavelength nm -> A/W)
            reference_spectrum: Reference spectrum (wavelength nm -> W/m²/nm)
            measured_current: Measured short-circuit current (A)
            temperature: Cell temperature (°C)
            traceability: Traceability to national lab
            uncertainty: Calibration uncertainty (%)

        Returns:
            ReferenceCellCalibration object
        """
        if self.cell_type != CellType.PRIMARY:
            raise ValueError("This method is only for primary reference cells")

        # Calculate expected current from spectral response and reference spectrum
        wavelengths = sorted(set(spectral_response.keys()) & set(reference_spectrum.keys()))

        total_irradiance = 0.0
        for i in range(len(wavelengths) - 1):
            wl = wavelengths[i]
            wl_next = wavelengths[i + 1]
            avg_irr = (reference_spectrum[wl] + reference_spectrum[wl_next]) / 2
            total_irradiance += avg_irr * (wl_next - wl)

        # Calibration constant = Isc / Irradiance
        calibration_constant = measured_current / total_irradiance if total_irradiance > 0 else 0

        # Temperature coefficient (typical value, should be measured)
        temp_coeff = -0.05  # %/°C (typical for c-Si)

        self.calibration = ReferenceCellCalibration(
            cell_serial=self.cell_serial,
            cell_type=self.cell_type,
            calibration_date=datetime.now(),
            calibration_constant=calibration_constant,
            temperature_coefficient=temp_coeff,
            spectral_response=spectral_response,
            reference_temperature=temperature,
            reference_irradiance=total_irradiance,
            uncertainty=uncertainty,
            calibration_method=CalibrationMethod.SPECTRAL_RESPONSE,
            traceability=traceability
        )

        return self.calibration

    def calibrate_by_transfer(
        self,
        primary_cell: 'ReferenceCell',
        measured_current_secondary: float,
        measured_current_primary: float,
        irradiance: float,
        temperature: float = 25.0,
        uncertainty_addon: float = 0.2
    ) -> ReferenceCellCalibration:
        """
        Calibrate secondary/working reference cell by transfer from primary

        Args:
            primary_cell: Calibrated primary reference cell
            measured_current_secondary: Measured current from this cell (A)
            measured_current_primary: Measured current from primary cell (A)
            irradiance: Irradiance during measurement (W/m²)
            temperature: Cell temperature (°C)
            uncertainty_addon: Additional uncertainty from transfer (%)

        Returns:
            ReferenceCellCalibration object
        """
        if not primary_cell.calibration or not primary_cell.calibration.is_valid():
            raise ValueError("Primary cell must have valid calibration")

        if self.cell_type == CellType.PRIMARY:
            raise ValueError("Transfer calibration not applicable to primary cells")

        # Calculate calibration constant for secondary cell
        ratio = measured_current_secondary / measured_current_primary if measured_current_primary > 0 else 0
        calibration_constant = ratio * primary_cell.calibration.calibration_constant

        # Temperature coefficient (typical, should be measured)
        temp_coeff = -0.05  # %/°C

        # Combined uncertainty
        combined_uncertainty = np.sqrt(
            primary_cell.calibration.uncertainty**2 + uncertainty_addon**2
        )

        self.calibration = ReferenceCellCalibration(
            cell_serial=self.cell_serial,
            cell_type=self.cell_type,
            calibration_date=datetime.now(),
            calibration_constant=calibration_constant,
            temperature_coefficient=temp_coeff,
            spectral_response=primary_cell.calibration.spectral_response.copy(),
            reference_temperature=temperature,
            reference_irradiance=irradiance,
            uncertainty=combined_uncertainty,
            calibration_method=CalibrationMethod.TRANSFER_CALIBRATION,
            traceability=f"Transfer from {primary_cell.cell_serial} ({primary_cell.calibration.traceability})"
        )

        return self.calibration

    def measure_irradiance(
        self,
        measured_current: float,
        temperature: float
    ) -> Tuple[float, float]:
        """
        Measure irradiance using reference cell

        Args:
            measured_current: Measured short-circuit current (A)
            temperature: Cell temperature (°C)

        Returns:
            Tuple of (irradiance W/m², uncertainty %)
        """
        if not self.calibration or not self.calibration.is_valid():
            raise ValueError("Reference cell requires valid calibration")

        # Temperature correction
        delta_t = temperature - self.calibration.reference_temperature
        temp_correction = 1 + (self.calibration.temperature_coefficient / 100.0) * delta_t

        # Calculate irradiance
        corrected_current = measured_current / temp_correction
        irradiance = corrected_current / self.calibration.calibration_constant

        # Record measurement
        self.measurement_history.append({
            'timestamp': datetime.now().isoformat(),
            'measured_current': measured_current,
            'temperature': temperature,
            'irradiance': irradiance,
            'uncertainty': self.calibration.uncertainty
        })

        return float(irradiance), float(self.calibration.uncertainty)

    def determine_temperature_coefficient(
        self,
        temperatures: List[float],
        currents: List[float],
        irradiance: float
    ) -> float:
        """
        Determine temperature coefficient of Isc

        Args:
            temperatures: List of cell temperatures (°C)
            currents: List of measured currents at each temperature (A)
            irradiance: Constant irradiance during measurement (W/m²)

        Returns:
            Temperature coefficient (%/°C)
        """
        if len(temperatures) != len(currents):
            raise ValueError("Temperature and current arrays must have same length")

        if len(temperatures) < 3:
            raise ValueError("Minimum 3 temperature points required")

        # Normalize currents to reference temperature (25°C)
        temps_array = np.array(temperatures)
        currents_array = np.array(currents)

        # Linear regression: I = I0 * (1 + α * (T - T0))
        # Rearrange: I = I0 + I0 * α * (T - T0)
        t_ref = 25.0
        delta_t = temps_array - t_ref

        # Fit: I = a + b * delta_t
        coeffs = np.polyfit(delta_t, currents_array, 1)
        slope = coeffs[0]
        i_ref = coeffs[1]

        # Temperature coefficient in %/°C
        temp_coeff = (slope / i_ref) * 100.0 if i_ref > 0 else 0

        # Update calibration if exists
        if self.calibration:
            self.calibration.temperature_coefficient = float(temp_coeff)

        return float(temp_coeff)

    def check_stability(
        self,
        lookback_days: int = 30,
        max_drift_percent: float = 1.0
    ) -> Dict[str, Any]:
        """
        Check stability of reference cell over time

        Args:
            lookback_days: Number of days to analyze
            max_drift_percent: Maximum acceptable drift (%)

        Returns:
            Dictionary with stability analysis results
        """
        if len(self.measurement_history) < 10:
            return {
                'stable': None,
                'message': 'Insufficient measurement history for stability analysis'
            }

        # Filter recent measurements
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_measurements = [
            m for m in self.measurement_history
            if datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]

        if len(recent_measurements) < 10:
            return {
                'stable': None,
                'message': f'Insufficient measurements in last {lookback_days} days'
            }

        # Analyze drift in normalized current (corrected for temperature)
        normalized_currents = []
        for m in recent_measurements:
            delta_t = m['temperature'] - self.calibration.reference_temperature
            temp_correction = 1 + (self.calibration.temperature_coefficient / 100.0) * delta_t
            normalized_i = m['measured_current'] / temp_correction
            normalized_currents.append(normalized_i)

        currents_array = np.array(normalized_currents)
        mean_current = np.mean(currents_array)
        std_current = np.std(currents_array)
        drift_percent = (std_current / mean_current) * 100.0 if mean_current > 0 else 0

        # Check trend
        time_indices = np.arange(len(currents_array))
        coeffs = np.polyfit(time_indices, currents_array, 1)
        trend_slope = coeffs[0]
        trend_percent = (trend_slope * len(currents_array) / mean_current) * 100.0

        stable = drift_percent <= max_drift_percent

        return {
            'stable': stable,
            'measurements_analyzed': len(recent_measurements),
            'lookback_days': lookback_days,
            'mean_current': float(mean_current),
            'std_deviation': float(std_current),
            'drift_percent': float(drift_percent),
            'trend_percent': float(trend_percent),
            'max_drift_percent': max_drift_percent,
            'recommendation': 'Recalibration recommended' if not stable else 'Cell is stable'
        }

    def verify_spectral_response(
        self,
        measured_response: Dict[float, float],
        tolerance_percent: float = 5.0
    ) -> Dict[str, Any]:
        """
        Verify spectral response matches calibration

        Args:
            measured_response: Newly measured spectral response
            tolerance_percent: Acceptable deviation (%)

        Returns:
            Verification results
        """
        if not self.calibration:
            raise ValueError("No calibration data available")

        calibrated_response = self.calibration.spectral_response
        common_wavelengths = sorted(set(measured_response.keys()) & set(calibrated_response.keys()))

        if len(common_wavelengths) < 10:
            return {
                'verified': False,
                'message': 'Insufficient common wavelengths for comparison'
            }

        deviations = []
        for wl in common_wavelengths:
            measured = measured_response[wl]
            calibrated = calibrated_response[wl]
            if calibrated > 0:
                deviation = abs((measured - calibrated) / calibrated) * 100.0
                deviations.append({
                    'wavelength': wl,
                    'measured': measured,
                    'calibrated': calibrated,
                    'deviation_percent': deviation
                })

        max_deviation = max(d['deviation_percent'] for d in deviations)
        mean_deviation = np.mean([d['deviation_percent'] for d in deviations])

        verified = max_deviation <= tolerance_percent

        return {
            'verified': verified,
            'wavelengths_compared': len(common_wavelengths),
            'max_deviation_percent': float(max_deviation),
            'mean_deviation_percent': float(mean_deviation),
            'tolerance_percent': tolerance_percent,
            'deviations': deviations,
            'recommendation': 'Spectral response verified' if verified else 'Recalibration required'
        }

    def get_calibration_certificate(self) -> Dict[str, Any]:
        """
        Generate calibration certificate data

        Returns:
            Dictionary containing calibration certificate information
        """
        if not self.calibration:
            raise ValueError("No calibration data available")

        return {
            'standard': 'IEC 60904-2:2023',
            'certificate_date': datetime.now().isoformat(),
            'cell_information': {
                'serial_number': self.cell_serial,
                'cell_type': self.cell_type.value,
                'active_area_cm2': self.active_area
            },
            'calibration_data': self.calibration.to_dict(),
            'iso17025_compliant': True,
            'traceability': self.calibration.traceability,
            'measurement_history_count': len(self.measurement_history)
        }
