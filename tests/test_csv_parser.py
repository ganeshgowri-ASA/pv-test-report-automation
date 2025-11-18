"""Tests for CSV parser with auto-detection."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.csv_parser import CSVParser


class TestCSVParser:
    """Test CSV parser functionality."""

    def test_detect_delimiter_comma(self):
        """Test comma delimiter detection."""
        parser = CSVParser()

        # Create test CSV with comma delimiter
        csv_content = "col1,col2,col3\n1,2,3\n4,5,6\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            delimiter = parser.detect_delimiter(temp_path, "utf-8")
            assert delimiter == ","
        finally:
            Path(temp_path).unlink()

    def test_detect_delimiter_semicolon(self):
        """Test semicolon delimiter detection."""
        parser = CSVParser()

        csv_content = "col1;col2;col3\n1;2;3\n4;5;6\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            delimiter = parser.detect_delimiter(temp_path, "utf-8")
            assert delimiter == ";"
        finally:
            Path(temp_path).unlink()

    def test_detect_delimiter_tab(self):
        """Test tab delimiter detection."""
        parser = CSVParser()

        csv_content = "col1\tcol2\tcol3\n1\t2\t3\n4\t5\t6\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            delimiter = parser.detect_delimiter(temp_path, "utf-8")
            assert delimiter == "\t"
        finally:
            Path(temp_path).unlink()

    def test_parse_csv_with_header(self):
        """Test parsing CSV with header."""
        parser = CSVParser()

        csv_content = "Name,Value,Unit\nTest1,100,W\nTest2,200,W\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.row_count == 2
            assert result.column_count == 3
            assert result.delimiter_detected == ","
            assert result.has_header is True
            assert list(result.dataframe.columns) == ["Name", "Value", "Unit"]
        finally:
            Path(temp_path).unlink()

    def test_parse_from_string(self):
        """Test parsing CSV from string."""
        parser = CSVParser()

        csv_string = "A,B,C\n1,2,3\n4,5,6\n"
        result = parser.parse_from_string(csv_string)

        assert result.row_count == 2
        assert result.column_count == 3
        assert result.delimiter_detected == ","

    def test_missing_values_detection(self):
        """Test missing value detection."""
        parser = CSVParser()

        csv_content = "A,B,C\n1,2,3\n4,,6\n7,8,\n"
        result = parser.parse_from_string(csv_content)

        assert result.missing_values["B"] == 1
        assert result.missing_values["C"] == 1

    def test_data_types_detection(self):
        """Test data type detection."""
        parser = CSVParser()

        csv_content = "Integer,Float,String\n1,1.5,text\n2,2.5,more\n"
        result = parser.parse_from_string(csv_content)

        assert "Integer" in result.data_types
        assert "Float" in result.data_types
        assert "String" in result.data_types

    def test_file_hash_consistency(self):
        """Test file hash is consistent."""
        parser = CSVParser()

        csv_content = "A,B\n1,2\n3,4\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result1 = parser.parse(temp_path)
            result2 = parser.parse(temp_path)

            assert result1.file_hash == result2.file_hash
        finally:
            Path(temp_path).unlink()
