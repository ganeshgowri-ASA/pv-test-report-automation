"""Equipment data format handler for various PV test equipment."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd

from ..models.ingestion_models import (
    EquipmentData,
    EquipmentType,
    ISO17025Metadata,
)
from .csv_parser import CSVParser
from .json_parser import JSONParser


class EquipmentDataHandler:
    """Handler for equipment-specific data formats."""

    def __init__(self):
        """Initialize equipment data handler."""
        self.csv_parser = CSVParser()
        self.json_parser = JSONParser()

    def parse_iv_tracer_export(
        self,
        file_path: Union[str, Path],
        equipment_id: str,
        manufacturer: str = "Unknown",
        model: str = "Unknown",
        serial_number: str = "Unknown",
        calibration_date: Optional[datetime] = None,
        calibration_due_date: Optional[datetime] = None,
        test_standard: str = "IEC 60904-1",
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> EquipmentData:
        """Parse IV tracer export file.

        Args:
            file_path: Path to export file
            equipment_id: Equipment identifier
            manufacturer: Equipment manufacturer
            model: Equipment model
            serial_number: Serial number
            calibration_date: Last calibration date
            calibration_due_date: Next calibration due date
            test_standard: Test standard
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            EquipmentData object
        """
        file_path = Path(file_path)

        # Try CSV first
        if file_path.suffix.lower() in [".csv", ".txt"]:
            result = self.csv_parser.parse(file_path)
            df = result.dataframe
            raw_format = "csv"
        elif file_path.suffix.lower() == ".json":
            result = self.json_parser.parse(file_path, to_dataframe=True)
            df = result.dataframe if result.dataframe is not None else pd.DataFrame(result.data)
            raw_format = "json"
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Detect measurement units from column names or data
        measurement_units = self._detect_units(df)

        # Use provided dates or defaults
        if calibration_date is None:
            calibration_date = datetime.now()
        if calibration_due_date is None:
            # Default to 1 year from calibration
            calibration_due_date = datetime(
                calibration_date.year + 1,
                calibration_date.month,
                calibration_date.day,
            )

        return EquipmentData(
            equipment_type=EquipmentType.IV_TRACER,
            equipment_id=equipment_id,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            calibration_date=calibration_date,
            calibration_due_date=calibration_due_date,
            measurement_data=df,
            measurement_units=measurement_units,
            measurement_timestamp=datetime.now(),
            test_standard=test_standard,
            raw_data_format=raw_format,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_chamber_export(
        self,
        file_path: Union[str, Path],
        equipment_id: str,
        chamber_type: EquipmentType = EquipmentType.THERMAL_CHAMBER,
        manufacturer: str = "Unknown",
        model: str = "Unknown",
        serial_number: str = "Unknown",
        calibration_date: Optional[datetime] = None,
        calibration_due_date: Optional[datetime] = None,
        test_standard: str = "IEC 61215",
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> EquipmentData:
        """Parse thermal/climatic chamber export file.

        Args:
            file_path: Path to export file
            equipment_id: Equipment identifier
            chamber_type: Type of chamber
            manufacturer: Equipment manufacturer
            model: Equipment model
            serial_number: Serial number
            calibration_date: Last calibration date
            calibration_due_date: Next calibration due date
            test_standard: Test standard
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            EquipmentData object
        """
        file_path = Path(file_path)

        # Parse file
        if file_path.suffix.lower() in [".csv", ".txt"]:
            result = self.csv_parser.parse(file_path)
            df = result.dataframe
            raw_format = "csv"
        elif file_path.suffix.lower() == ".json":
            result = self.json_parser.parse(file_path, to_dataframe=True)
            df = result.dataframe if result.dataframe is not None else pd.DataFrame(result.data)
            raw_format = "json"
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Detect units
        measurement_units = self._detect_units(df)

        # Dates
        if calibration_date is None:
            calibration_date = datetime.now()
        if calibration_due_date is None:
            calibration_due_date = datetime(
                calibration_date.year + 1,
                calibration_date.month,
                calibration_date.day,
            )

        return EquipmentData(
            equipment_type=chamber_type,
            equipment_id=equipment_id,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            calibration_date=calibration_date,
            calibration_due_date=calibration_due_date,
            measurement_data=df,
            measurement_units=measurement_units,
            measurement_timestamp=datetime.now(),
            test_standard=test_standard,
            raw_data_format=raw_format,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_generic_equipment_export(
        self,
        file_path: Union[str, Path],
        equipment_type: EquipmentType,
        equipment_id: str,
        manufacturer: str,
        model: str,
        serial_number: str,
        calibration_date: datetime,
        calibration_due_date: datetime,
        test_standard: str,
        measurement_units: Optional[Dict[str, str]] = None,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> EquipmentData:
        """Parse generic equipment export file.

        Args:
            file_path: Path to export file
            equipment_type: Type of equipment
            equipment_id: Equipment identifier
            manufacturer: Equipment manufacturer
            model: Equipment model
            serial_number: Serial number
            calibration_date: Last calibration date
            calibration_due_date: Next calibration due date
            test_standard: Test standard
            measurement_units: Optional units mapping
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            EquipmentData object
        """
        file_path = Path(file_path)

        # Parse file
        if file_path.suffix.lower() in [".csv", ".txt"]:
            result = self.csv_parser.parse(file_path)
            df = result.dataframe
            raw_format = "csv"
        elif file_path.suffix.lower() == ".json":
            result = self.json_parser.parse(file_path, to_dataframe=True)
            df = result.dataframe if result.dataframe is not None else pd.DataFrame(result.data)
            raw_format = "json"
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
            raw_format = "excel"
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Detect or use provided units
        if measurement_units is None:
            measurement_units = self._detect_units(df)

        return EquipmentData(
            equipment_type=equipment_type,
            equipment_id=equipment_id,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            calibration_date=calibration_date,
            calibration_due_date=calibration_due_date,
            measurement_data=df,
            measurement_units=measurement_units,
            measurement_timestamp=datetime.now(),
            test_standard=test_standard,
            raw_data_format=raw_format,
            iso17025_metadata=iso17025_metadata,
        )

    def _detect_units(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect measurement units from column names.

        Args:
            df: DataFrame with measurement data

        Returns:
            Dictionary mapping column names to units
        """
        units = {}

        # Common unit patterns
        unit_patterns = {
            "voltage": "V",
            "current": "A",
            "power": "W",
            "temperature": "°C",
            "temp": "°C",
            "humidity": "%",
            "pressure": "Pa",
            "irradiance": "W/m²",
            "time": "s",
            "resistance": "Ω",
            "capacitance": "F",
            "frequency": "Hz",
        }

        for col in df.columns:
            col_lower = str(col).lower()

            # Check if unit is in column name (e.g., "Voltage (V)")
            if "(" in col_lower and ")" in col_lower:
                unit = col_lower.split("(")[1].split(")")[0]
                units[col] = unit
            else:
                # Try pattern matching
                for pattern, unit in unit_patterns.items():
                    if pattern in col_lower:
                        units[col] = unit
                        break

                # Default to dimensionless if not found
                if col not in units:
                    units[col] = "-"

        return units

    def export_to_standard_format(
        self,
        equipment_data: EquipmentData,
        output_path: Union[str, Path],
        format: str = "csv",
    ) -> None:
        """Export equipment data to standardized format.

        Args:
            equipment_data: EquipmentData object
            output_path: Output file path
            format: Output format ('csv', 'json', 'excel')
        """
        output_path = Path(output_path)

        if format == "csv":
            equipment_data.measurement_data.to_csv(output_path, index=False)
        elif format == "json":
            equipment_data.measurement_data.to_json(
                output_path, orient="records", indent=2
            )
        elif format == "excel":
            equipment_data.measurement_data.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
