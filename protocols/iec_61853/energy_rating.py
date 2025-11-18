"""
Energy Rating Calculations - IEC 61853-3
=========================================

Annual energy yield calculation and energy rating classification.

Key Features:
- Location-specific energy yield modeling
- Climate profile integration (IEC 61853-4)
- Performance ratio calculations
- Spectral and thermal loss modeling
- Energy rating classification (A+ to E)
- Comparison to STC ratings

Climate Types (IEC 61853-4):
- Tropical (high temperature, high humidity)
- Subtropical Desert (high temperature, low humidity)
- Temperate (moderate temperature)
- Temperate Desert (moderate temperature, low humidity)
- Cold (low temperature)

Calculations Account For:
- Temperature losses (using γ coefficient)
- Spectral mismatch (using spectral response)
- Angular losses (using IAM factor)
- System losses (inverter, wiring, soiling)
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from .models import LocationProfileData, EnergyRatingData, ClimateType
from .data_analyzer import PerformanceSurface, TemperatureCoefficients


# Configure logging
logger = logging.getLogger(__name__)


# ==================== Constants ====================

# Standard test locations (IEC 61853-4)
STANDARD_LOCATIONS = {
    "Nicosia": {
        "latitude": 35.17,
        "longitude": 33.37,
        "climate": ClimateType.SUBTROPICAL_DESERT,
        "annual_irradiation": 1780,  # kWh/m²/year
        "average_temp": 19.7,  # °C
    },
    "Phoenix": {
        "latitude": 33.43,
        "longitude": -112.02,
        "climate": ClimateType.SUBTROPICAL_DESERT,
        "annual_irradiation": 2110,
        "average_temp": 23.9,
    },
    "Aachen": {
        "latitude": 50.78,
        "longitude": 6.08,
        "climate": ClimateType.TEMPERATE,
        "annual_irradiation": 1070,
        "average_temp": 9.4,
    },
    "Mumbai": {
        "latitude": 19.08,
        "longitude": 72.88,
        "climate": ClimateType.TROPICAL,
        "annual_irradiation": 1950,
        "average_temp": 27.2,
    },
}

# Energy rating thresholds (example values)
ENERGY_RATING_THRESHOLDS = {
    "A+": 1.10,  # >110% of STC rating
    "A": 1.05,
    "B": 1.00,
    "C": 0.95,
    "D": 0.90,
    "E": 0.0,
}


# ==================== Data Classes ====================

@dataclass
class SystemLosses:
    """System-level loss factors"""
    inverter_efficiency: float = 0.96  # Typical inverter efficiency
    wiring_losses: float = 0.02  # 2% wiring losses
    soiling_losses: float = 0.03  # 3% soiling losses
    mismatch_losses: float = 0.02  # 2% mismatch losses
    availability: float = 0.99  # 99% system availability

    def get_total_loss_factor(self) -> float:
        """Calculate total system loss factor"""
        return (
            self.inverter_efficiency *
            (1 - self.wiring_losses) *
            (1 - self.soiling_losses) *
            (1 - self.mismatch_losses) *
            self.availability
        )


@dataclass
class MonthlyEnergyData:
    """Monthly energy yield data"""
    month: int  # 1-12
    irradiation: float  # kWh/m²
    average_temp: float  # °C
    energy_yield: float  # kWh
    performance_ratio: float


@dataclass
class LocationProfile:
    """Complete location profile for energy rating"""
    name: str
    latitude: float
    longitude: float
    climate_type: ClimateType
    annual_irradiation: float  # kWh/m²/year
    average_temperature: float  # °C
    altitude: float = 0.0  # meters
    monthly_data: Optional[List[MonthlyEnergyData]] = None


# ==================== Energy Rating Calculator ====================

class EnergyRatingCalculator:
    """
    Energy rating calculator per IEC 61853-3

    Calculates annual energy yield and energy rating class based on
    performance matrix data and location-specific climate profiles.
    """

    def __init__(
        self,
        performance_surface: PerformanceSurface,
        temperature_coefficients: TemperatureCoefficients,
        rated_power: float,  # W
        spectral_mismatch_factor: float = 1.0,
        iam_factor: float = 0.97,
        system_losses: Optional[SystemLosses] = None
    ):
        self.performance_surface = performance_surface
        self.temp_coefficients = temperature_coefficients
        self.rated_power = rated_power
        self.spectral_mismatch = spectral_mismatch_factor
        self.iam_factor = iam_factor
        self.system_losses = system_losses or SystemLosses()

        logger.info(
            f"Energy rating calculator initialized (Prated={rated_power}W)"
        )

    def calculate_annual_energy(
        self,
        location: LocationProfile,
        use_monthly_breakdown: bool = True
    ) -> EnergyRatingData:
        """
        Calculate annual energy yield for specific location

        Args:
            location: Location profile with climate data
            use_monthly_breakdown: Use monthly data if available

        Returns:
            EnergyRatingData with complete energy rating
        """
        logger.info(
            f"Calculating annual energy yield for {location.name} "
            f"({location.climate_type.value})"
        )

        if use_monthly_breakdown and location.monthly_data:
            # Use monthly data for more accurate calculation
            monthly_energies = [
                self._calculate_monthly_energy(month_data)
                for month_data in location.monthly_data
            ]
            annual_energy = sum(monthly_energies)
        else:
            # Use simplified annual calculation
            annual_energy = self._calculate_annual_energy_simplified(location)

        # Calculate specific yield (kWh/kWp)
        rated_power_kwp = self.rated_power / 1000.0
        specific_yield = annual_energy / rated_power_kwp

        # Calculate performance ratio
        # PR = actual yield / theoretical yield at STC
        theoretical_yield = (
            location.annual_irradiation * rated_power_kwp
        )  # kWh (if efficiency = 100%)
        performance_ratio = annual_energy / theoretical_yield if theoretical_yield > 0 else 0.0

        # Determine energy rating class
        comparison_to_stc = (annual_energy * 1000) / (
            location.annual_irradiation * self.rated_power
        )
        energy_class = self._determine_energy_class(comparison_to_stc)

        # Create location profile data
        location_data = LocationProfileData(
            name=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            climate_type=location.climate_type,
            annual_irradiation=location.annual_irradiation,
            average_temperature=location.average_temperature,
            altitude=location.altitude
        )

        energy_rating = EnergyRatingData(
            location_profile=location_data,
            annual_energy_kwh=float(annual_energy),
            specific_yield_kwh_kwp=float(specific_yield),
            performance_ratio=float(performance_ratio),
            energy_rating_class=energy_class,
            comparison_to_stc=float(comparison_to_stc * 100)  # Convert to percentage
        )

        logger.info(
            f"Energy rating: {annual_energy:.1f} kWh/year, "
            f"Specific yield: {specific_yield:.1f} kWh/kWp, "
            f"PR: {performance_ratio:.3f}, "
            f"Class: {energy_class}"
        )

        return energy_rating

    def _calculate_annual_energy_simplified(
        self,
        location: LocationProfile
    ) -> float:
        """
        Simplified annual energy calculation

        Uses average conditions and applies correction factors.

        Returns:
            Annual energy in kWh
        """
        # Use performance surface to predict power at average conditions
        # Assume average irradiance during daylight hours
        average_irradiance = 500.0  # W/m² (rough approximation)

        # Predict power at average conditions
        predicted_power = self.performance_surface.predict(
            average_irradiance,
            location.average_temperature
        )

        # Apply correction factors
        corrected_power = predicted_power * self.spectral_mismatch * self.iam_factor

        # Calculate equivalent full-sun hours
        # Annual irradiation / 1000 W/m² = equivalent hours at 1000 W/m²
        equivalent_hours = location.annual_irradiation

        # Scale power to equivalent hours
        # This is a simplification; real calculation would integrate hourly data
        annual_energy = (
            corrected_power / 1000.0 *  # Convert W to kW
            equivalent_hours *
            self.system_losses.get_total_loss_factor()
        )

        return annual_energy

    def _calculate_monthly_energy(
        self,
        month_data: MonthlyEnergyData
    ) -> float:
        """Calculate energy for a single month"""
        # Similar to annual calculation but for monthly data
        average_irradiance = 400.0  # W/m²

        predicted_power = self.performance_surface.predict(
            average_irradiance,
            month_data.average_temp
        )

        corrected_power = predicted_power * self.spectral_mismatch * self.iam_factor

        monthly_energy = (
            corrected_power / 1000.0 *
            month_data.irradiation *
            self.system_losses.get_total_loss_factor()
        )

        return monthly_energy

    def _determine_energy_class(self, comparison_to_stc: float) -> str:
        """
        Determine energy rating class based on comparison to STC

        Args:
            comparison_to_stc: Ratio of actual to STC performance

        Returns:
            Energy class string (A+, A, B, C, D, E)
        """
        for rating, threshold in ENERGY_RATING_THRESHOLDS.items():
            if comparison_to_stc >= threshold:
                return rating
        return "E"

    def calculate_multiple_locations(
        self,
        locations: Optional[List[str]] = None
    ) -> Dict[str, EnergyRatingData]:
        """
        Calculate energy ratings for multiple standard locations

        Args:
            locations: List of location names (uses all standard locations if None)

        Returns:
            Dictionary mapping location names to energy ratings
        """
        if locations is None:
            locations = list(STANDARD_LOCATIONS.keys())

        results = {}

        for loc_name in locations:
            if loc_name not in STANDARD_LOCATIONS:
                logger.warning(f"Unknown location: {loc_name}")
                continue

            loc_data = STANDARD_LOCATIONS[loc_name]
            location = LocationProfile(
                name=loc_name,
                latitude=loc_data["latitude"],
                longitude=loc_data["longitude"],
                climate_type=loc_data["climate"],
                annual_irradiation=loc_data["annual_irradiation"],
                average_temperature=loc_data["average_temp"]
            )

            energy_rating = self.calculate_annual_energy(location)
            results[loc_name] = energy_rating

        return results

    def compare_to_reference_module(
        self,
        location: LocationProfile,
        reference_energy: float
    ) -> Dict[str, Any]:
        """
        Compare energy yield to reference module

        Args:
            location: Location profile
            reference_energy: Reference module annual energy (kWh)

        Returns:
            Comparison results
        """
        test_energy = self.calculate_annual_energy(location)

        energy_gain = test_energy.annual_energy_kwh - reference_energy
        energy_gain_pct = (energy_gain / reference_energy) * 100 if reference_energy > 0 else 0

        return {
            "location": location.name,
            "test_module_energy": test_energy.annual_energy_kwh,
            "reference_module_energy": reference_energy,
            "energy_gain": energy_gain,
            "energy_gain_percent": energy_gain_pct,
            "test_module_class": test_energy.energy_rating_class,
        }

    def generate_energy_rating_report(
        self,
        locations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive energy rating report

        Args:
            locations: List of location names

        Returns:
            Complete energy rating report
        """
        logger.info("Generating comprehensive energy rating report")

        # Calculate for all locations
        location_results = self.calculate_multiple_locations(locations)

        # Summary statistics
        annual_energies = [r.annual_energy_kwh for r in location_results.values()]
        specific_yields = [r.specific_yield_kwh_kwp for r in location_results.values()]

        report = {
            "module_rating": {
                "rated_power_w": self.rated_power,
                "spectral_mismatch_factor": self.spectral_mismatch,
                "iam_factor": self.iam_factor,
            },
            "temperature_coefficients": {
                "gamma_pmax": self.temp_coefficients.gamma_pmax,
                "alpha_isc": self.temp_coefficients.alpha_isc,
                "beta_voc": self.temp_coefficients.beta_voc,
            },
            "location_results": {
                name: {
                    "annual_energy_kwh": rating.annual_energy_kwh,
                    "specific_yield_kwh_kwp": rating.specific_yield_kwh_kwp,
                    "performance_ratio": rating.performance_ratio,
                    "energy_class": rating.energy_rating_class,
                    "climate": rating.location_profile.climate_type.value,
                }
                for name, rating in location_results.items()
            },
            "summary": {
                "locations_tested": len(location_results),
                "average_annual_energy": float(np.mean(annual_energies)),
                "average_specific_yield": float(np.mean(specific_yields)),
                "min_energy": float(np.min(annual_energies)),
                "max_energy": float(np.max(annual_energies)),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "standard": "IEC 61853-3",
        }

        return report

    def export_to_json(self, filename: str, locations: Optional[List[str]] = None):
        """Export energy rating report to JSON file"""
        import json

        report = self.generate_energy_rating_report(locations)

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Energy rating report exported to {filename}")


# ==================== Helper Functions ====================

def create_location_profile(
    name: str,
    latitude: float,
    longitude: float,
    climate_type: ClimateType,
    annual_irradiation: float,
    average_temperature: float,
    **kwargs
) -> LocationProfile:
    """Helper to create LocationProfile"""
    return LocationProfile(
        name=name,
        latitude=latitude,
        longitude=longitude,
        climate_type=climate_type,
        annual_irradiation=annual_irradiation,
        average_temperature=average_temperature,
        **kwargs
    )


def get_standard_location(name: str) -> Optional[LocationProfile]:
    """Get standard IEC 61853-4 location profile"""
    if name not in STANDARD_LOCATIONS:
        return None

    data = STANDARD_LOCATIONS[name]
    return LocationProfile(
        name=name,
        latitude=data["latitude"],
        longitude=data["longitude"],
        climate_type=data["climate"],
        annual_irradiation=data["annual_irradiation"],
        average_temperature=data["average_temp"]
    )


def compare_energy_ratings(
    ratings: List[EnergyRatingData]
) -> Dict[str, Any]:
    """
    Compare multiple energy ratings

    Args:
        ratings: List of EnergyRatingData to compare

    Returns:
        Comparison analysis
    """
    if not ratings:
        return {}

    energies = [r.annual_energy_kwh for r in ratings]
    specific_yields = [r.specific_yield_kwh_kwp for r in ratings]

    return {
        "count": len(ratings),
        "energy": {
            "mean": float(np.mean(energies)),
            "std": float(np.std(energies)),
            "min": float(np.min(energies)),
            "max": float(np.max(energies)),
            "range": float(np.max(energies) - np.min(energies)),
        },
        "specific_yield": {
            "mean": float(np.mean(specific_yields)),
            "std": float(np.std(specific_yields)),
            "min": float(np.min(specific_yields)),
            "max": float(np.max(specific_yields)),
        },
        "locations": [r.location_profile.name for r in ratings],
        "classes": [r.energy_rating_class for r in ratings],
    }
