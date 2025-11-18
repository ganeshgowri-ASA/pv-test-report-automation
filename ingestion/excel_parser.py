"""
Main Excel Parser Module

Provides comprehensive Excel data ingestion for PV test data with support for
multiple formats (.xlsx, .xls, .xlsm, .xlsb) and IEC-specific parsing.
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from pydantic import BaseModel, Field

try:
    import xlrd
except ImportError:
    xlrd = None

try:
    from .excel_extractors import ExcelExtractor
    from .excel_transformers import ExcelTransformer
    from .excel_validators import ExcelValidator
except ImportError:
    from excel_extractors import ExcelExtractor
    from excel_transformers import ExcelTransformer
    from excel_validators import ExcelValidator


class ExcelIngestionError(Exception):
    """Base exception for Excel ingestion errors."""
    pass


class FileNotFoundError(ExcelIngestionError):
    """Raised when Excel file is not found."""
    pass


class CorruptedFileError(ExcelIngestionError):
    """Raised when Excel file is corrupted."""
    pass


class InvalidSheetError(ExcelIngestionError):
    """Raised when specified sheet does not exist."""
    pass


class DataValidationError(ExcelIngestionError):
    """Raised when data validation fails."""
    pass


class ExcelIngestionResult(BaseModel):
    """
    Result of Excel data ingestion.

    Attributes:
        dataframe: Extracted and validated data
        metadata: File and extraction metadata
        sheet_count: Number of sheets in workbook
        extraction_timestamp: When the data was extracted
        file_hash: SHA-256 hash for traceability
        warnings: List of non-critical issues
        errors: List of errors encountered
        is_valid: Whether the ingestion was successful
    """
    dataframe: Any = Field(default=None, description="Pandas DataFrame with extracted data")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sheet_count: int = Field(default=0)
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    file_hash: str = Field(default="")
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    is_valid: bool = Field(default=True)

    class Config:
        arbitrary_types_allowed = True


class ExcelIngestion:
    """
    Comprehensive Excel data ingestion engine for PV test data.

    Supports multiple Excel formats, IEC-specific parsing, validation,
    and transformation of test data.

    Example:
        >>> ingestion = ExcelIngestion(file_path="test_data.xlsx")
        >>> result = ingestion.parse_iec61215_mst(
        ...     sheet_name="DampHeat",
        ...     data_range="A10:D210"
        ... )
        >>> if result.is_valid:
        ...     df = result.dataframe
        ...     metadata = result.metadata
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        password: Optional[str] = None
    ):
        """
        Initialize Excel ingestion engine.

        Args:
            file_path: Path to Excel file
            password: Password for protected workbooks (optional)

        Raises:
            FileNotFoundError: If file does not exist
            CorruptedFileError: If file cannot be read
        """
        self.file_path = Path(file_path)
        self.password = password
        self.workbook: Optional[Workbook] = None
        self.extractor = ExcelExtractor()
        self.validator = ExcelValidator()
        self.transformer = ExcelTransformer()

        # Validate file existence
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        # Calculate file hash for traceability
        self.file_hash = self._calculate_file_hash()

        # Load workbook
        self._load_workbook()

    def _calculate_file_hash(self) -> str:
        """
        Calculate SHA-256 hash of the file for ISO 17025 traceability.

        Returns:
            SHA-256 hash as hexadecimal string
        """
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _load_workbook(self) -> None:
        """
        Load Excel workbook based on file extension.

        Raises:
            CorruptedFileError: If file cannot be loaded
        """
        file_ext = self.file_path.suffix.lower()

        try:
            if file_ext in ['.xlsx', '.xlsm', '.xlsb']:
                # Use openpyxl for modern Excel formats
                self.workbook = load_workbook(
                    filename=self.file_path,
                    read_only=False,
                    data_only=True,  # Read formula values, not formulas
                    keep_vba=file_ext == '.xlsm'
                )
            elif file_ext == '.xls':
                # Legacy format - will be handled separately in extraction
                if xlrd is None:
                    raise CorruptedFileError(
                        "xlrd library required for .xls files. "
                        "Install with: pip install xlrd"
                    )
                # Note: xlrd workbooks are handled differently
                self.workbook = None  # Will use pandas with xlrd engine
            else:
                raise CorruptedFileError(
                    f"Unsupported file format: {file_ext}. "
                    f"Supported formats: .xlsx, .xls, .xlsm, .xlsb"
                )
        except Exception as e:
            raise CorruptedFileError(f"Failed to load workbook: {str(e)}")

    def get_sheet_names(self) -> List[str]:
        """
        Get list of sheet names in the workbook.

        Returns:
            List of sheet names
        """
        if self.workbook:
            return self.workbook.sheetnames
        else:
            # For .xls files, use pandas
            try:
                xl_file = pd.ExcelFile(self.file_path, engine='xlrd')
                return xl_file.sheet_names
            except Exception:
                return []

    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract workbook metadata and properties.

        Returns:
            Dictionary containing workbook metadata
        """
        metadata = {
            'file_path': str(self.file_path),
            'file_name': self.file_path.name,
            'file_size_bytes': self.file_path.stat().st_size,
            'file_hash': self.file_hash,
            'file_extension': self.file_path.suffix,
            'sheet_names': self.get_sheet_names(),
            'sheet_count': len(self.get_sheet_names()),
        }

        if self.workbook and hasattr(self.workbook, 'properties'):
            props = self.workbook.properties
            metadata.update({
                'author': props.creator if props.creator else 'Unknown',
                'created': props.created if props.created else None,
                'modified': props.modified if props.modified else None,
                'last_modified_by': props.lastModifiedBy if props.lastModifiedBy else 'Unknown',
                'title': props.title if props.title else '',
                'subject': props.subject if props.subject else '',
                'description': props.description if props.description else '',
            })

        return metadata

    def parse_sheet(
        self,
        sheet_name: str,
        data_range: Optional[str] = None,
        header_row: Optional[int] = 0,
        skip_rows: Optional[List[int]] = None,
        validate: bool = True
    ) -> ExcelIngestionResult:
        """
        Parse a sheet from the workbook.

        Args:
            sheet_name: Name of the sheet to parse
            data_range: Excel range notation (e.g., "A1:D100"), None for entire sheet
            header_row: Row index for column headers (0-indexed)
            skip_rows: List of row indices to skip
            validate: Whether to perform validation

        Returns:
            ExcelIngestionResult with parsed data
        """
        result = ExcelIngestionResult(
            metadata=self.extract_metadata(),
            file_hash=self.file_hash,
            sheet_count=len(self.get_sheet_names())
        )

        # Validate sheet exists (raise exception immediately for invalid sheet)
        if sheet_name not in self.get_sheet_names():
            raise InvalidSheetError(f"Sheet '{sheet_name}' not found")

        try:
            # Extract data
            if data_range:
                df = self.extractor.extract_range(
                    self.workbook,
                    sheet_name,
                    data_range,
                    header_row
                )
            else:
                # Read entire sheet
                df = pd.read_excel(
                    self.file_path,
                    sheet_name=sheet_name,
                    header=header_row,
                    skiprows=skip_rows
                )

            # Validate data if requested
            if validate:
                validation_result = self.validator.validate_dataframe(df)
                result.warnings.extend(validation_result.get('warnings', []))
                result.errors.extend(validation_result.get('errors', []))

                if validation_result.get('errors'):
                    result.is_valid = False

            result.dataframe = df
            result.metadata['rows'] = len(df)
            result.metadata['columns'] = len(df.columns)
            result.metadata['sheet_name'] = sheet_name

        except (InvalidSheetError, FileNotFoundError, CorruptedFileError):
            # Re-raise critical errors
            raise
        except Exception as e:
            # Catch other errors and add to result
            result.errors.append(str(e))
            result.is_valid = False

        return result

    def parse_iec61215_mst(
        self,
        sheet_name: str = "DampHeat",
        data_range: Optional[str] = None,
        time_column: str = "Time (h)",
        temp_column: str = "Temperature (°C)",
        humidity_column: str = "Humidity (%RH)"
    ) -> ExcelIngestionResult:
        """
        Parse IEC 61215 Module Stability Test (MST) damp heat cycle data.

        Expected columns:
        - Time (h): Test duration in hours
        - Temperature (°C): Chamber temperature
        - Humidity (%RH): Relative humidity
        - Optional: Additional sensor readings

        Args:
            sheet_name: Sheet containing MST data
            data_range: Excel range notation (e.g., "A10:D210")
            time_column: Name of time column
            temp_column: Name of temperature column
            humidity_column: Name of humidity column

        Returns:
            ExcelIngestionResult with MST data
        """
        result = self.parse_sheet(sheet_name, data_range)

        if not result.is_valid:
            return result

        df = result.dataframe

        # Validate required columns
        required_columns = [time_column, temp_column, humidity_column]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            result.errors.append(
                f"Missing required columns for IEC 61215 MST: {missing_columns}"
            )
            result.is_valid = False
            return result

        # Validate data types
        try:
            df[time_column] = pd.to_numeric(df[time_column], errors='coerce')
            df[temp_column] = pd.to_numeric(df[temp_column], errors='coerce')
            df[humidity_column] = pd.to_numeric(df[humidity_column], errors='coerce')
        except Exception as e:
            result.errors.append(f"Data type conversion error: {str(e)}")
            result.is_valid = False
            return result

        # Check for missing values
        missing_data = df[required_columns].isnull().sum()
        if missing_data.any():
            result.warnings.append(
                f"Missing values detected: {missing_data[missing_data > 0].to_dict()}"
            )

        # Validate test conditions (IEC 61215: 85°C, 85% RH)
        temp_range = (83, 87)  # Allow ±2°C tolerance
        humidity_range = (83, 87)  # Allow ±2% tolerance

        temp_out_of_range = (
            (df[temp_column] < temp_range[0]) |
            (df[temp_column] > temp_range[1])
        ).sum()

        humidity_out_of_range = (
            (df[humidity_column] < humidity_range[0]) |
            (df[humidity_column] > humidity_range[1])
        ).sum()

        if temp_out_of_range > 0:
            result.warnings.append(
                f"{temp_out_of_range} temperature readings outside "
                f"IEC 61215 specification ({temp_range[0]}-{temp_range[1]}°C)"
            )

        if humidity_out_of_range > 0:
            result.warnings.append(
                f"{humidity_out_of_range} humidity readings outside "
                f"IEC 61215 specification ({humidity_range[0]}-{humidity_range[1]}%RH)"
            )

        result.dataframe = df
        result.metadata['test_type'] = 'IEC 61215 MST Damp Heat'
        result.metadata['test_duration_hours'] = df[time_column].max()
        result.metadata['avg_temperature'] = df[temp_column].mean()
        result.metadata['avg_humidity'] = df[humidity_column].mean()

        return result

    def parse_iec61730_impact(
        self,
        sheet_name: str = "ImpactTest",
        data_range: Optional[str] = None
    ) -> ExcelIngestionResult:
        """
        Parse IEC 61730 mechanical impact test (ball drop test) results.

        Expected columns:
        - Test No.: Test number/identifier
        - Drop Height (mm): Height from which ball is dropped
        - Ball Mass (g): Mass of the impactor
        - Impact Location: Location on module
        - Result: Pass/Fail
        - Notes: Additional observations

        Args:
            sheet_name: Sheet containing impact test data
            data_range: Excel range notation

        Returns:
            ExcelIngestionResult with impact test data
        """
        result = self.parse_sheet(sheet_name, data_range)

        if not result.is_valid:
            return result

        df = result.dataframe

        # Flexible column matching
        test_no_col = self._find_column(df, ['Test No', 'Test No.', 'Test Number', 'ID'])
        height_col = self._find_column(df, ['Drop Height', 'Height (mm)', 'Height'])
        mass_col = self._find_column(df, ['Ball Mass', 'Mass (g)', 'Mass'])
        result_col = self._find_column(df, ['Result', 'Pass/Fail', 'Status'])

        if not all([test_no_col, height_col, mass_col, result_col]):
            result.errors.append(
                "Missing required columns for IEC 61730 impact test"
            )
            result.is_valid = False
            return result

        # Validate IEC 61730 specifications (227g ball, 1270mm height)
        expected_mass = 227  # grams
        expected_height = 1270  # mm

        mass_variance = df[mass_col].std()
        height_variance = df[height_col].std()

        if mass_variance > 5:  # More than 5g variance
            result.warnings.append(
                f"Ball mass variance exceeds tolerance: {mass_variance:.2f}g"
            )

        if height_variance > 50:  # More than 50mm variance
            result.warnings.append(
                f"Drop height variance exceeds tolerance: {height_variance:.2f}mm"
            )

        result.dataframe = df
        result.metadata['test_type'] = 'IEC 61730 Mechanical Impact'
        result.metadata['total_tests'] = len(df)
        result.metadata['pass_count'] = (df[result_col].str.upper() == 'PASS').sum()
        result.metadata['fail_count'] = (df[result_col].str.upper() == 'FAIL').sum()

        return result

    def parse_iec62716_ammonia(
        self,
        sheet_name: str = "AmmoniaExposure",
        data_range: Optional[str] = None
    ) -> ExcelIngestionResult:
        """
        Parse IEC 62716 ammonia corrosion test chamber concentration logs.

        Expected columns:
        - Time (h): Exposure duration
        - NH3 Concentration (ppm): Ammonia concentration
        - Temperature (°C): Chamber temperature
        - Humidity (%RH): Relative humidity

        Args:
            sheet_name: Sheet containing ammonia test data
            data_range: Excel range notation

        Returns:
            ExcelIngestionResult with ammonia test data
        """
        result = self.parse_sheet(sheet_name, data_range)

        if not result.is_valid:
            return result

        df = result.dataframe

        # Find columns
        time_col = self._find_column(df, ['Time', 'Time (h)', 'Duration'])
        nh3_col = self._find_column(df, ['NH3', 'Ammonia', 'Concentration', 'NH3 Concentration'])
        temp_col = self._find_column(df, ['Temperature', 'Temp', 'T (°C)'])
        humidity_col = self._find_column(df, ['Humidity', 'RH', '%RH'])

        if not all([time_col, nh3_col]):
            result.errors.append(
                "Missing required columns for IEC 62716 ammonia test"
            )
            result.is_valid = False
            return result

        # IEC 62716 specifications: 20-40 ppm NH3
        nh3_range = (20, 40)
        nh3_out_of_range = (
            (df[nh3_col] < nh3_range[0]) |
            (df[nh3_col] > nh3_range[1])
        ).sum()

        if nh3_out_of_range > 0:
            result.warnings.append(
                f"{nh3_out_of_range} NH3 concentration readings outside "
                f"IEC 62716 specification ({nh3_range[0]}-{nh3_range[1]} ppm)"
            )

        result.dataframe = df
        result.metadata['test_type'] = 'IEC 62716 Ammonia Corrosion'
        result.metadata['test_duration_hours'] = df[time_col].max()
        result.metadata['avg_nh3_concentration'] = df[nh3_col].mean()

        return result

    def parse_iec61701_salt_mist(
        self,
        sheet_name: str = "SaltMist",
        data_range: Optional[str] = None
    ) -> ExcelIngestionResult:
        """
        Parse IEC 61701 salt mist corrosion test data (mass loss and visual inspection).

        Expected columns:
        - Sample ID: Module/sample identifier
        - Initial Mass (g): Pre-test mass
        - Final Mass (g): Post-test mass
        - Mass Loss (g): Mass loss due to corrosion
        - Visual Inspection: Pass/Fail/Observations
        - Severity Level: 1-6 per IEC 61701

        Args:
            sheet_name: Sheet containing salt mist test data
            data_range: Excel range notation

        Returns:
            ExcelIngestionResult with salt mist test data
        """
        result = self.parse_sheet(sheet_name, data_range)

        if not result.is_valid:
            return result

        df = result.dataframe

        # Find columns
        sample_col = self._find_column(df, ['Sample', 'Sample ID', 'Module ID'])
        initial_mass_col = self._find_column(df, ['Initial Mass', 'Mass Before', 'Pre-test Mass'])
        final_mass_col = self._find_column(df, ['Final Mass', 'Mass After', 'Post-test Mass'])
        mass_loss_col = self._find_column(df, ['Mass Loss', 'Loss', 'Delta Mass'])

        if not sample_col:
            result.errors.append(
                "Missing sample ID column for IEC 61701 salt mist test"
            )
            result.is_valid = False
            return result

        # Calculate mass loss if not provided
        if not mass_loss_col and initial_mass_col and final_mass_col:
            df['Mass Loss (g)'] = df[initial_mass_col] - df[final_mass_col]
            mass_loss_col = 'Mass Loss (g)'
            result.warnings.append("Mass loss calculated from initial and final mass")

        if mass_loss_col:
            # Check for significant mass loss
            significant_loss_threshold = 1.0  # grams
            significant_loss_count = (df[mass_loss_col] > significant_loss_threshold).sum()

            if significant_loss_count > 0:
                result.warnings.append(
                    f"{significant_loss_count} samples with mass loss > {significant_loss_threshold}g"
                )

            result.metadata['avg_mass_loss'] = df[mass_loss_col].mean()
            result.metadata['max_mass_loss'] = df[mass_loss_col].max()

        result.dataframe = df
        result.metadata['test_type'] = 'IEC 61701 Salt Mist Corrosion'
        result.metadata['total_samples'] = len(df)

        return result

    def parse_iv_curve(
        self,
        sheet_name: str = "IV_Curve",
        data_range: Optional[str] = None,
        voltage_column: str = "Voltage (V)",
        current_column: str = "Current (A)",
        power_column: Optional[str] = "Power (W)"
    ) -> ExcelIngestionResult:
        """
        Parse I-V curve raw data (voltage, current, power measurements).

        Expected columns:
        - Voltage (V): Voltage measurements
        - Current (A): Current measurements
        - Power (W): Power measurements (optional, will be calculated if missing)

        Metadata expected in header rows:
        - Module Serial: Module identifier
        - Test Date: Date of measurement
        - Irradiance: Light intensity (W/m²)
        - Temperature: Module temperature (°C)

        Args:
            sheet_name: Sheet containing I-V curve data
            data_range: Excel range notation
            voltage_column: Name of voltage column
            current_column: Name of current column
            power_column: Name of power column (optional)

        Returns:
            ExcelIngestionResult with I-V curve data
        """
        # First extract metadata from header
        metadata_result = self.extractor.extract_key_value_pairs(
            self.workbook,
            sheet_name,
            search_range="A1:B10"
        )

        # Then extract I-V data
        result = self.parse_sheet(sheet_name, data_range)

        if not result.is_valid:
            return result

        df = result.dataframe

        # Validate required columns
        if voltage_column not in df.columns or current_column not in df.columns:
            result.errors.append(
                f"Missing required columns: {voltage_column}, {current_column}"
            )
            result.is_valid = False
            return result

        # Convert to numeric
        df[voltage_column] = pd.to_numeric(df[voltage_column], errors='coerce')
        df[current_column] = pd.to_numeric(df[current_column], errors='coerce')

        # Calculate power if not provided
        if power_column and power_column in df.columns:
            df[power_column] = pd.to_numeric(df[power_column], errors='coerce')
        else:
            df['Power (W)'] = df[voltage_column] * df[current_column]
            power_column = 'Power (W)'
            result.warnings.append("Power calculated from voltage and current")

        # Extract characteristic points
        max_power_idx = df[power_column].idxmax()
        vmp = df.loc[max_power_idx, voltage_column]
        imp = df.loc[max_power_idx, current_column]
        pmax = df.loc[max_power_idx, power_column]

        # Voc: voltage at zero current
        voc_idx = (df[current_column] - 0).abs().idxmin()
        voc = df.loc[voc_idx, voltage_column]

        # Isc: current at zero voltage
        isc_idx = (df[voltage_column] - 0).abs().idxmin()
        isc = df.loc[isc_idx, current_column]

        # Calculate fill factor
        fill_factor = pmax / (voc * isc) if (voc * isc) > 0 else 0

        result.dataframe = df
        result.metadata['test_type'] = 'I-V Curve Measurement'
        result.metadata.update(metadata_result)
        result.metadata.update({
            'voc': float(voc),
            'isc': float(isc),
            'vmp': float(vmp),
            'imp': float(imp),
            'pmax': float(pmax),
            'fill_factor': float(fill_factor),
            'data_points': len(df)
        })

        return result

    def parse_key_value_metadata(
        self,
        sheet_name: str,
        search_range: str = "A1:B20"
    ) -> Dict[str, Any]:
        """
        Extract key-value pairs from equipment specs or metadata sections.

        Searches for patterns like:
        - Equipment ID: XYZ-123
        - Test Date: 2024-01-15
        - Operator: John Doe

        Args:
            sheet_name: Sheet containing metadata
            search_range: Range to search for key-value pairs

        Returns:
            Dictionary of extracted metadata
        """
        return self.extractor.extract_key_value_pairs(
            self.workbook,
            sheet_name,
            search_range
        )

    def _find_column(
        self,
        df: pd.DataFrame,
        possible_names: List[str]
    ) -> Optional[str]:
        """
        Find column in DataFrame by checking multiple possible names.

        Args:
            df: DataFrame to search
            possible_names: List of possible column names

        Returns:
            Actual column name if found, None otherwise
        """
        for name in possible_names:
            # Case-insensitive partial match
            matching_cols = [
                col for col in df.columns
                if name.lower() in str(col).lower()
            ]
            if matching_cols:
                return matching_cols[0]
        return None

    def close(self) -> None:
        """Close the workbook and release resources."""
        if self.workbook:
            self.workbook.close()
