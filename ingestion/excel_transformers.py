"""
Excel Data Transformation Utilities

Provides transformation functions for Excel data including pivot table flattening,
multi-header column naming, unit conversion, timestamp parsing, and precision handling.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


class ExcelTransformer:
    """
    Transformer for Excel data.

    Handles:
    - Pivot table flattening
    - Multi-header column naming
    - Unit conversion
    - Timestamp parsing
    - Numeric precision handling
    """

    def __init__(self):
        """Initialize transformer with unit conversion tables."""
        # Common unit conversions for PV testing
        self.unit_conversions = {
            'voltage': {
                'mV': 0.001,
                'V': 1.0,
                'kV': 1000.0
            },
            'current': {
                'μA': 1e-6,
                'mA': 0.001,
                'A': 1.0,
                'kA': 1000.0
            },
            'power': {
                'mW': 0.001,
                'W': 1.0,
                'kW': 1000.0,
                'MW': 1e6
            },
            'temperature': {
                'C': lambda x: x,
                'K': lambda x: x - 273.15,
                'F': lambda x: (x - 32) * 5/9
            },
            'irradiance': {
                'W/m²': 1.0,
                'W/cm²': 10000.0
            },
            'time': {
                's': 1.0,
                'min': 60.0,
                'h': 3600.0,
                'hr': 3600.0,
                'd': 86400.0
            }
        }

    def flatten_pivot_table(
        self,
        df: pd.DataFrame,
        reset_index: bool = True
    ) -> pd.DataFrame:
        """
        Flatten a pivot table to regular DataFrame format.

        Args:
            df: DataFrame with MultiIndex (pivot table)
            reset_index: Whether to reset index to columns

        Returns:
            Flattened DataFrame
        """
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten column MultiIndex
            df.columns = [
                ' - '.join(str(col).strip() for col in cols if col)
                for cols in df.columns.values
            ]

        if isinstance(df.index, pd.MultiIndex) and reset_index:
            # Flatten row MultiIndex
            df = df.reset_index()

        return df

    def combine_multi_level_headers(
        self,
        df: pd.DataFrame,
        separator: str = ' - ',
        prefix: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Combine multi-level headers into single-level with separator.

        Args:
            df: DataFrame with MultiIndex columns
            separator: String to join header levels
            prefix: Optional prefix for all column names

        Returns:
            DataFrame with flattened column names
        """
        if not isinstance(df.columns, pd.MultiIndex):
            # Already single level
            if prefix:
                df.columns = [f"{prefix}{separator}{col}" for col in df.columns]
            return df

        # Combine levels
        new_columns = []
        for col in df.columns:
            # Filter out None or empty strings
            parts = [str(part) for part in col if part and str(part).strip()]
            combined = separator.join(parts)

            if prefix:
                combined = f"{prefix}{separator}{combined}"

            new_columns.append(combined)

        df.columns = new_columns

        return df

    def convert_units(
        self,
        df: pd.DataFrame,
        column: str,
        from_unit: str,
        to_unit: str,
        unit_type: str
    ) -> pd.DataFrame:
        """
        Convert values from one unit to another.

        Args:
            df: DataFrame to transform
            column: Column name to convert
            from_unit: Source unit
            to_unit: Target unit
            unit_type: Type of unit ('voltage', 'current', 'power', etc.)

        Returns:
            DataFrame with converted values
        """
        if unit_type not in self.unit_conversions:
            raise ValueError(f"Unknown unit type: {unit_type}")

        conversions = self.unit_conversions[unit_type]

        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(
                f"Unknown units for {unit_type}: {from_unit} or {to_unit}"
            )

        # Get conversion factors
        from_factor = conversions[from_unit]
        to_factor = conversions[to_unit]

        # Handle callable conversions (like temperature)
        if callable(from_factor) or callable(to_factor):
            if unit_type == 'temperature':
                # Special handling for temperature
                if from_unit == 'F':
                    df[column] = df[column].apply(lambda x: (x - 32) * 5/9)
                elif from_unit == 'K':
                    df[column] = df[column] - 273.15

                if to_unit == 'F':
                    df[column] = df[column] * 9/5 + 32
                elif to_unit == 'K':
                    df[column] = df[column] + 273.15
        else:
            # Standard conversion
            df[column] = df[column] * (from_factor / to_factor)

        # Update column name to reflect new unit
        new_column_name = column.replace(from_unit, to_unit)
        df = df.rename(columns={column: new_column_name})

        return df

    def auto_detect_and_convert_units(
        self,
        df: pd.DataFrame,
        column: str,
        target_unit: str,
        unit_type: str
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Automatically detect source unit and convert to target unit.

        Args:
            df: DataFrame to transform
            column: Column name to convert
            target_unit: Target unit
            unit_type: Type of unit ('voltage', 'current', 'power', etc.)

        Returns:
            Tuple of (transformed DataFrame, detected source unit)
        """
        if unit_type not in self.unit_conversions:
            return df, None

        conversions = self.unit_conversions[unit_type]

        # Try to detect unit from column name
        detected_unit = None
        for unit in conversions.keys():
            if unit in column:
                detected_unit = unit
                break

        if detected_unit and detected_unit != target_unit:
            df = self.convert_units(df, column, detected_unit, target_unit, unit_type)
            return df, detected_unit

        return df, detected_unit

    def parse_timestamp(
        self,
        df: pd.DataFrame,
        column: str,
        format: Optional[str] = None,
        handle_excel_serial: bool = True
    ) -> pd.DataFrame:
        """
        Parse timestamp/date column to datetime.

        Args:
            df: DataFrame to transform
            column: Column name containing timestamps
            format: Datetime format string (None for automatic detection)
            handle_excel_serial: Whether to handle Excel serial dates

        Returns:
            DataFrame with parsed timestamps
        """
        if column not in df.columns:
            return df

        # Handle Excel serial dates (numeric values)
        if handle_excel_serial and pd.api.types.is_numeric_dtype(df[column]):
            # Excel serial date: days since 1899-12-30
            try:
                excel_epoch = pd.Timestamp('1899-12-30')
                df[column] = pd.to_timedelta(df[column], unit='D') + excel_epoch
                return df
            except:
                pass  # Fall through to standard parsing

        # Standard datetime parsing
        if format:
            df[column] = pd.to_datetime(df[column], format=format, errors='coerce')
        else:
            # Automatic format detection
            df[column] = pd.to_datetime(df[column], errors='coerce', infer_datetime_format=True)

        return df

    def normalize_numeric_precision(
        self,
        df: pd.DataFrame,
        column: str,
        decimals: int
    ) -> pd.DataFrame:
        """
        Normalize numeric precision to specified decimal places.

        Args:
            df: DataFrame to transform
            column: Column name to normalize
            decimals: Number of decimal places

        Returns:
            DataFrame with normalized precision
        """
        if column in df.columns:
            df[column] = df[column].round(decimals)

        return df

    def clean_column_names(
        self,
        df: pd.DataFrame,
        lowercase: bool = False,
        remove_special_chars: bool = True,
        replace_spaces: str = '_'
    ) -> pd.DataFrame:
        """
        Clean and standardize column names.

        Args:
            df: DataFrame to transform
            lowercase: Convert to lowercase
            remove_special_chars: Remove special characters
            replace_spaces: Replace spaces with this character

        Returns:
            DataFrame with cleaned column names
        """
        new_columns = []

        for col in df.columns:
            new_col = str(col).strip()

            if lowercase:
                new_col = new_col.lower()

            if replace_spaces:
                new_col = new_col.replace(' ', replace_spaces)

            if remove_special_chars:
                # Keep alphanumeric, underscore, and hyphen
                new_col = re.sub(r'[^a-zA-Z0-9_-]', '', new_col)

            new_columns.append(new_col)

        df.columns = new_columns

        return df

    def fill_missing_values(
        self,
        df: pd.DataFrame,
        method: str = 'forward',
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fill missing values using specified method.

        Args:
            df: DataFrame to transform
            method: Fill method ('forward', 'backward', 'mean', 'median', 'zero')
            columns: Specific columns to fill (None for all)
            limit: Maximum number of consecutive NaNs to fill

        Returns:
            DataFrame with filled values
        """
        if columns is None:
            columns = df.columns

        for col in columns:
            if col not in df.columns:
                continue

            if method == 'forward':
                df[col] = df[col].fillna(method='ffill', limit=limit)
            elif method == 'backward':
                df[col] = df[col].fillna(method='bfill', limit=limit)
            elif method == 'mean':
                df[col] = df[col].fillna(df[col].mean())
            elif method == 'median':
                df[col] = df[col].fillna(df[col].median())
            elif method == 'zero':
                df[col] = df[col].fillna(0)

        return df

    def remove_outliers(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Remove outliers from a column.

        Args:
            df: DataFrame to transform
            column: Column name to process
            method: Detection method ('zscore' or 'iqr')
            threshold: Z-score threshold or IQR multiplier

        Returns:
            DataFrame with outliers removed
        """
        if column not in df.columns:
            return df

        if method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(df[column].dropna()))
            # Create mask for all rows
            mask = pd.Series(True, index=df.index)
            mask.loc[df[column].notna()] = z_scores < threshold
            df = df[mask]

        elif method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - (threshold * IQR)
            upper_bound = Q3 + (threshold * IQR)

            df = df[
                (df[column] >= lower_bound) &
                (df[column] <= upper_bound)
            ]

        return df

    def interpolate_missing_data(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = 'linear'
    ) -> pd.DataFrame:
        """
        Interpolate missing data points.

        Args:
            df: DataFrame to transform
            column: Column name to interpolate
            method: Interpolation method ('linear', 'polynomial', 'spline')

        Returns:
            DataFrame with interpolated values
        """
        if column in df.columns:
            df[column] = df[column].interpolate(method=method)

        return df

    def aggregate_time_series(
        self,
        df: pd.DataFrame,
        time_column: str,
        value_columns: List[str],
        frequency: str,
        aggregation: str = 'mean'
    ) -> pd.DataFrame:
        """
        Aggregate time-series data to specified frequency.

        Args:
            df: DataFrame to transform
            time_column: Column containing timestamps
            value_columns: Columns to aggregate
            frequency: Pandas frequency string ('1H', '1D', etc.)
            aggregation: Aggregation method ('mean', 'sum', 'min', 'max')

        Returns:
            Aggregated DataFrame
        """
        # Ensure time column is datetime
        df[time_column] = pd.to_datetime(df[time_column])

        # Set time as index
        df = df.set_index(time_column)

        # Resample and aggregate
        if aggregation == 'mean':
            df = df[value_columns].resample(frequency).mean()
        elif aggregation == 'sum':
            df = df[value_columns].resample(frequency).sum()
        elif aggregation == 'min':
            df = df[value_columns].resample(frequency).min()
        elif aggregation == 'max':
            df = df[value_columns].resample(frequency).max()

        return df.reset_index()

    def extract_unit_from_column_name(
        self,
        column_name: str
    ) -> Tuple[str, Optional[str]]:
        """
        Extract unit from column name.

        Examples:
            "Temperature (°C)" -> ("Temperature", "°C")
            "Voltage [V]" -> ("Voltage", "V")
            "Current_A" -> ("Current", "A")

        Args:
            column_name: Column name to parse

        Returns:
            Tuple of (base_name, unit)
        """
        # Pattern 1: Name (Unit)
        match = re.search(r'(.+?)\s*\(([^)]+)\)', column_name)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        # Pattern 2: Name [Unit]
        match = re.search(r'(.+?)\s*\[([^\]]+)\]', column_name)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        # Pattern 3: Name_Unit
        match = re.search(r'(.+?)_([A-Za-z°]+)$', column_name)
        if match:
            base = match.group(1)
            unit = match.group(2)
            # Check if unit is valid
            if len(unit) <= 5:  # Reasonable unit length
                return base.strip(), unit.strip()

        # No unit found
        return column_name, None

    def standardize_units_in_dataframe(
        self,
        df: pd.DataFrame,
        standard_units: Dict[str, Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        Standardize units across DataFrame based on mapping.

        Args:
            df: DataFrame to transform
            standard_units: Dict mapping column base names to (unit_type, target_unit)
                           e.g., {'Voltage': ('voltage', 'V'), 'Current': ('current', 'A')}

        Returns:
            DataFrame with standardized units
        """
        for col in df.columns:
            base_name, current_unit = self.extract_unit_from_column_name(col)

            if base_name in standard_units and current_unit:
                unit_type, target_unit = standard_units[base_name]

                try:
                    df, detected = self.auto_detect_and_convert_units(
                        df, col, target_unit, unit_type
                    )
                except Exception:
                    # Skip if conversion fails
                    pass

        return df

    def split_datetime_components(
        self,
        df: pd.DataFrame,
        datetime_column: str,
        components: List[str] = ['year', 'month', 'day', 'hour', 'minute']
    ) -> pd.DataFrame:
        """
        Split datetime column into separate components.

        Args:
            df: DataFrame to transform
            datetime_column: Column containing datetime values
            components: List of components to extract

        Returns:
            DataFrame with additional component columns
        """
        if datetime_column not in df.columns:
            return df

        dt_series = pd.to_datetime(df[datetime_column])

        for component in components:
            if component == 'year':
                df[f'{datetime_column}_year'] = dt_series.dt.year
            elif component == 'month':
                df[f'{datetime_column}_month'] = dt_series.dt.month
            elif component == 'day':
                df[f'{datetime_column}_day'] = dt_series.dt.day
            elif component == 'hour':
                df[f'{datetime_column}_hour'] = dt_series.dt.hour
            elif component == 'minute':
                df[f'{datetime_column}_minute'] = dt_series.dt.minute
            elif component == 'second':
                df[f'{datetime_column}_second'] = dt_series.dt.second
            elif component == 'dayofweek':
                df[f'{datetime_column}_dayofweek'] = dt_series.dt.dayofweek
            elif component == 'dayofyear':
                df[f'{datetime_column}_dayofyear'] = dt_series.dt.dayofyear

        return df
