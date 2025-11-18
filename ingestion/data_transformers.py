"""
Data Transformation Utilities

Comprehensive data transformation tools for PV test data including
unit conversions, column mapping, aggregation, and data cleaning.
"""

from typing import Optional, List, Dict, Any, Callable, Union
import pandas as pd
import numpy as np
from pathlib import Path

from .models import TransformationConfig
from .exceptions import TransformationError


class DataTransformer:
    """
    Data transformation utility for PV test data.

    Features:
    - Unit conversion (automatic detection)
    - Column renaming/mapping
    - Data aggregation
    - Pivot table operations
    - Missing data interpolation
    - Outlier detection and removal
    - Data type conversion
    - Custom transformations

    Example:
        >>> transformer = DataTransformer(df)
        >>> df = transformer.convert_units({'power': ('W', 'kW')})
        >>> df = transformer.rename_columns({'V': 'Voltage', 'I': 'Current'})
        >>> df = transformer.remove_outliers(['power'], method='zscore')
    """

    # Unit conversion factors (to base SI unit)
    UNIT_CONVERSIONS = {
        # Power
        ('W', 'kW'): 0.001,
        ('W', 'MW'): 1e-6,
        ('kW', 'W'): 1000,
        ('MW', 'W'): 1e6,
        ('mW', 'W'): 0.001,

        # Voltage
        ('V', 'mV'): 1000,
        ('V', 'kV'): 0.001,
        ('mV', 'V'): 0.001,
        ('kV', 'V'): 1000,

        # Current
        ('A', 'mA'): 1000,
        ('A', 'kA'): 0.001,
        ('mA', 'A'): 0.001,
        ('kA', 'A'): 1000,

        # Energy
        ('Wh', 'kWh'): 0.001,
        ('Wh', 'MWh'): 1e-6,
        ('kWh', 'Wh'): 1000,
        ('MWh', 'Wh'): 1e6,
        ('J', 'Wh'): 0.000277778,
        ('Wh', 'J'): 3600,

        # Temperature
        ('C', 'K'): lambda x: x + 273.15,
        ('K', 'C'): lambda x: x - 273.15,
        ('C', 'F'): lambda x: x * 9/5 + 32,
        ('F', 'C'): lambda x: (x - 32) * 5/9,

        # Irradiance
        ('W/m2', 'kW/m2'): 0.001,
        ('kW/m2', 'W/m2'): 1000,

        # Pressure
        ('Pa', 'kPa'): 0.001,
        ('kPa', 'Pa'): 1000,
        ('Pa', 'bar'): 1e-5,
        ('bar', 'Pa'): 1e5,

        # Area
        ('m2', 'cm2'): 10000,
        ('cm2', 'm2'): 0.0001,
    }

    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize data transformer.

        Args:
            dataframe: DataFrame to transform
        """
        self.df = dataframe.copy()
        self._original_df = dataframe.copy()

    def get_dataframe(self) -> pd.DataFrame:
        """Get current transformed DataFrame."""
        return self.df

    def reset(self) -> 'DataTransformer':
        """Reset to original DataFrame."""
        self.df = self._original_df.copy()
        return self

    def convert_units(
        self,
        conversions: Dict[str, tuple],
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Convert units for specified columns.

        Args:
            conversions: {column: (from_unit, to_unit)}
            inplace: Modify DataFrame in place

        Returns:
            Transformed DataFrame

        Example:
            >>> df = transformer.convert_units({
            ...     'power': ('W', 'kW'),
            ...     'voltage': ('V', 'mV')
            ... })
        """
        df = self.df if inplace else self.df.copy()

        for col, (from_unit, to_unit) in conversions.items():
            if col not in df.columns:
                raise TransformationError(f"Column '{col}' not found")

            conversion_key = (from_unit, to_unit)

            if conversion_key not in self.UNIT_CONVERSIONS:
                raise TransformationError(
                    f"Unknown unit conversion: {from_unit} -> {to_unit}"
                )

            factor = self.UNIT_CONVERSIONS[conversion_key]

            if callable(factor):
                # Temperature conversions (lambda functions)
                df[col] = df[col].apply(factor)
            else:
                # Simple multiplication
                df[col] = df[col] * factor

        if inplace:
            self.df = df

        return df

    def rename_columns(
        self,
        mapping: Dict[str, str],
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Rename columns.

        Args:
            mapping: {old_name: new_name}
            inplace: Modify DataFrame in place

        Returns:
            Transformed DataFrame
        """
        df = self.df if inplace else self.df.copy()
        df = df.rename(columns=mapping)

        if inplace:
            self.df = df

        return df

    def drop_columns(
        self,
        columns: List[str],
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Drop columns.

        Args:
            columns: Columns to drop
            inplace: Modify DataFrame in place

        Returns:
            Transformed DataFrame
        """
        df = self.df if inplace else self.df.copy()
        existing_cols = [col for col in columns if col in df.columns]

        if existing_cols:
            df = df.drop(columns=existing_cols)

        if inplace:
            self.df = df

        return df

    def filter_rows(
        self,
        conditions: Dict[str, Any],
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Filter rows based on conditions.

        Args:
            conditions: {column: value} or {column: (operator, value)}
            inplace: Modify DataFrame in place

        Returns:
            Filtered DataFrame

        Example:
            >>> df = transformer.filter_rows({
            ...     'efficiency': ('>', 15),
            ...     'grade': 'A'
            ... })
        """
        df = self.df if inplace else self.df.copy()

        for col, condition in conditions.items():
            if col not in df.columns:
                raise TransformationError(f"Column '{col}' not found")

            if isinstance(condition, tuple):
                operator, value = condition

                if operator == '>':
                    df = df[df[col] > value]
                elif operator == '>=':
                    df = df[df[col] >= value]
                elif operator == '<':
                    df = df[df[col] < value]
                elif operator == '<=':
                    df = df[df[col] <= value]
                elif operator == '==':
                    df = df[df[col] == value]
                elif operator == '!=':
                    df = df[df[col] != value]
                else:
                    raise TransformationError(f"Unknown operator: {operator}")
            else:
                # Direct equality
                df = df[df[col] == condition]

        if inplace:
            self.df = df

        return df

    def aggregate(
        self,
        group_by: Union[str, List[str]],
        aggregations: Dict[str, Union[str, List[str]]],
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Aggregate data by groups.

        Args:
            group_by: Column(s) to group by
            aggregations: {column: 'function'} or {column: ['func1', 'func2']}
            inplace: Modify DataFrame in place

        Returns:
            Aggregated DataFrame

        Example:
            >>> df = transformer.aggregate(
            ...     group_by='serial_number',
            ...     aggregations={'power': ['mean', 'std'], 'voltage': 'max'}
            ... )
        """
        df = self.df if inplace else self.df.copy()

        grouped = df.groupby(group_by)
        df = grouped.agg(aggregations).reset_index()

        # Flatten column names if multi-level
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip('_') for col in df.columns.values]

        if inplace:
            self.df = df

        return df

    def pivot(
        self,
        index: str,
        columns: str,
        values: str,
        aggfunc: str = 'mean',
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Create pivot table.

        Args:
            index: Column to use as index
            columns: Column to use as columns
            values: Column to aggregate
            aggfunc: Aggregation function
            inplace: Modify DataFrame in place

        Returns:
            Pivot table DataFrame
        """
        df = self.df if inplace else self.df.copy()

        df = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
        ).reset_index()

        if inplace:
            self.df = df

        return df

    def remove_outliers(
        self,
        columns: List[str],
        method: str = 'zscore',
        threshold: float = 3.0,
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Remove outliers from data.

        Args:
            columns: Columns to check for outliers
            method: Detection method ('zscore' or 'iqr')
            threshold: Z-score threshold or IQR multiplier
            inplace: Modify DataFrame in place

        Returns:
            DataFrame with outliers removed
        """
        df = self.df if inplace else self.df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            if method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df = df[z_scores <= threshold]

            elif method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

            else:
                raise TransformationError(f"Unknown outlier method: {method}")

        if inplace:
            self.df = df

        return df

    def fill_missing(
        self,
        columns: Optional[List[str]] = None,
        method: str = 'ffill',
        value: Optional[Any] = None,
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Fill missing values.

        Args:
            columns: Columns to fill (all if None)
            method: Fill method ('ffill', 'bfill', 'interpolate', 'value')
            value: Value to fill with (if method='value')
            inplace: Modify DataFrame in place

        Returns:
            DataFrame with missing values filled
        """
        df = self.df if inplace else self.df.copy()

        if columns is None:
            columns = df.columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            if method == 'ffill':
                df[col] = df[col].fillna(method='ffill')
            elif method == 'bfill':
                df[col] = df[col].fillna(method='bfill')
            elif method == 'interpolate':
                df[col] = df[col].interpolate()
            elif method == 'value':
                if value is None:
                    raise TransformationError("Value required for method='value'")
                df[col] = df[col].fillna(value)
            else:
                raise TransformationError(f"Unknown fill method: {method}")

        if inplace:
            self.df = df

        return df

    def calculate_derived_column(
        self,
        column_name: str,
        formula: Union[str, Callable],
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Calculate derived column from existing columns.

        Args:
            column_name: Name for new column
            formula: Formula string or callable
            inplace: Modify DataFrame in place

        Returns:
            DataFrame with new column

        Example:
            >>> # Formula string
            >>> df = transformer.calculate_derived_column(
            ...     'power', 'voltage * current'
            ... )
            >>> # Callable
            >>> df = transformer.calculate_derived_column(
            ...     'efficiency', lambda row: row['pmax'] / row['pin'] * 100
            ... )
        """
        df = self.df if inplace else self.df.copy()

        if callable(formula):
            df[column_name] = df.apply(formula, axis=1)
        else:
            # Evaluate formula string
            df[column_name] = df.eval(formula)

        if inplace:
            self.df = df

        return df

    def normalize_column(
        self,
        column: str,
        method: str = 'minmax',
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Normalize column values.

        Args:
            column: Column to normalize
            method: Normalization method ('minmax' or 'zscore')
            inplace: Modify DataFrame in place

        Returns:
            DataFrame with normalized column
        """
        df = self.df if inplace else self.df.copy()

        if column not in df.columns:
            raise TransformationError(f"Column '{column}' not found")

        if method == 'minmax':
            # Scale to [0, 1]
            min_val = df[column].min()
            max_val = df[column].max()
            df[column] = (df[column] - min_val) / (max_val - min_val)

        elif method == 'zscore':
            # Standardize to mean=0, std=1
            mean_val = df[column].mean()
            std_val = df[column].std()
            df[column] = (df[column] - mean_val) / std_val

        else:
            raise TransformationError(f"Unknown normalization method: {method}")

        if inplace:
            self.df = df

        return df

    def apply_config(
        self,
        config: TransformationConfig,
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        Apply transformation configuration.

        Args:
            config: Transformation configuration
            inplace: Modify DataFrame in place

        Returns:
            Transformed DataFrame
        """
        df = self.df if inplace else self.df.copy()

        # Column mapping
        if config.column_mapping:
            df = self.rename_columns(config.column_mapping, inplace=False)

        # Unit conversions
        if config.unit_conversions:
            transformer = DataTransformer(df)
            df = transformer.convert_units(config.unit_conversions, inplace=False)

        # Drop columns
        if config.drop_columns:
            transformer = DataTransformer(df)
            df = transformer.drop_columns(config.drop_columns, inplace=False)

        # Filter conditions
        if config.filter_conditions:
            transformer = DataTransformer(df)
            df = transformer.filter_rows(config.filter_conditions, inplace=False)

        # Aggregations
        if config.aggregate_functions:
            # Assume aggregating all data
            transformer = DataTransformer(df)
            agg_dict = config.aggregate_functions
            df = pd.DataFrame([df[list(agg_dict.keys())].agg(agg_dict)])

        # Pivot
        if config.pivot_config:
            transformer = DataTransformer(df)
            df = transformer.pivot(**config.pivot_config, inplace=False)

        if inplace:
            self.df = df

        return df

    def export(
        self,
        output_path: Union[str, Path],
        format: str = 'csv',
        **kwargs
    ) -> None:
        """
        Export transformed data.

        Args:
            output_path: Output file path
            format: Export format ('csv', 'json', 'excel', 'parquet')
            **kwargs: Additional arguments for export function
        """
        output_path = Path(output_path)

        if format == 'csv':
            self.df.to_csv(output_path, **kwargs)
        elif format == 'json':
            self.df.to_json(output_path, **kwargs)
        elif format == 'excel':
            self.df.to_excel(output_path, **kwargs)
        elif format == 'parquet':
            self.df.to_parquet(output_path, **kwargs)
        else:
            raise TransformationError(f"Unknown export format: {format}")
