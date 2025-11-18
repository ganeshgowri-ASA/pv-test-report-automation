"""
Constants and standard specification limits for PV testing.

References:
- IEC 61215: Terrestrial photovoltaic (PV) modules - Design qualification and type approval
- IEC 61730: Photovoltaic (PV) module safety qualification
- ISO 17025: General requirements for the competence of testing and calibration laboratories
"""

from typing import Dict, Any


class IEC61215Limits:
    """IEC 61215 standard specification limits and test parameters."""

    # Hail Impact Test (Section 10.17 of IEC 61215)
    HAIL_IMPACT = {
        "standard_ball_diameter_mm": 25,  # Standard ice ball diameter
        "standard_impact_velocity_ms": 23,  # Standard impact velocity (m/s)
        "standard_impact_count": 11,  # Number of impact points
        "max_power_degradation_pct": 5.0,  # Maximum allowable power degradation
        "velocity_tolerance_pct": 2.5,  # Velocity measurement tolerance
        "ball_diameter_tolerance_mm": 1.0,  # Ice ball diameter tolerance
        "impact_angles_deg": [0],  # Normal impact (perpendicular)
        "temperature_range_celsius": {
            "min": 20,
            "max": 30
        },
        "impact_locations": [
            # Standard 11-point impact pattern
            {"point": 1, "description": "Center of module"},
            {"point": 2, "description": "Center of a cell"},
            {"point": 3, "description": "Cell interconnect"},
            {"point": 4, "description": "Near frame corner"},
            {"point": 5, "description": "Module edge center"},
            {"point": 6, "description": "Junction box vicinity"},
            {"point": 7, "description": "Cell corner"},
            {"point": 8, "description": "Bus bar"},
            {"point": 9, "description": "Between cells"},
            {"point": 10, "description": "Frame edge"},
            {"point": 11, "description": "Diode box area"}
        ]
    }

    # General electrical test limits
    ELECTRICAL = {
        "temperature_range_celsius": {"min": -40, "max": 85},
        "irradiance_wm2": {"min": 950, "max": 1050},
        "cell_temp_celsius": {"min": 23, "max": 27},
        "max_power_degradation_thermal_cycling_pct": 5.0,
        "max_power_degradation_humidity_freeze_pct": 5.0,
        "max_power_degradation_damp_heat_pct": 5.0
    }

    # Visual inspection criteria
    VISUAL_INSPECTION = {
        "allowable_defects": [
            "Minor scratches not affecting function",
            "Small bubbles < 5mm from edge"
        ],
        "unacceptable_defects": [
            "Glass breakage",
            "Delamination",
            "Cell cracks",
            "Broken interconnects",
            "Junction box damage"
        ]
    }


class IEC61730Limits:
    """IEC 61730 safety qualification limits."""

    SAFETY = {
        "high_pot_voltage_v": 1500,
        "isolation_resistance_megaohm": 100,
        "insulation_test_voltage_v": 1000
    }


class ISO17025Requirements:
    """ISO 17025 compliance requirements for test laboratories."""

    TRACEABILITY = {
        "calibration_interval_months": 12,
        "uncertainty_budget_required": True,
        "measurement_traceability_required": True,
        "equipment_records_required": True
    }

    DOCUMENTATION = {
        "operator_signature_required": True,
        "reviewer_signature_required": True,
        "environmental_conditions_required": True,
        "equipment_list_required": True,
        "test_procedure_reference_required": True
    }


class TestEquipment:
    """Standard test equipment specifications."""

    HAIL_TEST = {
        "hail_gun": {
            "type": "Pneumatic launcher",
            "velocity_range_ms": {"min": 10, "max": 40},
            "calibration_interval_months": 12,
            "accuracy": "±2.5% of reading"
        },
        "chronograph": {
            "type": "Optical velocity measurement",
            "range_ms": {"min": 0, "max": 50},
            "accuracy": "±0.5 m/s",
            "calibration_interval_months": 12
        },
        "high_speed_camera": {
            "type": "Impact documentation (optional)",
            "frame_rate_fps": {"min": 1000, "max": 10000},
            "resolution": "1920x1080 minimum"
        },
        "ice_ball_preparation": {
            "type": "Ice sphere maker",
            "diameter_range_mm": {"min": 10, "max": 50},
            "tolerance_mm": 1.0
        },
        "flash_tester": {
            "type": "Solar simulator + IV curve tracer",
            "irradiance_wm2": 1000,
            "spectrum": "AM 1.5G",
            "calibration_interval_months": 6,
            "class": "AAA"
        }
    }


class UncertaintyBudget:
    """Measurement uncertainty budget for key parameters."""

    HAIL_TEST_UNCERTAINTY = {
        "velocity_measurement": {
            "instrument_uncertainty_ms": 0.5,
            "calibration_uncertainty_ms": 0.3,
            "environmental_effects_ms": 0.2,
            "combined_uncertainty_ms": 0.62  # RSS of components
        },
        "ball_diameter": {
            "measurement_uncertainty_mm": 0.5,
            "manufacturing_tolerance_mm": 0.5,
            "temperature_effects_mm": 0.2,
            "combined_uncertainty_mm": 0.75
        },
        "power_measurement": {
            "flash_tester_uncertainty_pct": 2.0,
            "temperature_coefficient_pct": 0.5,
            "irradiance_uncertainty_pct": 1.0,
            "combined_uncertainty_pct": 2.35
        }
    }


# Environmental condition limits
ENVIRONMENTAL_LIMITS = {
    "temperature_celsius": {"min": 15, "max": 35},
    "relative_humidity_pct": {"min": 20, "max": 80},
    "atmospheric_pressure_kpa": {"min": 86, "max": 106}
}


# Quality control limits
QUALITY_CONTROL = {
    "duplicate_test_frequency": 0.1,  # 10% of tests
    "control_chart_sigma_limit": 3.0,
    "repeatability_rsd_pct": 5.0,
    "reproducibility_rsd_pct": 10.0
}
