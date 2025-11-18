"""
Excel Editor Component

Streamlit-based Excel editor with AgGrid integration for cell editing,
formulas, validation, import/export, and bulk operations.
"""

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import json
import re
from io import BytesIO
import openpyxl

from .editor_utils import (
    EditorState,
    EditorType,
    UndoRedoManager,
    AutoSaveManager,
    EditorValidator,
    ActionType,
    EditorAction,
    init_session_state,
    format_timestamp,
)


@dataclass
class CellValidation:
    """Cell validation rule"""
    column: str
    rule_type: str  # "range", "list", "regex", "custom"
    rule_value: Any
    error_message: str = "Invalid value"

    def validate(self, value: Any) -> bool:
        """Validate cell value"""
        if self.rule_type == "range":
            min_val, max_val = self.rule_value
            return min_val <= value <= max_val
        elif self.rule_type == "list":
            return value in self.rule_value
        elif self.rule_type == "regex":
            return bool(re.match(self.rule_value, str(value)))
        elif self.rule_type == "custom":
            return self.rule_value(value)
        return True


@dataclass
class CellFormula:
    """Cell formula definition"""
    cell: str  # e.g., "C1"
    formula: str  # e.g., "=A1+B1"
    dependencies: List[str] = field(default_factory=list)

    def evaluate(self, data: pd.DataFrame) -> Any:
        """Evaluate formula"""
        # Simple formula evaluation
        # In production, use a proper expression evaluator
        try:
            # Replace cell references with values
            expr = self.formula.lstrip("=")
            for dep in self.dependencies:
                col, row = self._parse_cell_ref(dep)
                if col in data.columns and row < len(data):
                    value = data.iloc[row][col]
                    expr = expr.replace(dep, str(value))

            # Evaluate
            return eval(expr)
        except Exception:
            return "#ERROR!"

    @staticmethod
    def _parse_cell_ref(ref: str) -> tuple:
        """Parse cell reference like 'A1' to ('A', 0)"""
        match = re.match(r"([A-Z]+)(\d+)", ref)
        if match:
            col = match.group(1)
            row = int(match.group(2)) - 1
            return col, row
        return None, None


class ExcelEditor:
    """
    Excel-like editor component with AgGrid.

    Features:
    - Interactive grid editing
    - Cell formulas
    - Data validation
    - Import/Export (CSV, Excel)
    - Bulk operations
    - Conditional formatting
    - Filtering and sorting
    """

    def __init__(
        self,
        editor_id: str = "excel_editor",
        auto_save_interval: int = 60,
        max_history: int = 50,
    ):
        """
        Initialize Excel editor.

        Args:
            editor_id: Unique editor identifier
            auto_save_interval: Auto-save interval in seconds
            max_history: Maximum undo/redo history
        """
        self.editor_id = editor_id
        self.state_key = f"{editor_id}_state"

        # Initialize state
        self._init_state()

        # Initialize managers
        self.undo_manager = UndoRedoManager(max_history=max_history)
        self.validator = EditorValidator()

        # Setup auto-save
        self.auto_save_manager = AutoSaveManager(
            save_callback=self._save_callback,
            auto_save_interval=auto_save_interval,
        )

        # Validation rules and formulas
        self.validations: List[CellValidation] = []
        self.formulas: List[CellFormula] = []

    def _init_state(self):
        """Initialize editor state"""
        if self.state_key not in st.session_state:
            # Create empty DataFrame
            df = pd.DataFrame({
                "A": [""] * 10,
                "B": [""] * 10,
                "C": [""] * 10,
            })

            state = EditorState(
                editor_id=self.editor_id,
                editor_type=EditorType.EXCEL,
                content={
                    "data": df.to_dict(),
                    "name": "Untitled Sheet",
                    "validations": [],
                    "formulas": [],
                },
            )
            st.session_state[self.state_key] = state

    def _save_callback(self, state: EditorState) -> bool:
        """Save callback for auto-save"""
        try:
            state.mark_saved()
            return True
        except Exception:
            return False

    def get_state(self) -> EditorState:
        """Get current editor state"""
        return st.session_state[self.state_key]

    def get_dataframe(self) -> pd.DataFrame:
        """Get current DataFrame"""
        state = self.get_state()
        return pd.DataFrame.from_dict(state.content.get("data", {}))

    def set_dataframe(self, df: pd.DataFrame):
        """Set DataFrame"""
        state = self.get_state()
        state.content["data"] = df.to_dict()
        state.mark_modified()

    def render(self):
        """Render the Excel editor"""
        st.subheader("📊 Excel Editor")

        state = self.get_state()

        # Toolbar
        self._render_toolbar(state)

        # Grid
        self._render_grid(state)

        # Bulk operations
        with st.expander("🔧 Bulk Operations"):
            self._render_bulk_operations(state)

        # Validations
        with st.expander("✓ Data Validation"):
            self._render_validations(state)

        # Formulas
        with st.expander("ƒ Formulas"):
            self._render_formulas(state)

        # Auto-save
        if self.auto_save_manager.auto_save(state):
            st.toast("✅ Auto-saved", icon="💾")

    def _render_toolbar(self, state: EditorState):
        """Render toolbar"""
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            # Sheet name
            new_name = st.text_input(
                "Sheet Name",
                value=state.content.get("name", "Untitled Sheet"),
                key=f"{self.editor_id}_name",
            )
            if new_name != state.content.get("name"):
                state.content["name"] = new_name
                state.mark_modified()

        with col2:
            # Save
            if st.button("💾 Save", use_container_width=True):
                if self.auto_save_manager.manual_save(state):
                    st.success("Saved!")

        with col3:
            # Import
            uploaded = st.file_uploader(
                "Import",
                type=["csv", "xlsx"],
                key=f"{self.editor_id}_import",
                label_visibility="collapsed",
            )
            if uploaded:
                self._import_file(uploaded, state)

        with col4:
            # Export CSV
            if st.button("📥 CSV", use_container_width=True):
                self._export_csv(state)

        with col5:
            # Export Excel
            if st.button("📥 Excel", use_container_width=True):
                self._export_excel(state)

        # Status
        df = self.get_dataframe()
        st.caption(f"Rows: {len(df)} | Columns: {len(df.columns)} | Modified: {'Yes' if state.modified else 'No'}")

    def _render_grid(self, state: EditorState):
        """Render AgGrid"""
        df = self.get_dataframe()

        # Configure grid
        gb = GridOptionsBuilder.from_dataframe(df)

        # Enable editing
        gb.configure_default_column(
            editable=True,
            resizable=True,
            sortable=True,
            filter=True,
        )

        # Enable selection
        gb.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
        )

        # Enable pagination
        gb.configure_pagination(
            enabled=True,
            paginationPageSize=20,
        )

        # Enable sidebar
        gb.configure_side_bar()

        grid_options = gb.build()

        # Render grid
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            height=400,
            allow_unsafe_jscode=True,
            key=f"{self.editor_id}_grid",
        )

        # Update DataFrame if changed
        if grid_response and grid_response["data"] is not None:
            new_df = pd.DataFrame(grid_response["data"])
            if not new_df.equals(df):
                self.set_dataframe(new_df)

        # Show selected rows
        if grid_response and grid_response["selected_rows"] is not None:
            selected = grid_response["selected_rows"]
            if len(selected) > 0:
                st.info(f"Selected {len(selected)} row(s)")

    def _render_bulk_operations(self, state: EditorState):
        """Render bulk operations"""
        df = self.get_dataframe()

        st.markdown("#### Bulk Operations")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Add Rows/Columns**")

            num_rows = st.number_input("Rows to add", min_value=1, value=5, key=f"{self.editor_id}_add_rows")
            if st.button("Add Rows", key=f"{self.editor_id}_do_add_rows"):
                self._add_rows(num_rows, state)

            num_cols = st.number_input("Columns to add", min_value=1, value=1, key=f"{self.editor_id}_add_cols")
            col_name = st.text_input("Column name", key=f"{self.editor_id}_col_name")
            if st.button("Add Column", key=f"{self.editor_id}_do_add_col") and col_name:
                self._add_column(col_name, state)

        with col2:
            st.markdown("**Fill Operations**")

            fill_col = st.selectbox("Column", df.columns, key=f"{self.editor_id}_fill_col")
            fill_value = st.text_input("Fill value", key=f"{self.editor_id}_fill_val")

            if st.button("Fill Column", key=f"{self.editor_id}_do_fill"):
                self._fill_column(fill_col, fill_value, state)

            # Clear operations
            if st.button("Clear All", key=f"{self.editor_id}_clear_all"):
                if st.warning("Are you sure?"):
                    self._clear_all(state)

    def _render_validations(self, state: EditorState):
        """Render validation rules"""
        st.markdown("#### Data Validation Rules")

        df = self.get_dataframe()

        col1, col2 = st.columns(2)

        with col1:
            val_col = st.selectbox("Column", df.columns, key=f"{self.editor_id}_val_col")
            val_type = st.selectbox(
                "Type",
                ["range", "list", "regex"],
                key=f"{self.editor_id}_val_type"
            )

        with col2:
            if val_type == "range":
                min_val = st.number_input("Min", key=f"{self.editor_id}_val_min")
                max_val = st.number_input("Max", key=f"{self.editor_id}_val_max")
                val_value = (min_val, max_val)
            elif val_type == "list":
                list_values = st.text_input("Values (comma-separated)", key=f"{self.editor_id}_val_list")
                val_value = [v.strip() for v in list_values.split(",")]
            else:  # regex
                val_value = st.text_input("Pattern", key=f"{self.editor_id}_val_regex")

        if st.button("Add Validation", key=f"{self.editor_id}_add_val"):
            validation = CellValidation(
                column=val_col,
                rule_type=val_type,
                rule_value=val_value,
            )
            self.validations.append(validation)
            st.success(f"Added validation for {val_col}")

        # Show existing validations
        if self.validations:
            st.markdown("**Active Validations:**")
            for i, val in enumerate(self.validations):
                st.text(f"{i+1}. {val.column}: {val.rule_type} = {val.rule_value}")

    def _render_formulas(self, state: EditorState):
        """Render formula editor"""
        st.markdown("#### Formulas")

        df = self.get_dataframe()

        col1, col2 = st.columns(2)

        with col1:
            cell_ref = st.text_input("Cell (e.g., C1)", key=f"{self.editor_id}_formula_cell")

        with col2:
            formula = st.text_input("Formula (e.g., =A1+B1)", key=f"{self.editor_id}_formula_expr")

        if st.button("Add Formula", key=f"{self.editor_id}_add_formula"):
            if cell_ref and formula:
                # Extract dependencies
                deps = re.findall(r"[A-Z]+\d+", formula)

                cell_formula = CellFormula(
                    cell=cell_ref,
                    formula=formula,
                    dependencies=deps,
                )
                self.formulas.append(cell_formula)
                st.success(f"Added formula: {cell_ref} = {formula}")

        # Evaluate formulas
        if st.button("Evaluate All Formulas", key=f"{self.editor_id}_eval_formulas"):
            self._evaluate_formulas(state)

        # Show existing formulas
        if self.formulas:
            st.markdown("**Active Formulas:**")
            for i, formula in enumerate(self.formulas):
                st.text(f"{i+1}. {formula.cell} = {formula.formula}")

    def _add_rows(self, num_rows: int, state: EditorState):
        """Add rows to DataFrame"""
        df = self.get_dataframe()

        # Create empty rows
        new_rows = pd.DataFrame(
            {col: [""] * num_rows for col in df.columns}
        )

        df = pd.concat([df, new_rows], ignore_index=True)
        self.set_dataframe(df)

        st.success(f"Added {num_rows} row(s)")
        st.rerun()

    def _add_column(self, col_name: str, state: EditorState):
        """Add column to DataFrame"""
        df = self.get_dataframe()

        if col_name not in df.columns:
            df[col_name] = ""
            self.set_dataframe(df)
            st.success(f"Added column: {col_name}")
            st.rerun()
        else:
            st.error(f"Column '{col_name}' already exists")

    def _fill_column(self, column: str, value: str, state: EditorState):
        """Fill column with value"""
        df = self.get_dataframe()

        if column in df.columns:
            df[column] = value
            self.set_dataframe(df)
            st.success(f"Filled column '{column}' with '{value}'")
            st.rerun()

    def _clear_all(self, state: EditorState):
        """Clear all data"""
        df = self.get_dataframe()
        df[:] = ""
        self.set_dataframe(df)
        st.success("Cleared all data")
        st.rerun()

    def _evaluate_formulas(self, state: EditorState):
        """Evaluate all formulas"""
        df = self.get_dataframe()

        for formula in self.formulas:
            result = formula.evaluate(df)

            # Set result in DataFrame
            col, row = formula._parse_cell_ref(formula.cell)
            if col in df.columns and row < len(df):
                df.iloc[row, df.columns.get_loc(col)] = result

        self.set_dataframe(df)
        st.success("Evaluated all formulas")
        st.rerun()

    def _import_file(self, uploaded_file, state: EditorState):
        """Import CSV or Excel file"""
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Unsupported file format")
                return

            self.set_dataframe(df)
            st.success(f"Imported {len(df)} rows")
            st.rerun()

        except Exception as e:
            st.error(f"Import failed: {str(e)}")

    def _export_csv(self, state: EditorState):
        """Export as CSV"""
        df = self.get_dataframe()

        csv = df.to_csv(index=False)
        filename = f"{state.content.get('name', 'sheet')}.csv"

        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
        )

    def _export_excel(self, state: EditorState):
        """Export as Excel"""
        df = self.get_dataframe()

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=state.content.get('name', 'Sheet1'))

        output.seek(0)
        filename = f"{state.content.get('name', 'sheet')}.xlsx"

        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def apply_conditional_formatting(
        self,
        column: str,
        condition: Callable[[Any], bool],
        style: Dict[str, str],
    ):
        """
        Apply conditional formatting to column.

        Args:
            column: Column name
            condition: Function to test cell value
            style: CSS style to apply
        """
        # Store formatting rule
        # In production, this would be applied in AgGrid configuration
        pass

    def validate_data(self) -> bool:
        """
        Validate all data against validation rules.

        Returns:
            True if all validations pass
        """
        df = self.get_dataframe()
        all_valid = True

        for validation in self.validations:
            if validation.column in df.columns:
                for value in df[validation.column]:
                    if not validation.validate(value):
                        all_valid = False
                        st.error(
                            f"Validation failed in {validation.column}: "
                            f"{validation.error_message}"
                        )

        return all_valid


# Export
__all__ = ["ExcelEditor", "CellValidation", "CellFormula"]
