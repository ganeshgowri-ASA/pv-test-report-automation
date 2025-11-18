"""
Comprehensive Unit Tests for JSON & CSV Data Ingestion Engine

Tests all components:
- CSV parser with auto-detection
- JSON parser with schema validation
- Time-series parser
- Schema validator
- Data transformers
"""

import unittest
import tempfile
import os
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

from csv_parser import CSVIngestion
from json_parser import JSONIngestion
from timeseries_parser import TimeSeriesParser
from schema_validator import SchemaValidator
from data_transformers import DataTransformer
from models import TimeSeriesConfig, TransformationConfig


class TestCSVParser(unittest.TestCase):
    """Test CSV ingestion functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "sample_data"

    def test_parse_iv_curve(self):
        """Test parsing I-V curve CSV."""
        csv_file = self.test_dir / "iv_curve.csv"
        ingestion = CSVIngestion(csv_file)
        result = ingestion.parse()

        self.assertTrue(result.is_valid)
        self.assertEqual(result.row_count, 18)
        self.assertEqual(result.column_count, 5)
        self.assertEqual(result.delimiter_detected, ',')
        self.assertIn('Voltage', result.columns)
        self.assertIn('Current', result.columns)
        self.assertIn('Power', result.columns)

    def test_parse_batch_results(self):
        """Test parsing batch test results CSV."""
        csv_file = self.test_dir / "batch_results.csv"
        ingestion = CSVIngestion(csv_file)
        result = ingestion.parse_batch_results(serial_col="Serial")

        self.assertTrue(result.is_valid)
        self.assertEqual(result.row_count, 10)
        self.assertIn('Serial', result.columns)
        self.assertIn('Pmax', result.columns)

    def test_delimiter_detection_semicolon(self):
        """Test auto-detection of semicolon delimiter."""
        csv_file = self.test_dir / "chamber_log_alternate.csv"
        ingestion = CSVIngestion(csv_file)
        result = ingestion.parse()

        self.assertTrue(result.is_valid)
        self.assertEqual(result.delimiter_detected, ';')

    def test_parse_with_validation(self):
        """Test CSV parsing with validation constraints."""
        csv_file = self.test_dir / "batch_results.csv"
        ingestion = CSVIngestion(csv_file)

        result = ingestion.parse(
            required_columns=['Serial', 'Pmax', 'Voc'],
            numeric_columns=['Pmax', 'Voc', 'Isc'],
            range_checks={'Efficiency': (0, 100)}
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_timeseries_parsing(self):
        """Test time-series specific CSV parsing."""
        csv_file = self.test_dir / "iv_curve.csv"
        ingestion = CSVIngestion(csv_file)

        result = ingestion.parse_timeseries(
            timestamp_col="Time",
            value_cols=["Voltage", "Current", "Power"]
        )

        self.assertTrue(result.is_valid)
        df = ingestion.get_dataframe()
        self.assertTrue(isinstance(df.index, pd.DatetimeIndex))

    def test_file_hash_calculation(self):
        """Test SHA-256 file hash calculation for traceability."""
        csv_file = self.test_dir / "iv_curve.csv"
        ingestion = CSVIngestion(csv_file)
        result = ingestion.parse()

        self.assertTrue(len(result.metadata.file_hash) == 64)  # SHA-256 hex length


class TestJSONParser(unittest.TestCase):
    """Test JSON ingestion functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "sample_data"
        self.schema_dir = Path(__file__).parent / "schemas"

    def test_parse_chamber_log_json(self):
        """Test parsing chamber log JSON."""
        json_file = self.test_dir / "chamber_log.json"
        ingestion = JSONIngestion(json_file)
        result = ingestion.parse()

        self.assertTrue(result.is_valid)
        self.assertEqual(result.record_count, 5)

    def test_parse_jsonl_format(self):
        """Test parsing JSON Lines (.jsonl) format."""
        jsonl_file = self.test_dir / "flash_test.jsonl"
        ingestion = JSONIngestion(jsonl_file)
        result = ingestion.parse()

        self.assertTrue(result.is_valid)
        self.assertEqual(result.record_count, 5)

    def test_schema_validation(self):
        """Test JSON schema validation."""
        json_file = self.test_dir / "chamber_log.json"
        schema_file = self.schema_dir / "chamber_log_schema.json"

        ingestion = JSONIngestion(json_file)
        result = ingestion.parse(schema=schema_file)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.schema_validated)
        self.assertEqual(len(result.schema_errors), 0)

    def test_flatten_json(self):
        """Test JSON structure flattening."""
        json_file = self.test_dir / "chamber_log.json"
        ingestion = JSONIngestion(json_file)
        result = ingestion.parse(flatten=True)

        self.assertTrue(result.is_valid)
        df = ingestion.get_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 5)

    def test_nested_depth_calculation(self):
        """Test nested depth calculation."""
        json_file = self.test_dir / "chamber_log.json"
        ingestion = JSONIngestion(json_file)
        result = ingestion.parse()

        self.assertGreaterEqual(result.nested_depth, 1)

    def test_to_csv_export(self):
        """Test JSON to CSV export."""
        json_file = self.test_dir / "chamber_log.json"
        ingestion = JSONIngestion(json_file)
        ingestion.parse(flatten=True)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name

        try:
            ingestion.to_csv(output_file, index=False)
            self.assertTrue(os.path.exists(output_file))

            # Verify exported CSV
            df = pd.read_csv(output_file)
            self.assertEqual(len(df), 5)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestTimeSeriesParser(unittest.TestCase):
    """Test time-series specific parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "sample_data"

    def test_parse_iv_curve_timeseries(self):
        """Test parsing I-V curve as time-series."""
        csv_file = self.test_dir / "iv_curve.csv"

        config = TimeSeriesConfig(
            timestamp_col="Time",
            value_cols=["Voltage", "Current", "Power"]
        )

        parser = TimeSeriesParser(csv_file, config)
        df = parser.parse()

        self.assertIsInstance(df.index, pd.DatetimeIndex)
        self.assertEqual(len(df), 18)
        self.assertIn("Voltage", df.columns)

    def test_parse_irradiance_data(self):
        """Test parsing irradiance sensor data."""
        csv_file = self.test_dir / "irradiance_data.csv"

        config = TimeSeriesConfig(
            timestamp_col="Time",
            value_cols=["GHI", "DHI", "DNI"]
        )

        parser = TimeSeriesParser(csv_file, config)
        df = parser.parse_irradiance_data()

        self.assertIn("GHI", df.columns)
        self.assertIn("DHI", df.columns)
        self.assertIn("DNI", df.columns)

    def test_resample_timeseries(self):
        """Test time-series resampling."""
        csv_file = self.test_dir / "irradiance_data.csv"

        config = TimeSeriesConfig(
            timestamp_col="Time",
            value_cols=["GHI", "DHI", "DNI"]
        )

        parser = TimeSeriesParser(csv_file, config)
        parser.parse()

        # Resample to 2-hour frequency
        df_resampled = parser.resample('2H', {'GHI': 'mean', 'DHI': 'mean'})

        self.assertLess(len(df_resampled), 13)  # Should be fewer rows

    def test_detect_outliers(self):
        """Test outlier detection in time-series."""
        csv_file = self.test_dir / "iv_curve.csv"

        config = TimeSeriesConfig(
            timestamp_col="Time",
            value_cols=["Voltage", "Current", "Power"]
        )

        parser = TimeSeriesParser(csv_file, config)
        parser.parse()

        outliers = parser.detect_outliers(method='zscore', threshold=3.0)

        self.assertIsInstance(outliers, pd.DataFrame)
        self.assertEqual(len(outliers), 18)

    def test_interpolate_missing(self):
        """Test missing value interpolation."""
        csv_file = self.test_dir / "iv_curve.csv"

        config = TimeSeriesConfig(
            timestamp_col="Time",
            value_cols=["Voltage", "Current", "Power"]
        )

        parser = TimeSeriesParser(csv_file, config)
        df = parser.parse()

        # Artificially introduce missing values
        df_with_nan = df.copy()
        df_with_nan.iloc[5:8, 0] = None

        parser._dataframe = df_with_nan
        df_interpolated = parser.interpolate_missing(method='linear')

        # Check that missing values were filled
        self.assertEqual(df_interpolated.isna().sum().sum(), 0)


class TestSchemaValidator(unittest.TestCase):
    """Test schema validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "sample_data"

    def test_validate_iec61215_data(self):
        """Test IEC 61215 module data validation."""
        validator = SchemaValidator('iec61215_module')

        valid_data = {
            'serial_number': 'PV2025-001',
            'voc': 88.5,
            'isc': 8.95,
            'pmax': 422.3,
            'vmax': 57.4,
            'imax': 7.36,
            'fill_factor': 0.753,
            'efficiency': 19.2,
            'test_date': datetime(2025, 1, 15, 10, 0, 0),
            'test_temperature': 25.0,
            'irradiance': 1000.0
        }

        is_valid, errors = validator.validate_dict(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_dataframe(self):
        """Test DataFrame validation against schema."""
        csv_file = self.test_dir / "batch_results.csv"
        df = pd.read_csv(csv_file)

        # Rename columns to match schema
        df = df.rename(columns={
            'Serial': 'serial_number',
            'Voc': 'voc',
            'Isc': 'isc',
            'Pmax': 'pmax',
            'Vmax': 'vmax',
            'Imax': 'imax',
            'FF': 'fill_factor',
            'Efficiency': 'efficiency',
            'TestDate': 'test_date',
            'Grade': 'grade'
        })

        # Add required fields
        df['test_temperature'] = 25.0
        df['irradiance'] = 1000.0

        validator = SchemaValidator('iec61215_module', strict=False)
        errors = validator.validate_dataframe(df)

        # Should have minimal errors (may have date parsing issues)
        self.assertLess(len(errors), 5)

    def test_list_available_schemas(self):
        """Test listing available schemas."""
        schemas = SchemaValidator.list_schemas()

        self.assertIn('iec61215_module', schemas)
        self.assertIn('iv_curve', schemas)
        self.assertIn('chamber_log', schemas)
        self.assertIn('flash_test', schemas)

    def test_generate_schema_from_dataframe(self):
        """Test auto-generating schema from DataFrame."""
        csv_file = self.test_dir / "batch_results.csv"
        df = pd.read_csv(csv_file)

        schema = SchemaValidator.generate_schema_from_dataframe(
            df,
            schema_name="BatchResultsSchema"
        )

        self.assertIn('properties', schema)
        self.assertIn('required', schema)
        self.assertIn('Serial', schema['properties'])


class TestDataTransformers(unittest.TestCase):
    """Test data transformation utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "sample_data"

        # Load test data
        csv_file = self.test_dir / "batch_results.csv"
        self.df = pd.read_csv(csv_file)

    def test_convert_units(self):
        """Test unit conversion."""
        transformer = DataTransformer(self.df)

        df = transformer.convert_units({
            'Pmax': ('W', 'kW'),
        })

        # Check that values were converted
        self.assertLess(df['Pmax'].max(), 1)  # Should be in kW now

    def test_rename_columns(self):
        """Test column renaming."""
        transformer = DataTransformer(self.df)

        df = transformer.rename_columns({
            'Serial': 'SerialNumber',
            'Pmax': 'MaxPower'
        })

        self.assertIn('SerialNumber', df.columns)
        self.assertIn('MaxPower', df.columns)
        self.assertNotIn('Serial', df.columns)

    def test_filter_rows(self):
        """Test row filtering."""
        transformer = DataTransformer(self.df)

        df = transformer.filter_rows({
            'Efficiency': ('>', 19.0),
            'Grade': 'A'
        })

        # Should only have A-grade modules with efficiency > 19%
        self.assertTrue((df['Grade'] == 'A').all())
        self.assertTrue((df['Efficiency'] > 19.0).all())

    def test_aggregate(self):
        """Test data aggregation."""
        transformer = DataTransformer(self.df)

        df = transformer.aggregate(
            group_by='Grade',
            aggregations={
                'Pmax': ['mean', 'std'],
                'Efficiency': 'mean'
            }
        )

        self.assertIn('Grade', df.columns)
        self.assertGreater(len(df), 0)

    def test_remove_outliers(self):
        """Test outlier removal."""
        transformer = DataTransformer(self.df)

        original_count = len(transformer.df)
        df = transformer.remove_outliers(
            columns=['Pmax'],
            method='zscore',
            threshold=2.0
        )

        # May remove some outliers
        self.assertLessEqual(len(df), original_count)

    def test_calculate_derived_column(self):
        """Test derived column calculation."""
        transformer = DataTransformer(self.df)

        df = transformer.calculate_derived_column(
            'PowerCheck',
            'Vmax * Imax'
        )

        self.assertIn('PowerCheck', df.columns)
        # Should be approximately equal to Pmax
        self.assertTrue(((df['PowerCheck'] - df['Pmax']).abs() < 1).all())

    def test_normalize_column(self):
        """Test column normalization."""
        transformer = DataTransformer(self.df)

        df = transformer.normalize_column('Pmax', method='minmax')

        # Should be scaled to [0, 1]
        self.assertAlmostEqual(df['Pmax'].min(), 0, places=5)
        self.assertAlmostEqual(df['Pmax'].max(), 1, places=5)

    def test_transformation_config(self):
        """Test applying transformation configuration."""
        config = TransformationConfig(
            column_mapping={'Serial': 'SerialNumber'},
            unit_conversions={'Pmax': ('W', 'kW')},
            filter_conditions={'Grade': 'A'}
        )

        transformer = DataTransformer(self.df)
        df = transformer.apply_config(config)

        self.assertIn('SerialNumber', df.columns)
        self.assertTrue((df['Grade'] == 'A').all())


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "sample_data"
        self.schema_dir = Path(__file__).parent / "schemas"

    def test_csv_to_dataframe_pipeline(self):
        """Test complete CSV ingestion and transformation pipeline."""
        # 1. Parse CSV
        csv_file = self.test_dir / "batch_results.csv"
        ingestion = CSVIngestion(csv_file)
        result = ingestion.parse()

        self.assertTrue(result.is_valid)

        # 2. Transform data
        df = ingestion.get_dataframe()
        transformer = DataTransformer(df)
        df = transformer.filter_rows({'Grade': 'A'})
        df = transformer.convert_units({'Pmax': ('W', 'kW')})

        self.assertTrue((df['Grade'] == 'A').all())
        self.assertLess(df['Pmax'].max(), 1)

    def test_json_validation_and_export(self):
        """Test JSON validation and export pipeline."""
        # 1. Parse and validate JSON
        json_file = self.test_dir / "chamber_log.json"
        schema_file = self.schema_dir / "chamber_log_schema.json"

        ingestion = JSONIngestion(json_file)
        result = ingestion.parse(schema=schema_file, flatten=True)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.schema_validated)

        # 2. Export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name

        try:
            ingestion.to_csv(output_file, index=False)
            self.assertTrue(os.path.exists(output_file))
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_timeseries_analysis_pipeline(self):
        """Test complete time-series analysis pipeline."""
        # 1. Parse time-series data
        csv_file = self.test_dir / "irradiance_data.csv"

        config = TimeSeriesConfig(
            timestamp_col="Time",
            value_cols=["GHI", "DHI", "DNI"]
        )

        parser = TimeSeriesParser(csv_file, config)
        df = parser.parse()

        # 2. Detect outliers
        outliers = parser.detect_outliers(method='zscore')

        # 3. Calculate statistics
        stats = parser.calculate_statistics()

        self.assertIsInstance(stats, pd.DataFrame)
        self.assertIn('mean', stats.index)
        self.assertIn('std', stats.index)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
