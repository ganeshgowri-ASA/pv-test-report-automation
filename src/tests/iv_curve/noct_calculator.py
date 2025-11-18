"""
NOCT (Nominal Operating Cell Temperature) Calculator per IEC 61215
Thermal Performance Analysis for Photovoltaic Modules

NOCT Test Conditions per IEC 61215-2:
- Irradiance: 800 W/m²
- Ambient temperature: 20°C
- Wind speed: 1 m/s
- Mounting: Open rack
- Electrical load: Open circuit

This module provides:
- NOCT calculation and verification per IEC 61215
- Operating temperature prediction
- Thermal performance analysis
- Temperature rise calculations
- Power output at operating conditions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings


@dataclass
class NOCTConditions:
    """Nominal Operating Cell Temperature test conditions."""
    irradiance: float = 800.0  # W/m²
    ambient_temperature: float = 20.0  # °C
    wind_speed: float = 1.0  # m/s
    mounting: str = "open_rack"
    electrical_load: str = "open_circuit"
    tilt_angle: float = 45.0  # degrees


@dataclass
class ThermalParameters:
    """Module thermal characteristics."""
    noct: float  # °C - Nominal Operating Cell Temperature
    heat_loss_coefficient: Optional[float] = None  # W/(m²·K)
    absorptance: float = 0.90  # Solar absorptance (typical 0.85-0.95)
    emissivity: float = 0.85  # Thermal emissivity (typical 0.80-0.90)
    thermal_capacity: Optional[float] = None  # J/(m²·K)

    # Ross coefficient: ΔT = k × G (simplified)
    ross_coefficient: Optional[float] = None  # °C·m²/W


class NOCTCalculator:
    """
    Calculate and analyze NOCT per IEC 61215-2:2021.
    """

    # Standard NOCT test conditions
    NOCT_IRRADIANCE = 800.0  # W/m²
    NOCT_AMBIENT = 20.0  # °C
    NOCT_WIND_SPEED = 1.0  # m/s

    def __init__(self, noct_conditions: Optional[NOCTConditions] = None):
        """
        Initialize NOCT calculator.

        Args:
            noct_conditions: NOCT test conditions (default: IEC 61215 standard)
        """
        self.noct_conditions = noct_conditions or NOCTConditions()

    def calculate_noct_from_measurements(
        self,
        cell_temperature: float,
        ambient_temperature: float,
        irradiance: float,
        wind_speed: Optional[float] = None
    ) -> float:
        """
        Calculate NOCT from field measurements.

        NOCT is extrapolated to standard conditions (800 W/m², 20°C, 1 m/s).

        Args:
            cell_temperature: Measured cell temperature (°C)
            ambient_temperature: Measured ambient temperature (°C)
            irradiance: Measured irradiance (W/m²)
            wind_speed: Measured wind speed (m/s) - optional

        Returns:
            Calculated NOCT (°C)
        """
        if irradiance <= 0:
            raise ValueError("Irradiance must be positive")

        # Temperature rise above ambient
        delta_T_measured = cell_temperature - ambient_temperature

        # Normalize to NOCT irradiance (800 W/m²)
        # Assuming linear relationship: ΔT ∝ G
        delta_T_noct = delta_T_measured * (self.NOCT_IRRADIANCE / irradiance)

        # Wind speed correction (if available)
        if wind_speed is not None and wind_speed > 0:
            # Simplified correction: higher wind reduces temperature
            # ΔT ∝ 1/√(wind_speed)
            wind_correction = np.sqrt(self.NOCT_WIND_SPEED / wind_speed)
            delta_T_noct *= wind_correction

        # NOCT at standard ambient temperature
        noct = self.NOCT_AMBIENT + delta_T_noct

        return float(noct)

    def calculate_operating_temperature(
        self,
        thermal_params: ThermalParameters,
        ambient_temperature: float,
        irradiance: float,
        wind_speed: float = 1.0,
        mounting_correction: float = 1.0
    ) -> float:
        """
        Calculate module operating temperature from NOCT.

        Per IEC 61215, temperature rise is approximately linear with irradiance.

        T_cell = T_ambient + (NOCT - 20°C) × (G / 800 W/m²) × corrections

        Args:
            thermal_params: Module thermal parameters including NOCT
            ambient_temperature: Ambient air temperature (°C)
            irradiance: Plane-of-array irradiance (W/m²)
            wind_speed: Wind speed (m/s)
            mounting_correction: Correction for mounting type

        Returns:
            Estimated cell operating temperature (°C)
        """
        # Base temperature rise at NOCT conditions
        delta_T_noct = thermal_params.noct - self.NOCT_AMBIENT

        # Scale by irradiance
        irradiance_factor = irradiance / self.NOCT_IRRADIANCE

        # Wind speed correction
        wind_factor = self._wind_speed_correction(wind_speed, self.NOCT_WIND_SPEED)

        # Calculate operating temperature
        delta_T_operating = delta_T_noct * irradiance_factor * wind_factor * mounting_correction

        T_cell = ambient_temperature + delta_T_operating

        return float(T_cell)

    def calculate_ross_coefficient(self, thermal_params: ThermalParameters) -> float:
        """
        Calculate Ross coefficient for simplified temperature modeling.

        T_cell = T_ambient + k × G

        where k is the Ross coefficient in °C·m²/W.

        Args:
            thermal_params: Module thermal parameters including NOCT

        Returns:
            Ross coefficient (°C·m²/W)
        """
        if thermal_params.ross_coefficient is not None:
            return thermal_params.ross_coefficient

        # Calculate from NOCT
        # At NOCT conditions: NOCT = 20°C + k × 800 W/m²
        k = (thermal_params.noct - self.NOCT_AMBIENT) / self.NOCT_IRRADIANCE

        return float(k)

    def calculate_heat_loss_coefficient(
        self,
        thermal_params: ThermalParameters,
        module_area: Optional[float] = None
    ) -> float:
        """
        Calculate overall heat loss coefficient U_L.

        Energy balance at steady state:
        α × G = U_L × (T_cell - T_ambient)

        where:
        - α: solar absorptance
        - G: irradiance
        - U_L: heat loss coefficient

        Args:
            thermal_params: Module thermal parameters
            module_area: Module area in m² (optional)

        Returns:
            Heat loss coefficient U_L in W/(m²·K)
        """
        if thermal_params.heat_loss_coefficient is not None:
            return thermal_params.heat_loss_coefficient

        # Calculate from NOCT
        delta_T_noct = thermal_params.noct - self.NOCT_AMBIENT

        if delta_T_noct <= 0:
            warnings.warn("Invalid NOCT: temperature rise is non-positive")
            return 0.0

        # Energy balance: α×G = U_L×ΔT
        U_L = (thermal_params.absorptance * self.NOCT_IRRADIANCE) / delta_T_noct

        return float(U_L)

    def predict_power_at_operating_conditions(
        self,
        rated_power_stc: float,
        thermal_params: ThermalParameters,
        temp_coefficient_power: float,
        operating_conditions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Predict module power output at operating conditions.

        Accounts for:
        - Temperature derating
        - Irradiance scaling
        - Operating point shift

        Args:
            rated_power_stc: Rated power at STC (W)
            thermal_params: Module thermal parameters
            temp_coefficient_power: Temperature coefficient of power (%/°C)
            operating_conditions: Dict with 'ambient_temp', 'irradiance', 'wind_speed'

        Returns:
            Operating power and conditions
        """
        T_ambient = operating_conditions['ambient_temperature']
        G = operating_conditions['irradiance']
        wind = operating_conditions.get('wind_speed', 1.0)

        # Calculate operating temperature
        T_cell = self.calculate_operating_temperature(
            thermal_params, T_ambient, G, wind
        )

        # Temperature derating from STC (25°C)
        delta_T = T_cell - 25.0

        # Power temperature coefficient (convert %/°C to fractional)
        gamma = temp_coefficient_power / 100.0

        # Power at operating conditions
        # P_op = P_stc × (G / 1000) × [1 + γ × (T_cell - 25)]
        irradiance_factor = G / 1000.0
        temp_factor = 1.0 + gamma * delta_T

        P_operating = rated_power_stc * irradiance_factor * temp_factor

        return {
            'power_operating': float(P_operating),
            'cell_temperature': float(T_cell),
            'ambient_temperature': T_ambient,
            'irradiance': G,
            'irradiance_factor': float(irradiance_factor),
            'temperature_factor': float(temp_factor),
            'power_loss_temperature': float(-gamma * delta_T * 100),  # % loss
            'power_loss_irradiance': float((1 - irradiance_factor) * 100)  # % loss
        }

    def analyze_thermal_performance(
        self,
        thermal_params: ThermalParameters,
        temperature_range: Tuple[float, float] = (-10, 50),
        irradiance_range: Tuple[float, float] = (200, 1200),
        num_points: int = 20
    ) -> Dict[str, np.ndarray]:
        """
        Analyze thermal performance over range of conditions.

        Args:
            thermal_params: Module thermal parameters
            temperature_range: Ambient temperature range (°C)
            irradiance_range: Irradiance range (W/m²)
            num_points: Number of evaluation points

        Returns:
            Dictionary of operating temperatures for different conditions
        """
        T_ambient_range = np.linspace(temperature_range[0], temperature_range[1], num_points)
        G_range = np.linspace(irradiance_range[0], irradiance_range[1], num_points)

        # Create meshgrid
        T_amb_grid, G_grid = np.meshgrid(T_ambient_range, G_range)

        # Calculate operating temperatures
        T_cell_grid = np.zeros_like(T_amb_grid)

        for i in range(T_amb_grid.shape[0]):
            for j in range(T_amb_grid.shape[1]):
                T_cell_grid[i, j] = self.calculate_operating_temperature(
                    thermal_params,
                    T_amb_grid[i, j],
                    G_grid[i, j]
                )

        return {
            'ambient_temperature': T_amb_grid,
            'irradiance': G_grid,
            'cell_temperature': T_cell_grid,
            'temperature_rise': T_cell_grid - T_amb_grid
        }

    def estimate_thermal_time_constant(
        self,
        thermal_params: ThermalParameters,
        module_area: float = 1.6  # m² (typical)
    ) -> float:
        """
        Estimate thermal time constant for transient response.

        τ = (C × A) / (U_L × A) = C / U_L

        where:
        - C: thermal capacity per unit area (J/(m²·K))
        - U_L: heat loss coefficient (W/(m²·K))
        - τ: time constant (seconds)

        Args:
            thermal_params: Module thermal parameters
            module_area: Module area (m²)

        Returns:
            Thermal time constant (seconds)
        """
        if thermal_params.thermal_capacity is None:
            # Typical value for PV modules: 10,000-30,000 J/(m²·K)
            C = 20000.0
            warnings.warn(f"Using typical thermal capacity: {C} J/(m²·K)")
        else:
            C = thermal_params.thermal_capacity

        U_L = self.calculate_heat_loss_coefficient(thermal_params, module_area)

        if U_L <= 0:
            warnings.warn("Invalid heat loss coefficient")
            return 0.0

        tau = C / U_L

        return float(tau)

    def _wind_speed_correction(self, wind_actual: float, wind_reference: float) -> float:
        """
        Calculate wind speed correction factor.

        Heat transfer coefficient increases with wind speed:
        h ∝ √(wind_speed)

        Therefore: ΔT ∝ 1/√(wind_speed)

        Args:
            wind_actual: Actual wind speed (m/s)
            wind_reference: Reference wind speed (m/s)

        Returns:
            Correction factor
        """
        if wind_actual <= 0:
            warnings.warn("Wind speed must be positive, using reference value")
            return 1.0

        # Correction factor
        correction = np.sqrt(wind_reference / wind_actual)

        # Limit correction to reasonable range
        return float(np.clip(correction, 0.5, 2.0))

    def calculate_mounting_correction(self, mounting_type: str) -> float:
        """
        Calculate mounting correction factor for different installation types.

        Mounting types affect heat dissipation:
        - Open rack: Best cooling (reference, factor = 1.0)
        - Close roof mount: Reduced rear cooling (factor ≈ 1.2-1.3)
        - Integrated roof: Minimal cooling (factor ≈ 1.4-1.6)
        - Façade: Variable (factor ≈ 1.2-1.4)
        - Ground mount: Similar to open rack (factor ≈ 1.0-1.1)

        Args:
            mounting_type: Type of mounting

        Returns:
            Mounting correction factor (multiplier for temperature rise)
        """
        mounting_factors = {
            'open_rack': 1.0,
            'open': 1.0,
            'close_roof': 1.25,
            'close': 1.25,
            'roof_integrated': 1.5,
            'integrated': 1.5,
            'bipv': 1.5,
            'facade': 1.3,
            'ground': 1.05,
            'tracking': 1.0
        }

        mounting_lower = mounting_type.lower().replace(' ', '_')

        if mounting_lower in mounting_factors:
            return mounting_factors[mounting_lower]
        else:
            warnings.warn(f"Unknown mounting type '{mounting_type}', using open rack (1.0)")
            return 1.0

    def validate_noct_measurement(
        self,
        measured_noct: float,
        module_technology: str = 'crystalline_silicon'
    ) -> Tuple[bool, List[str]]:
        """
        Validate NOCT measurement against typical ranges.

        Typical NOCT ranges:
        - Crystalline silicon: 42-48°C
        - Thin film (CdTe, CIGS): 45-50°C
        - Amorphous silicon: 48-52°C

        Args:
            measured_noct: Measured NOCT value (°C)
            module_technology: PV technology type

        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings_list = []

        typical_ranges = {
            'crystalline_silicon': (40, 50),
            'monocrystalline': (42, 48),
            'polycrystalline': (43, 49),
            'thin_film': (45, 52),
            'cdte': (45, 50),
            'cigs': (45, 50),
            'amorphous': (48, 54),
            'hjt': (40, 46),  # Heterojunction
            'perc': (42, 48)   # PERC cells
        }

        tech_lower = module_technology.lower().replace(' ', '_')

        if tech_lower in typical_ranges:
            min_noct, max_noct = typical_ranges[tech_lower]

            if measured_noct < min_noct - 5:
                warnings_list.append(
                    f"NOCT ({measured_noct:.1f}°C) unusually low for {module_technology} "
                    f"(typical: {min_noct}-{max_noct}°C)"
                )
            elif measured_noct > max_noct + 5:
                warnings_list.append(
                    f"NOCT ({measured_noct:.1f}°C) unusually high for {module_technology} "
                    f"(typical: {min_noct}-{max_noct}°C)"
                )
        else:
            warnings_list.append(f"Unknown technology '{module_technology}', cannot validate")

        # Physical limits
        if measured_noct < 30:
            warnings_list.append(f"NOCT ({measured_noct:.1f}°C) below physical limits")

        if measured_noct > 70:
            warnings_list.append(f"NOCT ({measured_noct:.1f}°C) above reasonable limits")

        # NOCT should be above ambient
        if measured_noct <= self.NOCT_AMBIENT:
            warnings_list.append(
                f"NOCT ({measured_noct:.1f}°C) not above ambient ({self.NOCT_AMBIENT}°C)"
            )

        return len(warnings_list) == 0, warnings_list


def calculate_inoct_power(
    rated_power_stc: float,
    thermal_params: ThermalParameters,
    temp_coefficient_power: float
) -> float:
    """
    Calculate power at INOCT (Installed NOCT) conditions.

    INOCT conditions:
    - Irradiance: 800 W/m²
    - Cell temperature: NOCT
    - Operating point: Maximum power

    Args:
        rated_power_stc: Rated power at STC (W)
        thermal_params: Module thermal parameters
        temp_coefficient_power: Temperature coefficient of power (%/°C)

    Returns:
        Power at INOCT conditions (W)
    """
    # Temperature difference from STC
    delta_T = thermal_params.noct - 25.0

    # Power temperature coefficient (convert %/°C to fractional)
    gamma = temp_coefficient_power / 100.0

    # Power at INOCT
    # P_inoct = P_stc × (800/1000) × [1 + γ × (NOCT - 25)]
    P_inoct = rated_power_stc * 0.8 * (1.0 + gamma * delta_T)

    return float(P_inoct)


def calculate_module_efficiency_at_noct(
    rated_power_stc: float,
    module_area: float,
    thermal_params: ThermalParameters,
    temp_coefficient_power: float
) -> Dict[str, float]:
    """
    Calculate module efficiency at NOCT conditions.

    Args:
        rated_power_stc: Rated power at STC (W)
        module_area: Module area (m²)
        thermal_params: Module thermal parameters
        temp_coefficient_power: Temperature coefficient of power (%/°C)

    Returns:
        Efficiency at STC and NOCT conditions
    """
    # Efficiency at STC
    eta_stc = (rated_power_stc / (1000.0 * module_area)) * 100

    # Power at NOCT
    P_noct = calculate_inoct_power(rated_power_stc, thermal_params, temp_coefficient_power)

    # Efficiency at NOCT
    eta_noct = (P_noct / (800.0 * module_area)) * 100

    return {
        'efficiency_stc': float(eta_stc),
        'efficiency_noct': float(eta_noct),
        'power_stc': float(rated_power_stc),
        'power_noct': float(P_noct),
        'efficiency_ratio': float(eta_noct / eta_stc) if eta_stc > 0 else 0
    }


if __name__ == "__main__":
    print("NOCT Calculator - IEC 61215-2:2021")
    print("=" * 50)

    # Example usage
    calculator = NOCTCalculator()

    # Example 1: Calculate NOCT from measurements
    print("\n1. Calculate NOCT from field measurements:")
    print("-" * 50)

    measured_cell_temp = 55.0  # °C
    measured_ambient = 28.0  # °C
    measured_irradiance = 950.0  # W/m²
    measured_wind = 0.5  # m/s

    noct = calculator.calculate_noct_from_measurements(
        measured_cell_temp,
        measured_ambient,
        measured_irradiance,
        measured_wind
    )

    print(f"Measured conditions:")
    print(f"  Cell temperature: {measured_cell_temp}°C")
    print(f"  Ambient temperature: {measured_ambient}°C")
    print(f"  Irradiance: {measured_irradiance} W/m²")
    print(f"  Wind speed: {measured_wind} m/s")
    print(f"\nCalculated NOCT: {noct:.1f}°C")

    # Validate NOCT
    is_valid, warnings_list = calculator.validate_noct_measurement(noct, 'crystalline_silicon')
    print(f"Validation: {'PASS' if is_valid else 'WARNINGS'}")
    for warning in warnings_list:
        print(f"  ⚠ {warning}")

    # Example 2: Predict operating temperature
    print("\n2. Predict operating temperature:")
    print("-" * 50)

    thermal_params = ThermalParameters(noct=45.0)

    T_op = calculator.calculate_operating_temperature(
        thermal_params,
        ambient_temperature=35.0,
        irradiance=1000.0,
        wind_speed=2.0
    )

    print(f"Operating conditions:")
    print(f"  Ambient: 35°C, Irradiance: 1000 W/m², Wind: 2 m/s")
    print(f"  Predicted cell temperature: {T_op:.1f}°C")

    # Example 3: Power at operating conditions
    print("\n3. Power at operating conditions:")
    print("-" * 50)

    power_results = calculator.predict_power_at_operating_conditions(
        rated_power_stc=300.0,
        thermal_params=thermal_params,
        temp_coefficient_power=-0.40,  # %/°C
        operating_conditions={
            'ambient_temperature': 35.0,
            'irradiance': 1000.0,
            'wind_speed': 2.0
        }
    )

    print(f"Rated power (STC): 300 W")
    print(f"Operating power: {power_results['power_operating']:.1f} W")
    print(f"Temperature loss: {power_results['power_loss_temperature']:.1f}%")
    print(f"Cell temperature: {power_results['cell_temperature']:.1f}°C")

    # Example 4: Thermal coefficients
    print("\n4. Thermal characteristics:")
    print("-" * 50)

    ross_coeff = calculator.calculate_ross_coefficient(thermal_params)
    heat_loss = calculator.calculate_heat_loss_coefficient(thermal_params)
    time_const = calculator.estimate_thermal_time_constant(thermal_params)

    print(f"Ross coefficient: {ross_coeff:.4f} °C·m²/W")
    print(f"Heat loss coefficient: {heat_loss:.1f} W/(m²·K)")
    print(f"Thermal time constant: {time_const:.1f} seconds ({time_const/60:.1f} minutes)")

    # Example 5: Mounting corrections
    print("\n5. Mounting type corrections:")
    print("-" * 50)

    for mounting in ['open_rack', 'close_roof', 'integrated', 'ground']:
        factor = calculator.calculate_mounting_correction(mounting)
        T_cell = calculator.calculate_operating_temperature(
            thermal_params, 25.0, 800.0, 1.0, factor
        )
        print(f"  {mounting:15s}: factor={factor:.2f}, T_cell={T_cell:.1f}°C")

    print("\n" + "=" * 50)
    print("Module ready for production use")
