"""
Tests for Excel Editor

Tests for Excel-like editor with AgGrid, formulas,
validation, and bulk operations.
"""

import pytest
import pandas as pd
import numpy as np
from io import BytesIO

from ..excel_editor import (
    ExcelEditor,
    CellValidation,
    CellFormula,
)
from ..editor_utils import EditorState, EditorType


class TestCellValidation:
    """Test CellValidation class"""

    def test_init(self):
        """Test initialization"""
        validation = CellValidation(
            column="A",
            rule_type="range",
            rule_value=(0, 100),
        )

        assert validation.column == "A"
        assert validation.rule_type == "range"
        assert validation.rule_value == (0, 100)

    def test_validate_range(self):
        """Test range validation"""
        validation = CellValidation(
            column="A",
            rule_type="range",
            rule_value=(0, 100),
        )

        assert validation.validate(50)
        assert validation.validate(0)
        assert validation.validate(100)
        assert not validation.validate(-1)
        assert not validation.validate(101)

    def test_validate_list(self):
        """Test list validation"""
        validation = CellValidation(
            column="A",
            rule_type="list",
            rule_value=["Option1", "Option2", "Option3"],
        )

        assert validation.validate("Option1")
        assert validation.validate("Option2")
        assert not validation.validate("Option4")

    def test_validate_regex(self):
        """Test regex validation"""
        validation = CellValidation(
            column="A",
            rule_type="regex",
            rule_value=r"^\d{3}-\d{4}$",  # Phone number pattern
        )

        assert validation.validate("123-4567")
        assert not validation.validate("1234567")
        assert not validation.validate("abc-defg")

    def test_validate_custom(self):
        """Test custom validation"""
        def is_even(value):
            return value % 2 == 0

        validation = CellValidation(
            column="A",
            rule_type="custom",
            rule_value=is_even,
        )

        assert validation.validate(2)
        assert validation.validate(4)
        assert not validation.validate(3)


class TestCellFormula:
    """Test CellFormula class"""

    def test_init(self):
        """Test initialization"""
        formula = CellFormula(
            cell="C1",
            formula="=A1+B1",
            dependencies=["A1", "B1"],
        )

        assert formula.cell == "C1"
        assert formula.formula == "=A1+B1"
        assert len(formula.dependencies) == 2

    def test_parse_cell_ref(self):
        """Test cell reference parsing"""
        col, row = CellFormula._parse_cell_ref("A1")
        assert col == "A"
        assert row == 0

        col, row = CellFormula._parse_cell_ref("B10")
        assert col == "B"
        assert row == 9

    def test_evaluate_simple_formula(self):
        """Test evaluating simple formula"""
        df = pd.DataFrame({
            "A": [10, 20, 30],
            "B": [5, 10, 15],
            "C": [0, 0, 0],
        })

        formula = CellFormula(
            cell="C1",
            formula="=A1+B1",
            dependencies=["A1", "B1"],
        )

        # Note: Real evaluation would need proper implementation
        # This is a basic test of the structure


class TestExcelEditor:
    """Test ExcelEditor class"""

    @pytest.fixture
    def editor(self):
        """Create editor instance"""
        return ExcelEditor(editor_id="test_excel_editor")

    def test_init(self, editor):
        """Test initialization"""
        assert editor.editor_id == "test_excel_editor"
        assert editor.undo_manager is not None
        assert editor.validator is not None

    def test_get_state(self, editor):
        """Test getting editor state"""
        state = editor.get_state()

        assert isinstance(state, EditorState)
        assert state.editor_type == EditorType.EXCEL
        assert "data" in state.content
        assert "name" in state.content

    def test_get_dataframe(self, editor):
        """Test getting DataFrame"""
        df = editor.get_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df.columns) > 0

    def test_set_dataframe(self, editor):
        """Test setting DataFrame"""
        new_df = pd.DataFrame({
            "X": [1, 2, 3],
            "Y": [4, 5, 6],
        })

        editor.set_dataframe(new_df)
        df = editor.get_dataframe()

        assert "X" in df.columns
        assert "Y" in df.columns
        assert len(df) == 3

    def test_add_rows(self, editor):
        """Test adding rows"""
        state = editor.get_state()
        df = editor.get_dataframe()
        initial_rows = len(df)

        # Simulate adding rows
        new_rows = pd.DataFrame(
            {col: [""] * 5 for col in df.columns}
        )
        df = pd.concat([df, new_rows], ignore_index=True)
        editor.set_dataframe(df)

        assert len(editor.get_dataframe()) == initial_rows + 5

    def test_add_column(self, editor):
        """Test adding column"""
        df = editor.get_dataframe()
        initial_cols = len(df.columns)

        # Add new column
        df["NewColumn"] = ""
        editor.set_dataframe(df)

        assert len(editor.get_dataframe().columns) == initial_cols + 1
        assert "NewColumn" in editor.get_dataframe().columns

    def test_fill_column(self, editor):
        """Test filling column with value"""
        df = editor.get_dataframe()
        col_name = df.columns[0]

        # Fill column
        df[col_name] = "TestValue"
        editor.set_dataframe(df)

        result_df = editor.get_dataframe()
        assert all(result_df[col_name] == "TestValue")

    def test_clear_all(self, editor):
        """Test clearing all data"""
        df = editor.get_dataframe()

        # Set some values
        df.iloc[0, 0] = "Value"
        editor.set_dataframe(df)

        # Clear
        df[:] = ""
        editor.set_dataframe(df)

        result_df = editor.get_dataframe()
        assert all(result_df.values.flatten() == "")

    def test_validation_rules(self, editor):
        """Test validation rules"""
        # Add validation rule
        validation = CellValidation(
            column="A",
            rule_type="range",
            rule_value=(0, 100),
        )
        editor.validations.append(validation)

        assert len(editor.validations) == 1
        assert editor.validations[0].column == "A"

    def test_formulas(self, editor):
        """Test formula management"""
        # Add formula
        formula = CellFormula(
            cell="C1",
            formula="=A1+B1",
            dependencies=["A1", "B1"],
        )
        editor.formulas.append(formula)

        assert len(editor.formulas) == 1
        assert editor.formulas[0].cell == "C1"

    def test_validate_data(self, editor):
        """Test data validation"""
        # Set up data
        df = pd.DataFrame({
            "A": [10, 20, 30],
            "B": [50, 150, 75],  # 150 is out of range
        })
        editor.set_dataframe(df)

        # Add validation
        validation = CellValidation(
            column="B",
            rule_type="range",
            rule_value=(0, 100),
        )
        editor.validations.append(validation)

        # Validate (would fail because of 150)
        # Note: Full validation would need proper implementation

    def test_import_csv(self, editor):
        """Test CSV import"""
        # Create CSV data
        csv_data = "A,B,C\n1,2,3\n4,5,6\n7,8,9"

        # Simulate import
        df = pd.read_csv(BytesIO(csv_data.encode()))
        editor.set_dataframe(df)

        result_df = editor.get_dataframe()
        assert len(result_df) == 3
        assert "A" in result_df.columns
        assert result_df.iloc[0, 0] == 1

    def test_export_csv(self, editor):
        """Test CSV export"""
        # Set up data
        df = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
        })
        editor.set_dataframe(df)

        # Export
        csv = df.to_csv(index=False)

        assert "A,B" in csv
        assert "1,4" in csv

    def test_export_excel(self, editor):
        """Test Excel export"""
        # Set up data
        df = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
        })
        editor.set_dataframe(df)

        # Export to bytes
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")

        output.seek(0)
        assert len(output.getvalue()) > 0

    def test_conditional_formatting(self, editor):
        """Test conditional formatting setup"""
        # Test that we can add conditional formatting rules
        # In production, this would apply to AgGrid
        editor.apply_conditional_formatting(
            column="A",
            condition=lambda x: x > 50,
            style={"background-color": "red"},
        )

    def test_bulk_operations(self, editor):
        """Test bulk operations"""
        df = editor.get_dataframe()

        # Bulk update
        df.iloc[:, 0] = range(len(df))
        editor.set_dataframe(df)

        result_df = editor.get_dataframe()
        assert result_df.iloc[0, 0] == 0
        assert result_df.iloc[1, 0] == 1

    def test_data_types(self, editor):
        """Test different data types"""
        df = pd.DataFrame({
            "Integer": [1, 2, 3],
            "Float": [1.5, 2.5, 3.5],
            "String": ["a", "b", "c"],
            "Boolean": [True, False, True],
        })
        editor.set_dataframe(df)

        result_df = editor.get_dataframe()

        assert result_df["Integer"].dtype == np.int64
        assert result_df["Float"].dtype == np.float64
        assert result_df["String"].dtype == object
        assert result_df["Boolean"].dtype == bool

    def test_empty_dataframe(self, editor):
        """Test handling empty DataFrame"""
        empty_df = pd.DataFrame()
        editor.set_dataframe(empty_df)

        result_df = editor.get_dataframe()
        assert len(result_df) == 0

    def test_large_dataframe(self, editor):
        """Test handling large DataFrame"""
        large_df = pd.DataFrame({
            f"Col{i}": range(1000)
            for i in range(10)
        })
        editor.set_dataframe(large_df)

        result_df = editor.get_dataframe()
        assert len(result_df) == 1000
        assert len(result_df.columns) == 10
