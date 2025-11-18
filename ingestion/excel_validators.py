"""
Excel-Specific Validators

Provides validation functions for Excel data including missing values,
data types, duplicates, outliers, and unit consistency.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats


class ExcelValidator:
    """
    Validator for Excel data with focus on PV test data quality.

    Performs validation for:
    - Missing values
    - Data type consistency
    - Duplicate entries
    - Statistical outliers
    - Unit consistency
    """

    def __init__(self):
        """Initialize validator with default thresholds."""
        self.outlier_threshold = 3.0  # Z-score threshold
        self.missing_data_threshold = 0.1  # 10% threshold for warnings

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        strict: bool = False
    ) -> Dict[str, List[str]]:
        """
        Perform comprehensive validation on a DataFrame.

        Args:
            df: DataFrame to validate
            strict: If True, raise errors for warnings

        Returns:
            Dictionary with 'warnings' and 'errors' lists
        """
        result = {
            'warnings': [],
            'errors': []
        }

        # Check for empty DataFrame
        if df.empty:
            result['errors'].append("DataFrame is empty")
            return result

        # Validate missing values
        missing_result = self.validate_missing_values(df)
        result['warnings'].extend(missing_result.get('warnings', []))
        result['errors'].extend(missing_result.get('errors', []))

        # Validate data types
        dtype_result = self.validate_data_types(df)
        result['warnings'].extend(dtype_result.get('warnings', []))

        # Check for duplicates
        duplicate_result = self.validate_duplicates(df)
        result['warnings'].extend(duplicate_result.get('warnings', []))

        # Check for outliers in numeric columns
        outlier_result = self.detect_outliers(df)
        result['warnings'].extend(outlier_result.get('warnings', []))

        return result

    def validate_missing_values(
        self,
        df: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """
        Detect and report missing values.

        Args:
            df: DataFrame to check

        Returns:
            Dictionary with warnings and errors
        """
        result = {'warnings': [], 'errors': []}

        missing_counts = df.isnull().sum()
        missing_pcts = (missing_counts / len(df)) * 100

        for col, count in missing_counts[missing_counts > 0].items():
            pct = missing_pcts[col]
            msg = f"Column '{col}': {count} missing values ({pct:.1f}%)"

            if pct > self.missing_data_threshold * 100:
                result['warnings'].append(msg)

            # Critical: more than 50% missing
            if pct > 50:
                result['errors'].append(
                    f"Column '{col}' has >50% missing values ({pct:.1f}%)"
                )

        return result

    def validate_data_types(
        self,
        df: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """
        Validate data type consistency.

        Args:
            df: DataFrame to check

        Returns:
            Dictionary with warnings
        """
        result = {'warnings': []}

        for col in df.columns:
            # Check for mixed types
            if df[col].dtype == 'object':
                # Try to infer if it should be numeric
                numeric_count = pd.to_numeric(
                    df[col],
                    errors='coerce'
                ).notna().sum()

                total_count = df[col].notna().sum()

                if total_count > 0:
                    numeric_pct = (numeric_count / total_count) * 100

                    # If >80% are numeric, suggest conversion
                    if numeric_pct > 80:
                        result['warnings'].append(
                            f"Column '{col}' is object type but {numeric_pct:.1f}% "
                            "values are numeric. Consider data type conversion."
                        )

        return result

    def validate_duplicates(
        self,
        df: pd.DataFrame,
        subset: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Check for duplicate rows.

        Args:
            df: DataFrame to check
            subset: Columns to check for duplicates (None = all columns)

        Returns:
            Dictionary with warnings
        """
        result = {'warnings': []}

        duplicate_count = df.duplicated(subset=subset).sum()

        if duplicate_count > 0:
            result['warnings'].append(
                f"Found {duplicate_count} duplicate rows"
            )

            # Show which columns have duplicates if subset specified
            if subset:
                result['warnings'].append(
                    f"Duplicates based on columns: {', '.join(subset)}"
                )

        return result

    def detect_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = 'zscore'
    ) -> Dict[str, List[str]]:
        """
        Detect statistical outliers in numeric columns.

        Args:
            df: DataFrame to check
            columns: Specific columns to check (None = all numeric columns)
            method: Detection method ('zscore' or 'iqr')

        Returns:
            Dictionary with warnings
        """
        result = {'warnings': []}

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            data = df[col].dropna()

            if len(data) == 0:
                continue

            if method == 'zscore':
                outliers = self._detect_outliers_zscore(data)
            elif method == 'iqr':
                outliers = self._detect_outliers_iqr(data)
            else:
                continue

            if outliers.any():
                outlier_count = outliers.sum()
                outlier_pct = (outlier_count / len(data)) * 100

                result['warnings'].append(
                    f"Column '{col}': {outlier_count} outliers detected "
                    f"({outlier_pct:.1f}%) using {method} method"
                )

        return result

    def _detect_outliers_zscore(
        self,
        data: pd.Series
    ) -> pd.Series:
        """
        Detect outliers using Z-score method.

        Args:
            data: Series to check

        Returns:
            Boolean series indicating outliers
        """
        z_scores = np.abs(stats.zscore(data, nan_policy='omit'))
        return z_scores > self.outlier_threshold

    def _detect_outliers_iqr(
        self,
        data: pd.Series
    ) -> pd.Series:
        """
        Detect outliers using Interquartile Range (IQR) method.

        Args:
            data: Series to check

        Returns:
            Boolean series indicating outliers
        """
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        return (data < lower_bound) | (data > upper_bound)

    def validate_unit_consistency(
        self,
        df: pd.DataFrame,
        column: str,
        expected_range: Tuple[float, float],
        unit_multipliers: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Validate unit consistency by checking if values fall within expected range.

        This can detect if data is in wrong units (e.g., mV instead of V, mA instead of A).

        Args:
            df: DataFrame to check
            column: Column name to validate
            expected_range: (min, max) expected value range
            unit_multipliers: Dict of possible unit conversions
                             e.g., {'mV': 0.001, 'V': 1.0}

        Returns:
            Dictionary with validation results and suggested conversion
        """
        result = {
            'warnings': [],
            'in_range_count': 0,
            'out_of_range_count': 0,
            'suggested_conversion': None
        }

        if column not in df.columns:
            result['warnings'].append(f"Column '{column}' not found")
            return result

        data = pd.to_numeric(df[column], errors='coerce').dropna()

        if len(data) == 0:
            result['warnings'].append(f"No numeric data in column '{column}'")
            return result

        # Check how many values are in expected range
        in_range = (data >= expected_range[0]) & (data <= expected_range[1])
        result['in_range_count'] = in_range.sum()
        result['out_of_range_count'] = (~in_range).sum()

        in_range_pct = (result['in_range_count'] / len(data)) * 100

        # If less than 50% are in range, might be unit issue
        if in_range_pct < 50 and unit_multipliers:
            # Try each multiplier to see which brings data into range
            best_match = None
            best_pct = in_range_pct

            for unit, multiplier in unit_multipliers.items():
                converted_data = data * multiplier
                converted_in_range = (
                    (converted_data >= expected_range[0]) &
                    (converted_data <= expected_range[1])
                )
                converted_pct = (converted_in_range.sum() / len(data)) * 100

                if converted_pct > best_pct:
                    best_pct = converted_pct
                    best_match = (unit, multiplier)

            if best_match:
                result['suggested_conversion'] = best_match
                result['warnings'].append(
                    f"Column '{column}': Only {in_range_pct:.1f}% of values "
                    f"in expected range {expected_range}. "
                    f"Suggest conversion from {best_match[0]} "
                    f"(multiplier: {best_match[1]})"
                )
        elif in_range_pct < 90:
            result['warnings'].append(
                f"Column '{column}': {result['out_of_range_count']} values "
                f"({100-in_range_pct:.1f}%) outside expected range {expected_range}"
            )

        return result

    def validate_timestamp_format(
        self,
        df: pd.DataFrame,
        column: str
    ) -> Dict[str, List[str]]:
        """
        Validate timestamp/date format consistency.

        Args:
            df: DataFrame to check
            column: Column name containing timestamps

        Returns:
            Dictionary with warnings
        """
        result = {'warnings': [], 'errors': []}

        if column not in df.columns:
            result['errors'].append(f"Column '{column}' not found")
            return result

        try:
            # Try to convert to datetime
            timestamps = pd.to_datetime(df[column], errors='coerce')
            failed_conversions = timestamps.isna().sum() - df[column].isna().sum()

            if failed_conversions > 0:
                result['warnings'].append(
                    f"Column '{column}': {failed_conversions} values "
                    "could not be parsed as timestamps"
                )

            # Check for future dates
            if timestamps.notna().any():
                max_date = timestamps.max()
                if pd.notna(max_date) and max_date > pd.Timestamp.now():
                    result['warnings'].append(
                        f"Column '{column}': Contains future dates (max: {max_date})"
                    )

        except Exception as e:
            result['errors'].append(
                f"Error validating timestamp format: {str(e)}"
            )

        return result

    def validate_numeric_precision(
        self,
        df: pd.DataFrame,
        column: str,
        expected_decimals: int
    ) -> Dict[str, List[str]]:
        """
        Validate numeric precision (number of decimal places).

        Args:
            df: DataFrame to check
            column: Column name to validate
            expected_decimals: Expected number of decimal places

        Returns:
            Dictionary with warnings
        """
        result = {'warnings': []}

        if column not in df.columns:
            result['warnings'].append(f"Column '{column}' not found")
            return result

        data = pd.to_numeric(df[column], errors='coerce').dropna()

        if len(data) == 0:
            return result

        # Count decimal places
        decimal_counts = data.astype(str).str.split('.').str[1].str.len().fillna(0)
        avg_decimals = decimal_counts.mean()

        if abs(avg_decimals - expected_decimals) > 1:
            result['warnings'].append(
                f"Column '{column}': Average decimal places ({avg_decimals:.1f}) "
                f"differs from expected ({expected_decimals})"
            )

        return result
