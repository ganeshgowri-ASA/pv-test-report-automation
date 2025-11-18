"""
Performance Data Analysis - IEC 61853
======================================

Advanced analysis of performance matrix data:

1. Performance Surface Modeling:
   - Pmax(G, T) surface fitting
   - Polynomial regression (2D)
   - Model validation and quality metrics

2. Temperature Coefficients:
   - α (Isc): Current temperature coefficient
   - β (Voc): Voltage temperature coefficient
   - γ (Pmax): Power temperature coefficient
   - Linear regression at reference irradiance

3. Irradiance Coefficients:
   - Power vs irradiance relationships
   - Non-linearity analysis
   - Low-light performance

4. Statistical Analysis:
   - R² (coefficient of determination)
   - RMSE (root mean square error)
   - Confidence intervals
   - Outlier detection
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import optimize, stats
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

from .models import (
    MatrixTestPointData,
    TemperatureCoefficientsData,
    PerformanceSurfaceData,
)
from .performance_matrix import MatrixTestPoint, MatrixTestResults


# Configure logging
logger = logging.getLogger(__name__)


# ==================== Data Classes ====================

@dataclass
class PerformanceSurface:
    """3D performance surface Pmax(G, T)"""
    model: Any  # sklearn model
    polynomial_degree: int
    coefficients: List[float]
    r_squared: float
    rmse: float
    temperature_range: Tuple[float, float]
    irradiance_range: Tuple[float, float]

    def predict(
        self,
        irradiance: float,
        temperature: float
    ) -> float:
        """
        Predict Pmax at given conditions

        Args:
            irradiance: Irradiance in W/m²
            temperature: Temperature in °C

        Returns:
            Predicted Pmax in W
        """
        X = np.array([[irradiance, temperature]])
        return float(self.model.predict(X)[0])

    def predict_batch(
        self,
        irradiances: np.ndarray,
        temperatures: np.ndarray
    ) -> np.ndarray:
        """Predict Pmax for arrays of conditions"""
        X = np.column_stack([irradiances.ravel(), temperatures.ravel()])
        predictions = self.model.predict(X)
        return predictions.reshape(irradiances.shape)


@dataclass
class TemperatureCoefficients:
    """Temperature coefficients (α, β, γ)"""
    alpha_isc: float  # %/°C
    beta_voc: float  # %/°C
    gamma_pmax: float  # %/°C
    alpha_isc_abs: float  # A/°C
    beta_voc_abs: float  # V/°C
    gamma_pmax_abs: float  # W/°C
    reference_temperature: float  # °C
    reference_irradiance: float  # W/m²
    r_squared_isc: float
    r_squared_voc: float
    r_squared_pmax: float


@dataclass
class IrradianceCoefficients:
    """Irradiance dependency coefficients"""
    linear_coefficient: float  # W per W/m²
    non_linearity: float  # Deviation from linearity
    low_light_performance: float  # Relative performance at 200W/m²
    reference_temperature: float  # °C


# ==================== Performance Analyzer ====================

class PerformanceAnalyzer:
    """
    Comprehensive analysis of performance matrix data

    Performs statistical analysis, curve fitting, and coefficient extraction.
    """

    def __init__(self, matrix_results: MatrixTestResults):
        self.results = matrix_results
        self._performance_surface: Optional[PerformanceSurface] = None
        self._temp_coefficients: Optional[TemperatureCoefficients] = None
        self._irrad_coefficients: Optional[IrradianceCoefficients] = None

        logger.info("Performance analyzer initialized")

    def analyze_all(self) -> Dict[str, Any]:
        """
        Run complete analysis suite

        Returns:
            Dictionary with all analysis results
        """
        logger.info("Starting comprehensive performance analysis")

        # Fit performance surface
        surface = self.fit_performance_surface(polynomial_degree=2)

        # Extract temperature coefficients
        temp_coeff = self.extract_temperature_coefficients(
            reference_irradiance=1000.0,
            reference_temperature=25.0
        )

        # Analyze irradiance dependency
        irrad_coeff = self.analyze_irradiance_dependency(
            reference_temperature=25.0
        )

        # Statistical quality metrics
        quality = self.calculate_quality_metrics()

        return {
            "performance_surface": {
                "r_squared": surface.r_squared,
                "rmse": surface.rmse,
                "polynomial_degree": surface.polynomial_degree,
            },
            "temperature_coefficients": {
                "alpha_isc": temp_coeff.alpha_isc,
                "beta_voc": temp_coeff.beta_voc,
                "gamma_pmax": temp_coeff.gamma_pmax,
            },
            "irradiance_coefficients": {
                "linear_coefficient": irrad_coeff.linear_coefficient,
                "non_linearity": irrad_coeff.non_linearity,
                "low_light_performance": irrad_coeff.low_light_performance,
            },
            "quality_metrics": quality,
        }

    def fit_performance_surface(
        self,
        polynomial_degree: int = 2
    ) -> PerformanceSurface:
        """
        Fit Pmax(G, T) performance surface using polynomial regression

        Args:
            polynomial_degree: Degree of polynomial (1=linear, 2=quadratic, etc.)

        Returns:
            PerformanceSurface model
        """
        logger.info(f"Fitting performance surface (degree={polynomial_degree})")

        # Extract successful test points
        test_points = [
            p for p in self.results.test_points
            if p.data is not None
        ]

        if len(test_points) < 6:
            raise ValueError(f"Insufficient data points: {len(test_points)} (need ≥6)")

        # Prepare training data
        irradiances = np.array([p.irradiance for p in test_points])
        temperatures = np.array([p.temperature for p in test_points])
        pmax_values = np.array([p.data.iv_curve.pmax for p in test_points])

        X = np.column_stack([irradiances, temperatures])

        # Create polynomial features
        poly = PolynomialFeatures(degree=polynomial_degree, include_bias=True)
        X_poly = poly.fit_transform(X)

        # Fit linear regression on polynomial features
        model = LinearRegression()
        model.fit(X_poly, pmax_values)

        # Predictions and quality metrics
        y_pred = model.predict(X_poly)
        r_squared = r2_score(pmax_values, y_pred)
        rmse = np.sqrt(mean_squared_error(pmax_values, y_pred))

        # Get coefficients
        coefficients = model.coef_.tolist()

        # Create combined model for predictions
        class CombinedModel:
            def __init__(self, poly, linear_model):
                self.poly = poly
                self.linear_model = linear_model

            def predict(self, X):
                X_poly = self.poly.transform(X)
                return self.linear_model.predict(X_poly)

        combined_model = CombinedModel(poly, model)

        # Determine ranges
        temp_range = (float(temperatures.min()), float(temperatures.max()))
        irrad_range = (float(irradiances.min()), float(irradiances.max()))

        surface = PerformanceSurface(
            model=combined_model,
            polynomial_degree=polynomial_degree,
            coefficients=coefficients,
            r_squared=float(r_squared),
            rmse=float(rmse),
            temperature_range=temp_range,
            irradiance_range=irrad_range
        )

        logger.info(
            f"Surface fit: R²={r_squared:.4f}, RMSE={rmse:.2f}W, "
            f"Temp range={temp_range}°C, Irrad range={irrad_range}W/m²"
        )

        self._performance_surface = surface
        return surface

    def extract_temperature_coefficients(
        self,
        reference_irradiance: float = 1000.0,
        reference_temperature: float = 25.0,
        tolerance: float = 50.0  # W/m²
    ) -> TemperatureCoefficients:
        """
        Extract temperature coefficients at reference irradiance

        Calculates α (Isc), β (Voc), and γ (Pmax) from linear regression
        of parameter vs temperature at constant irradiance.

        Args:
            reference_irradiance: Reference irradiance (W/m²)
            reference_temperature: Reference temperature (°C)
            tolerance: Acceptable irradiance deviation (W/m²)

        Returns:
            TemperatureCoefficients
        """
        logger.info(
            f"Extracting temperature coefficients at G={reference_irradiance}W/m²"
        )

        # Filter test points at reference irradiance
        test_points = [
            p for p in self.results.test_points
            if p.data is not None and
            abs(p.irradiance - reference_irradiance) <= tolerance
        ]

        if len(test_points) < 3:
            raise ValueError(
                f"Insufficient points at {reference_irradiance}W/m²: {len(test_points)}"
            )

        # Extract data
        temperatures = np.array([p.temperature for p in test_points])
        isc_values = np.array([p.data.iv_curve.isc for p in test_points])
        voc_values = np.array([p.data.iv_curve.voc for p in test_points])
        pmax_values = np.array([p.data.iv_curve.pmax for p in test_points])

        # Get reference values (interpolate to reference temperature)
        isc_ref = np.interp(reference_temperature, temperatures, isc_values)
        voc_ref = np.interp(reference_temperature, temperatures, voc_values)
        pmax_ref = np.interp(reference_temperature, temperatures, pmax_values)

        # Linear regression for each parameter
        def linear_fit(temps, values, ref_value):
            """Fit linear model and extract coefficient"""
            slope, intercept, r_value, p_value, std_err = stats.linregress(temps, values)
            r_squared = r_value ** 2

            # Convert to percentage coefficient
            coeff_abs = slope  # Absolute units per °C
            coeff_pct = (slope / ref_value) * 100.0 if ref_value != 0 else 0.0  # %/°C

            return coeff_abs, coeff_pct, r_squared

        # Calculate coefficients
        alpha_abs, alpha_pct, r2_isc = linear_fit(temperatures, isc_values, isc_ref)
        beta_abs, beta_pct, r2_voc = linear_fit(temperatures, voc_values, voc_ref)
        gamma_abs, gamma_pct, r2_pmax = linear_fit(temperatures, pmax_values, pmax_ref)

        temp_coefficients = TemperatureCoefficients(
            alpha_isc=float(alpha_pct),
            beta_voc=float(beta_pct),
            gamma_pmax=float(gamma_pct),
            alpha_isc_abs=float(alpha_abs),
            beta_voc_abs=float(beta_abs),
            gamma_pmax_abs=float(gamma_abs),
            reference_temperature=reference_temperature,
            reference_irradiance=reference_irradiance,
            r_squared_isc=float(r2_isc),
            r_squared_voc=float(r2_voc),
            r_squared_pmax=float(r2_pmax)
        )

        logger.info(
            f"Temperature coefficients: α={alpha_pct:.3f}%/°C, "
            f"β={beta_pct:.3f}%/°C, γ={gamma_pct:.3f}%/°C"
        )

        self._temp_coefficients = temp_coefficients
        return temp_coefficients

    def analyze_irradiance_dependency(
        self,
        reference_temperature: float = 25.0,
        tolerance: float = 2.0  # °C
    ) -> IrradianceCoefficients:
        """
        Analyze power vs irradiance relationship

        Checks for linearity and low-light performance.

        Args:
            reference_temperature: Reference temperature (°C)
            tolerance: Acceptable temperature deviation (°C)

        Returns:
            IrradianceCoefficients
        """
        logger.info(
            f"Analyzing irradiance dependency at T={reference_temperature}°C"
        )

        # Filter test points at reference temperature
        test_points = [
            p for p in self.results.test_points
            if p.data is not None and
            abs(p.temperature - reference_temperature) <= tolerance
        ]

        if len(test_points) < 3:
            raise ValueError(
                f"Insufficient points at {reference_temperature}°C: {len(test_points)}"
            )

        # Extract data
        irradiances = np.array([p.irradiance for p in test_points])
        pmax_values = np.array([p.data.iv_curve.pmax for p in test_points])

        # Sort by irradiance
        sort_idx = np.argsort(irradiances)
        irradiances = irradiances[sort_idx]
        pmax_values = pmax_values[sort_idx]

        # Linear fit
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            irradiances, pmax_values
        )

        # Calculate non-linearity (deviation from linear fit)
        pmax_linear = slope * irradiances + intercept
        deviations = np.abs(pmax_values - pmax_linear)
        non_linearity = float(np.mean(deviations / pmax_values) * 100)  # %

        # Low-light performance (at 200 W/m²)
        # Normalize power to 1000 W/m²
        normalized_power = pmax_values / irradiances
        ref_normalized = np.interp(1000.0, irradiances, normalized_power)
        low_light_normalized = np.interp(200.0, irradiances, normalized_power)
        low_light_performance = float(low_light_normalized / ref_normalized)

        irrad_coefficients = IrradianceCoefficients(
            linear_coefficient=float(slope),
            non_linearity=non_linearity,
            low_light_performance=low_light_performance,
            reference_temperature=reference_temperature
        )

        logger.info(
            f"Irradiance analysis: slope={slope:.3f}W/(W/m²), "
            f"non-linearity={non_linearity:.2f}%, "
            f"low-light={low_light_performance:.3f}"
        )

        self._irrad_coefficients = irrad_coefficients
        return irrad_coefficients

    def calculate_quality_metrics(self) -> Dict[str, Any]:
        """
        Calculate data quality metrics

        Returns:
            Dictionary with quality metrics
        """
        test_points = [
            p for p in self.results.test_points
            if p.data is not None
        ]

        # Fill factor statistics
        fill_factors = [p.data.iv_curve.ff for p in test_points]
        ff_mean = np.mean(fill_factors)
        ff_std = np.std(fill_factors)
        ff_min = np.min(fill_factors)
        ff_max = np.max(fill_factors)

        # Temperature stability
        temp_stabilities = [p.data.chamber_temp_stability for p in test_points]
        temp_stab_mean = np.mean(temp_stabilities)
        temp_stab_max = np.max(temp_stabilities)

        # Irradiance uniformity
        irrad_uniformities = [p.data.irradiance_uniformity for p in test_points]
        irrad_unif_mean = np.mean(irrad_uniformities)
        irrad_unif_min = np.min(irrad_uniformities)

        return {
            "fill_factor": {
                "mean": float(ff_mean),
                "std": float(ff_std),
                "min": float(ff_min),
                "max": float(ff_max),
            },
            "temperature_stability": {
                "mean": float(temp_stab_mean),
                "max": float(temp_stab_max),
            },
            "irradiance_uniformity": {
                "mean": float(irrad_unif_mean),
                "min": float(irrad_unif_min),
            },
            "data_completeness": {
                "total_points": self.results.total_points,
                "successful_points": self.results.successful_points,
                "success_rate": self.results.successful_points / self.results.total_points
            }
        }

    def get_performance_surface(self) -> Optional[PerformanceSurface]:
        """Get fitted performance surface"""
        return self._performance_surface

    def get_temperature_coefficients(self) -> Optional[TemperatureCoefficients]:
        """Get extracted temperature coefficients"""
        return self._temp_coefficients

    def get_irradiance_coefficients(self) -> Optional[IrradianceCoefficients]:
        """Get irradiance dependency coefficients"""
        return self._irrad_coefficients

    def generate_mesh_predictions(
        self,
        temp_points: int = 20,
        irrad_points: int = 20
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate mesh grid predictions for 3D plotting

        Args:
            temp_points: Number of temperature points
            irrad_points: Number of irradiance points

        Returns:
            Tuple of (temperatures, irradiances, pmax_predictions) meshgrids
        """
        if self._performance_surface is None:
            raise ValueError("Performance surface not fitted yet")

        surface = self._performance_surface

        # Create mesh grid
        temps = np.linspace(
            surface.temperature_range[0],
            surface.temperature_range[1],
            temp_points
        )
        irrads = np.linspace(
            surface.irradiance_range[0],
            surface.irradiance_range[1],
            irrad_points
        )

        T, G = np.meshgrid(temps, irrads)

        # Predict Pmax at each point
        P = surface.predict_batch(G, T)

        return T, G, P

    def export_analysis_report(self, filename: str):
        """Export analysis results to JSON"""
        import json

        report = self.analyze_all()

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Analysis report exported to {filename}")
