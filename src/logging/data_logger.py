"""Data logging for test automation"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pythonjsonlogger import jsonlogger
import logging


class TestDataLogger:
    """Logger for test data with multiple output formats"""

    def __init__(
        self,
        test_id: str,
        output_dir: str = "./test_data",
        enable_json_log: bool = True,
        enable_csv_log: bool = True
    ):
        self.test_id = test_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.enable_json_log = enable_json_log
        self.enable_csv_log = enable_csv_log

        # Setup JSON logger
        if self.enable_json_log:
            self.json_logger = self._setup_json_logger()

        # CSV data buffer
        self.csv_data: List[Dict[str, Any]] = []

    def _setup_json_logger(self) -> logging.Logger:
        """Setup JSON structured logger"""
        logger = logging.getLogger(f"test_data_{self.test_id}")
        logger.setLevel(logging.INFO)

        # JSON file handler
        log_file = self.output_dir / f"{self.test_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
        handler = logging.FileHandler(log_file)

        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log_measurement(
        self,
        measurement_type: str,
        value: Any,
        unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a measurement"""
        data = {
            "test_id": self.test_id,
            "measurement_type": measurement_type,
            "value": value,
            "unit": unit,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            data.update(metadata)

        # JSON log
        if self.enable_json_log:
            self.json_logger.info("measurement", extra=data)

        # CSV buffer
        if self.enable_csv_log:
            self.csv_data.append(data)

    def log_event(
        self,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a test event"""
        data = {
            "test_id": self.test_id,
            "event_type": event_type,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            data.update(metadata)

        if self.enable_json_log:
            self.json_logger.info("event", extra=data)

    def save_csv(self, filename: Optional[str] = None) -> Path:
        """Save CSV data to file"""
        if not self.csv_data:
            raise ValueError("No CSV data to save")

        if filename is None:
            filename = f"{self.test_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = self.output_dir / filename

        # Get all unique keys
        fieldnames = set()
        for row in self.csv_data:
            fieldnames.update(row.keys())
        fieldnames = sorted(fieldnames)

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.csv_data)

        return filepath

    def save_json_summary(self, summary_data: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save test summary as JSON"""
        if filename is None:
            filename = f"{self.test_id}_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)

        return filepath
