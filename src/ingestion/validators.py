"""Schema validation and ISO 17025 compliance checkers."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import ValidationError

from ..models.ingestion_models import (
    ISO17025Metadata,
    IVCurveData,
    ChamberLogData,
    BatchTestResult,
    EquipmentData,
)


class SchemaValidator:
    """Validate data against Pydantic schemas."""

    @staticmethod
    def validate_iv_curve(data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """Validate I-V curve data.

        Args:
            data: Dictionary with I-V curve data

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            IVCurveData(**data)
            return True, None
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field}: {error['msg']}")
            return False, errors

    @staticmethod
    def validate_chamber_log(data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """Validate chamber log data.

        Args:
            data: Dictionary with chamber log data

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            ChamberLogData(**data)
            return True, None
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field}: {error['msg']}")
            return False, errors

    @staticmethod
    def validate_batch_result(data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """Validate batch test result data.

        Args:
            data: Dictionary with batch test data

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            BatchTestResult(**data)
            return True, None
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field}: {error['msg']}")
            return False, errors

    @staticmethod
    def validate_equipment_data(data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """Validate equipment data.

        Args:
            data: Dictionary with equipment data

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            EquipmentData(**data)
            return True, None
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field}: {error['msg']}")
            return False, errors

    @staticmethod
    def validate_dataframe_schema(
        df: pd.DataFrame, required_columns: List[str], optional_columns: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[List[str]]]:
        """Validate DataFrame has required columns.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            optional_columns: List of optional column names

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required columns
        missing_required = set(required_columns) - set(df.columns)
        if missing_required:
            errors.append(f"Missing required columns: {', '.join(missing_required)}")

        # Check for completely empty DataFrame
        if df.empty:
            errors.append("DataFrame is empty")

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None


class ISO17025Validator:
    """Validate data for ISO 17025 compliance."""

    # Maximum allowed calibration period (in days)
    MAX_CALIBRATION_PERIOD_DAYS = 365

    # Minimum required metadata fields
    REQUIRED_METADATA_FIELDS = [
        "lab_name",
        "lab_accreditation_number",
        "test_method",
        "test_date",
        "operator_id",
        "equipment_id",
    ]

    @staticmethod
    def validate_metadata(metadata: ISO17025Metadata) -> Tuple[bool, Optional[List[str]]]:
        """Validate ISO 17025 metadata completeness.

        Args:
            metadata: ISO17025Metadata object

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields are not empty
        if not metadata.lab_name or metadata.lab_name.strip() == "":
            errors.append("Lab name is required")

        if not metadata.lab_accreditation_number or metadata.lab_accreditation_number.strip() == "":
            errors.append("Lab accreditation number is required")

        if not metadata.test_method or metadata.test_method.strip() == "":
            errors.append("Test method/standard is required")

        if not metadata.operator_id or metadata.operator_id.strip() == "":
            errors.append("Operator ID is required")

        if not metadata.equipment_id or metadata.equipment_id.strip() == "":
            errors.append("Equipment ID is required")

        # Validate test date is not in future
        if metadata.test_date > datetime.now():
            errors.append("Test date cannot be in the future")

        # Validate calibration due date if provided
        if metadata.calibration_due_date:
            if metadata.calibration_due_date < datetime.now():
                errors.append("Equipment calibration is overdue")

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None

    @staticmethod
    def validate_calibration(
        calibration_date: datetime, calibration_due_date: datetime
    ) -> Tuple[bool, Optional[List[str]]]:
        """Validate equipment calibration status.

        Args:
            calibration_date: Last calibration date
            calibration_due_date: Next calibration due date

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        current_time = datetime.now()

        # Check calibration is not overdue
        if calibration_due_date < current_time:
            days_overdue = (current_time - calibration_due_date).days
            errors.append(f"Calibration is overdue by {days_overdue} days")

        # Check calibration period is reasonable
        calibration_period = (calibration_due_date - calibration_date).days
        if calibration_period > ISO17025Validator.MAX_CALIBRATION_PERIOD_DAYS:
            errors.append(
                f"Calibration period ({calibration_period} days) exceeds maximum "
                f"({ISO17025Validator.MAX_CALIBRATION_PERIOD_DAYS} days)"
            )

        # Check calibration date is not in future
        if calibration_date > current_time:
            errors.append("Calibration date cannot be in the future")

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None

    @staticmethod
    def validate_traceability(
        traceability_chain: Optional[List[str]],
    ) -> Tuple[bool, Optional[List[str]]]:
        """Validate calibration traceability chain.

        Args:
            traceability_chain: List of calibration references to national standards

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not traceability_chain or len(traceability_chain) == 0:
            errors.append("Traceability chain to national standards is required")
            return False, errors

        # Check for minimum traceability documentation
        if len(traceability_chain) < 2:
            errors.append(
                "Traceability chain should include at least 2 levels "
                "(e.g., working standard -> reference standard)"
            )

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None

    @staticmethod
    def validate_uncertainty(
        uncertainty_budget: Optional[Dict[str, float]],
    ) -> Tuple[bool, Optional[List[str]]]:
        """Validate measurement uncertainty documentation.

        Args:
            uncertainty_budget: Dictionary of uncertainty components

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not uncertainty_budget or len(uncertainty_budget) == 0:
            errors.append("Measurement uncertainty budget is required for ISO 17025")
            return False, errors

        # Check for negative uncertainties
        for component, value in uncertainty_budget.items():
            if value < 0:
                errors.append(f"Uncertainty component '{component}' cannot be negative")

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None

    @staticmethod
    def validate_environmental_conditions(
        environmental_conditions: Optional[Dict[str, float]],
        required_params: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[List[str]]]:
        """Validate environmental conditions documentation.

        Args:
            environmental_conditions: Dictionary of environmental parameters
            required_params: List of required parameter names

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not environmental_conditions:
            errors.append("Environmental conditions must be documented")
            return False, errors

        # Default required parameters
        if required_params is None:
            required_params = ["temperature", "humidity"]

        # Check required parameters are present
        missing_params = set(required_params) - set(environmental_conditions.keys())
        if missing_params:
            errors.append(f"Missing environmental parameters: {', '.join(missing_params)}")

        # Validate reasonable ranges
        if "temperature" in environmental_conditions:
            temp = environmental_conditions["temperature"]
            if temp < 15 or temp > 35:
                errors.append(
                    f"Temperature ({temp}°C) outside typical lab range (15-35°C)"
                )

        if "humidity" in environmental_conditions:
            humidity = environmental_conditions["humidity"]
            if humidity < 20 or humidity > 80:
                errors.append(
                    f"Humidity ({humidity}%) outside typical lab range (20-80%)"
                )

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None

    @staticmethod
    def validate_full_compliance(
        metadata: ISO17025Metadata,
        calibration_date: Optional[datetime] = None,
        calibration_due_date: Optional[datetime] = None,
    ) -> Tuple[bool, Dict[str, List[str]]]:
        """Perform full ISO 17025 compliance validation.

        Args:
            metadata: ISO17025Metadata object
            calibration_date: Optional calibration date (uses metadata if not provided)
            calibration_due_date: Optional calibration due date

        Returns:
            Tuple of (is_valid, errors_by_category)
        """
        all_errors: Dict[str, List[str]] = {}

        # Validate metadata
        is_valid, errors = ISO17025Validator.validate_metadata(metadata)
        if errors:
            all_errors["metadata"] = errors

        # Validate calibration if dates provided
        if calibration_date and calibration_due_date:
            is_valid, errors = ISO17025Validator.validate_calibration(
                calibration_date, calibration_due_date
            )
            if errors:
                all_errors["calibration"] = errors
        elif metadata.calibration_due_date:
            # Try to validate with metadata
            cal_date = datetime.now() - timedelta(days=180)  # Assume 6 months ago
            is_valid, errors = ISO17025Validator.validate_calibration(
                cal_date, metadata.calibration_due_date
            )
            if errors:
                all_errors["calibration"] = errors

        # Validate traceability
        is_valid, errors = ISO17025Validator.validate_traceability(
            metadata.traceability_chain
        )
        if errors:
            all_errors["traceability"] = errors

        # Validate uncertainty
        is_valid, errors = ISO17025Validator.validate_uncertainty(
            metadata.uncertainty_budget
        )
        if errors:
            all_errors["uncertainty"] = errors

        # Validate environmental conditions
        is_valid, errors = ISO17025Validator.validate_environmental_conditions(
            metadata.environmental_conditions
        )
        if errors:
            all_errors["environmental"] = errors

        is_compliant = len(all_errors) == 0
        return is_compliant, all_errors if all_errors else {}
