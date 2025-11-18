"""
Time-Series Data Parser

Specialized parser for time-series PV test data including I-V curves,
environmental chamber logs, and sensor readings.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime

from .csv_parser import CSVIngestion
from .json_parser import JSONIngestion
from .models import TimeSeriesConfig, ValidationError as ValidationErrorModel
from .exceptions import TimeSeriesError


class TimeSeriesParser:
    """
    Time-series data parser for PV test equipment.

    Features:
    - I-V curve measurements
    - Environmental chamber logs
    - Data logger exports
    - Power output monitoring
    - Irradiance sensor data
    - Automatic timestamp parsing
    - Data resampling and aggregation
    - Outlier detection
    - Missing data interpolation

    Example:
        >>> config = TimeSeriesConfig(
        ...     timestamp_col="Time",
        ...     value_cols=["Voltage", "Current", "Power"]
        ... )
        >>> parser = TimeSeriesParser("iv_curve.csv", config)
        >>> df = parser.parse()
        >>> df_resampled = parser.resample("1s")
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        config: TimeSeriesConfig,
        file_type: Optional[str] = None,
    ):
        """
        Initialize time-series parser.

        Args:
            file_path: Path to data file
            config: Time-series configuration
            file_type: File type ('csv' or 'json', auto-detected if None)
        """
        self.file_path = Path(file_path)
        self.config = config
        self._dataframe: Optional[pd.DataFrame] = None

        # Determine file type
        if file_type is None:
            suffix = self.file_path.suffix.lower()
            if suffix in ['.csv', '.txt']:
                file_type = 'csv'
            elif suffix in ['.json', '.jsonl']:
                file_type = 'json'
            else:
                raise TimeSeriesError(f"Unknown file type: {suffix}")

        self.file_type = file_type

    def parse(self) -> pd.DataFrame:
        """
        Parse time-series data file.

        Returns:
            DataFrame with timestamp index and value columns

        Raises:
            TimeSeriesError: If parsing fails
        """
        try:
            # Parse based on file type
            if self.file_type == 'csv':
                ingestion = CSVIngestion(self.file_path)
                result = ingestion.parse_timeseries(
                    timestamp_col=self.config.timestamp_col,
                    value_cols=self.config.value_cols,
                    timestamp_format=self.config.timestamp_format,
                )

                if not result.is_valid:
                    error_msgs = [e.message for e in result.errors]
                    raise TimeSeriesError(f"CSV parsing failed: {error_msgs}")

                df = ingestion.get_dataframe()

            elif self.file_type == 'json':
                ingestion = JSONIngestion(self.file_path)
                result = ingestion.parse(flatten=True)

                if not result.is_valid:
                    error_msgs = [e.message for e in result.errors]
                    raise TimeSeriesError(f"JSON parsing failed: {error_msgs}")

                df = ingestion.get_dataframe()

                # Parse timestamp column
                if self.config.timestamp_col not in df.columns:
                    raise TimeSeriesError(
                        f"Timestamp column '{self.config.timestamp_col}' not found"
                    )

                df[self.config.timestamp_col] = pd.to_datetime(
                    df[self.config.timestamp_col],
                    format=self.config.timestamp_format,
                    errors='coerce'
                )

                # Set timestamp as index
                df = df.set_index(self.config.timestamp_col)

            else:
                raise TimeSeriesError(f"Unsupported file type: {self.file_type}")

            # Validate value columns exist
            missing_cols = set(self.config.value_cols) - set(df.columns)
            if missing_cols:
                raise TimeSeriesError(f"Missing value columns: {missing_cols}")

            # Sort by timestamp
            df = df.sort_index()

            # Handle timezone if specified
            if self.config.timezone:
                df.index = df.index.tz_localize(self.config.timezone)

            self._dataframe = df
            return df

        except Exception as e:
            raise TimeSeriesError(f"Failed to parse time-series data: {str(e)}")

    def get_dataframe(self) -> pd.DataFrame:
        """
        Get parsed DataFrame.

        Returns:
            Parsed DataFrame with timestamp index

        Raises:
            ValueError: If parse() has not been called
        """
        if self._dataframe is None:
            raise ValueError("Data not yet parsed. Call parse() first.")
        return self._dataframe

    def resample(
        self,
        frequency: str,
        aggregation: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Resample time-series data to different frequency.

        Args:
            frequency: Resampling frequency (e.g., '1min', '1H', '1D')
            aggregation: Column-specific aggregation functions
                         {column: 'mean'/'sum'/'min'/'max'/'first'/'last'}

        Returns:
            Resampled DataFrame

        Example:
            >>> df = parser.resample('1min', {'Power': 'mean', 'Energy': 'sum'})
        """
        df = self.get_dataframe()

        if aggregation:
            resampled = df.resample(frequency).agg(aggregation)
        else:
            # Default to mean for all numeric columns
            resampled = df.resample(frequency).mean()

        return resampled

    def detect_outliers(
        self,
        columns: Optional[List[str]] = None,
        method: str = 'zscore',
        threshold: float = 3.0,
    ) -> pd.DataFrame:
        """
        Detect outliers in time-series data.

        Args:
            columns: Columns to check (all value columns if None)
            method: Detection method ('zscore' or 'iqr')
            threshold: Z-score threshold or IQR multiplier

        Returns:
            DataFrame with outlier flags (True = outlier)
        """
        df = self.get_dataframe()

        if columns is None:
            columns = self.config.value_cols

        outliers = pd.DataFrame(index=df.index)

        for col in columns:
            if col not in df.columns:
                continue

            if method == 'zscore':
                # Z-score method
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers[col] = z_scores > threshold

            elif method == 'iqr':
                # Interquartile range method
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outliers[col] = (df[col] < lower_bound) | (df[col] > upper_bound)

            else:
                raise ValueError(f"Unknown outlier detection method: {method}")

        return outliers

    def interpolate_missing(
        self,
        columns: Optional[List[str]] = None,
        method: str = 'linear',
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Interpolate missing values in time-series data.

        Args:
            columns: Columns to interpolate (all value columns if None)
            method: Interpolation method ('linear', 'time', 'nearest', 'cubic')
            limit: Maximum number of consecutive NaNs to fill

        Returns:
            DataFrame with interpolated values
        """
        df = self.get_dataframe().copy()

        if columns is None:
            columns = self.config.value_cols

        for col in columns:
            if col in df.columns:
                df[col] = df[col].interpolate(
                    method=method,
                    limit=limit,
                    limit_direction='both'
                )

        return df

    def calculate_statistics(
        self,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Calculate statistical summary of time-series data.

        Args:
            columns: Columns to analyze (all value columns if None)

        Returns:
            DataFrame with statistics (mean, std, min, max, etc.)
        """
        df = self.get_dataframe()

        if columns is None:
            columns = self.config.value_cols

        stats = df[columns].describe()
        return stats

    def detect_gaps(self, max_gap: pd.Timedelta) -> pd.DataFrame:
        """
        Detect time gaps in data.

        Args:
            max_gap: Maximum acceptable gap between timestamps

        Returns:
            DataFrame with gap information (start, end, duration)
        """
        df = self.get_dataframe()

        # Calculate time differences
        time_diffs = df.index.to_series().diff()

        # Find gaps larger than threshold
        gaps = time_diffs[time_diffs > max_gap]

        if len(gaps) == 0:
            return pd.DataFrame(columns=['gap_start', 'gap_end', 'duration'])

        gap_info = pd.DataFrame({
            'gap_start': gaps.index - gaps,
            'gap_end': gaps.index,
            'duration': gaps,
        })

        return gap_info

    def parse_iv_curve(self) -> pd.DataFrame:
        """
        Parse I-V curve measurement data.

        Expected columns: Time, Voltage (V), Current (A), Power (W)

        Returns:
            DataFrame with I-V curve data
        """
        df = self.parse()

        # Validate expected columns
        expected_cols = ['Voltage', 'Current', 'Power']
        missing = set(expected_cols) - set(df.columns)

        if missing:
            raise TimeSeriesError(
                f"I-V curve missing columns: {missing}. "
                f"Expected: {expected_cols}"
            )

        return df

    def parse_chamber_log(self) -> pd.DataFrame:
        """
        Parse environmental chamber log data.

        Expected columns: Time, Temperature, Humidity, Pressure

        Returns:
            DataFrame with chamber log data
        """
        df = self.parse()

        # Common chamber log columns (flexible)
        common_cols = ['Temperature', 'Humidity', 'Pressure']
        found_cols = [col for col in common_cols if col in df.columns]

        if not found_cols:
            raise TimeSeriesError(
                f"No standard chamber columns found. "
                f"Expected at least one of: {common_cols}"
            )

        return df

    def parse_irradiance_data(self) -> pd.DataFrame:
        """
        Parse irradiance sensor data.

        Expected columns: Time, GHI, DHI, DNI

        Returns:
            DataFrame with irradiance data
        """
        df = self.parse()

        # Irradiance columns
        irradiance_cols = ['GHI', 'DHI', 'DNI']
        found_cols = [col for col in irradiance_cols if col in df.columns]

        if not found_cols:
            raise TimeSeriesError(
                f"No irradiance columns found. "
                f"Expected at least one of: {irradiance_cols}"
            )

        return df

    def export_to_csv(
        self,
        output_path: Union[str, Path],
        include_outliers: bool = False,
    ) -> None:
        """
        Export processed time-series data to CSV.

        Args:
            output_path: Output CSV file path
            include_outliers: Include outlier detection columns
        """
        df = self.get_dataframe()

        if include_outliers:
            outliers = self.detect_outliers()
            for col in outliers.columns:
                df[f"{col}_outlier"] = outliers[col]

        df.to_csv(output_path)
