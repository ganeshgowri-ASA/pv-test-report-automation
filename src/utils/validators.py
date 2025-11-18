"""
Data validation utilities
"""

from typing import Any, Dict, List
from datetime import datetime


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_power_measurement(power: float) -> bool:
    """Validate power measurement is positive"""
    if power <= 0:
        raise ValidationError(f"Power must be positive, got {power}")
    return True


def validate_temperature_range(temp: float, min_temp: float = -50, max_temp: float = 100) -> bool:
    """Validate temperature is within realistic range"""
    if not (min_temp <= temp <= max_temp):
        raise ValidationError(f"Temperature {temp}°C outside valid range [{min_temp}, {max_temp}]")
    return True


def validate_pressure_load(load_pa: float) -> bool:
    """Validate pressure load is positive"""
    if load_pa <= 0:
        raise ValidationError(f"Pressure load must be positive, got {load_pa}")
    return True


def validate_module_id(module_id: str) -> bool:
    """Validate module ID format"""
    if not module_id or not isinstance(module_id, str):
        raise ValidationError(f"Invalid module ID: {module_id}")
    return True


def validate_iso17025_compliance(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate ISO 17025 compliance requirements"""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required ISO 17025 fields: {missing_fields}")
    return True


def validate_degradation_limit(initial: float, final: float, max_degradation_pct: float = 5.0) -> bool:
    """Validate power degradation is within acceptable limits"""
    degradation_pct = ((initial - final) / initial) * 100
    if degradation_pct > max_degradation_pct:
        raise ValidationError(
            f"Power degradation {degradation_pct:.2f}% exceeds limit {max_degradation_pct}%"
        )
    return True
