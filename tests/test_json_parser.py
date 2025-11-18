"""Tests for JSON/JSONL parser."""

import json
import tempfile
from pathlib import Path

import pytest

from src.ingestion.json_parser import JSONParser


class TestJSONParser:
    """Test JSON parser functionality."""

    def test_parse_json_dict(self):
        """Test parsing JSON object."""
        parser = JSONParser()

        json_data = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.record_count == 1
            assert result.is_jsonl is False
            assert result.data == json_data
        finally:
            Path(temp_path).unlink()

    def test_parse_json_array(self):
        """Test parsing JSON array."""
        parser = JSONParser()

        json_data = [{"id": 1, "name": "Test1"}, {"id": 2, "name": "Test2"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.record_count == 2
            assert result.is_jsonl is False
            assert result.data == json_data
        finally:
            Path(temp_path).unlink()

    def test_parse_jsonl(self):
        """Test parsing JSON Lines format."""
        parser = JSONParser()

        jsonl_content = '{"id": 1, "value": 100}\n{"id": 2, "value": 200}\n{"id": 3, "value": 300}\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(jsonl_content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.record_count == 3
            assert result.is_jsonl is True
            assert len(result.data) == 3
        finally:
            Path(temp_path).unlink()

    def test_parse_to_dataframe(self):
        """Test converting JSON to DataFrame."""
        parser = JSONParser()

        json_data = [
            {"col1": 1, "col2": "a"},
            {"col1": 2, "col2": "b"},
            {"col1": 3, "col2": "c"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name

        try:
            result = parser.parse(temp_path, to_dataframe=True)

            assert result.dataframe is not None
            assert len(result.dataframe) == 3
            assert list(result.dataframe.columns) == ["col1", "col2"]
        finally:
            Path(temp_path).unlink()

    def test_parse_from_string(self):
        """Test parsing JSON from string."""
        parser = JSONParser()

        json_string = '{"test": "value", "number": 42}'
        result = parser.parse_from_string(json_string)

        assert result.record_count == 1
        assert result.data["test"] == "value"
        assert result.data["number"] == 42

    def test_stream_parse_jsonl(self):
        """Test streaming JSONL parsing."""
        parser = JSONParser()

        jsonl_content = "\n".join(
            [json.dumps({"id": i, "value": i * 10}) for i in range(100)]
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(jsonl_content)
            temp_path = f.name

        try:
            batches = list(parser.stream_parse(temp_path, batch_size=20))

            assert len(batches) == 5  # 100 records / 20 per batch
            assert len(batches[0]) == 20
        finally:
            Path(temp_path).unlink()

    def test_schema_validation(self):
        """Test JSON schema validation."""
        parser = JSONParser(validate_schema=True)

        json_data = {"name": "Test", "age": 25}
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name", "age"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name

        try:
            result = parser.parse(temp_path, schema=schema)

            assert result.schema_valid is True
            assert result.validation_errors is None
        finally:
            Path(temp_path).unlink()
