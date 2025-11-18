"""Tests for schema validators and ISO 17025 compliance."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.models.ingestion_models import ISO17025Metadata
from src.ingestion.validators import SchemaValidator, ISO17025Validator


class TestSchemaValidator:
    """Test schema validation."""

    def test_validate_dataframe_schema_valid(self):
        """Test valid DataFrame schema."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        is_valid, errors = SchemaValidator.validate_dataframe_schema(
            df, required_columns=["col1", "col2"]
        )

        assert is_valid is True
        assert errors is None

    def test_validate_dataframe_schema_missing_columns(self):
        """Test DataFrame with missing required columns."""
        df = pd.DataFrame({"col1": [1, 2, 3]})

        is_valid, errors = SchemaValidator.validate_dataframe_schema(
            df, required_columns=["col1", "col2", "col3"]
        )

        assert is_valid is False
        assert errors is not None
        assert "col2" in errors[0]
        assert "col3" in errors[0]

    def test_validate_empty_dataframe(self):
        """Test empty DataFrame validation."""
        df = pd.DataFrame()

        is_valid, errors = SchemaValidator.validate_dataframe_schema(
            df, required_columns=[]
        )

        assert is_valid is False
        assert "empty" in errors[0].lower()


class TestISO17025Validator:
    """Test ISO 17025 compliance validation."""

    def test_validate_metadata_valid(self):
        """Test valid ISO 17025 metadata."""
        metadata = ISO17025Metadata(
            lab_name="Test Lab",
            lab_accreditation_number="ISO17025-12345",
            test_method="IEC 61215",
            test_date=datetime.now() - timedelta(days=1),
            operator_id="OP-001",
            equipment_id="EQ-001",
            calibration_due_date=datetime.now() + timedelta(days=180),
        )

        is_valid, errors = ISO17025Validator.validate_metadata(metadata)

        assert is_valid is True
        assert errors is None

    def test_validate_metadata_missing_fields(self):
        """Test metadata with missing required fields."""
        metadata = ISO17025Metadata(
            lab_name="",  # Empty
            lab_accreditation_number="ISO17025-12345",
            test_method="IEC 61215",
            test_date=datetime.now(),
            operator_id="OP-001",
            equipment_id="EQ-001",
        )

        is_valid, errors = ISO17025Validator.validate_metadata(metadata)

        assert is_valid is False
        assert any("lab name" in e.lower() for e in errors)

    def test_validate_calibration_valid(self):
        """Test valid calibration dates."""
        cal_date = datetime.now() - timedelta(days=180)
        cal_due = datetime.now() + timedelta(days=180)

        is_valid, errors = ISO17025Validator.validate_calibration(cal_date, cal_due)

        assert is_valid is True
        assert errors is None

    def test_validate_calibration_overdue(self):
        """Test overdue calibration."""
        cal_date = datetime.now() - timedelta(days=400)
        cal_due = datetime.now() - timedelta(days=10)  # Overdue

        is_valid, errors = ISO17025Validator.validate_calibration(cal_date, cal_due)

        assert is_valid is False
        assert any("overdue" in e.lower() for e in errors)

    def test_validate_traceability_valid(self):
        """Test valid traceability chain."""
        chain = [
            "Working Standard WS-001",
            "Reference Standard RS-001 (NIST traceable)",
        ]

        is_valid, errors = ISO17025Validator.validate_traceability(chain)

        assert is_valid is True
        assert errors is None

    def test_validate_traceability_missing(self):
        """Test missing traceability chain."""
        is_valid, errors = ISO17025Validator.validate_traceability(None)

        assert is_valid is False
        assert any("traceability" in e.lower() for e in errors)

    def test_validate_uncertainty_valid(self):
        """Test valid uncertainty budget."""
        uncertainty = {
            "calibration": 0.5,
            "repeatability": 0.3,
            "resolution": 0.1,
            "drift": 0.2,
        }

        is_valid, errors = ISO17025Validator.validate_uncertainty(uncertainty)

        assert is_valid is True
        assert errors is None

    def test_validate_uncertainty_missing(self):
        """Test missing uncertainty budget."""
        is_valid, errors = ISO17025Validator.validate_uncertainty(None)

        assert is_valid is False
        assert any("uncertainty" in e.lower() for e in errors)

    def test_validate_environmental_conditions_valid(self):
        """Test valid environmental conditions."""
        conditions = {"temperature": 23.0, "humidity": 45.0}

        is_valid, errors = ISO17025Validator.validate_environmental_conditions(
            conditions
        )

        assert is_valid is True
        assert errors is None

    def test_validate_environmental_conditions_out_of_range(self):
        """Test environmental conditions out of range."""
        conditions = {"temperature": 40.0, "humidity": 90.0}  # Too high

        is_valid, errors = ISO17025Validator.validate_environmental_conditions(
            conditions
        )

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_full_compliance(self):
        """Test full compliance validation."""
        metadata = ISO17025Metadata(
            lab_name="Accredited PV Test Lab",
            lab_accreditation_number="ISO17025-12345",
            test_method="IEC 61215-1",
            test_date=datetime.now() - timedelta(days=1),
            operator_id="OP-001",
            equipment_id="IV-TRACER-001",
            calibration_due_date=datetime.now() + timedelta(days=180),
            environmental_conditions={"temperature": 23.0, "humidity": 45.0},
            uncertainty_budget={
                "calibration": 0.5,
                "repeatability": 0.3,
                "resolution": 0.1,
            },
            traceability_chain=[
                "Working Standard WS-001",
                "NIST-traceable Reference",
            ],
        )

        cal_date = datetime.now() - timedelta(days=180)
        cal_due = datetime.now() + timedelta(days=180)

        is_compliant, errors = ISO17025Validator.validate_full_compliance(
            metadata, cal_date, cal_due
        )

        assert is_compliant is True
        assert len(errors) == 0
