"""Batch test results import handler."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from ..models.ingestion_models import BatchTestResult, ISO17025Metadata
from .csv_parser import CSVParser
from .json_parser import JSONParser


class BatchTestHandler:
    """Handler for batch test results import."""

    def __init__(self):
        """Initialize batch test handler."""
        self.csv_parser = CSVParser()
        self.json_parser = JSONParser()

    def parse_batch_csv(
        self,
        file_path: Union[str, Path],
        batch_id: str,
        test_standard: str,
        module_id_col: str = "Module_ID",
        result_col: str = "Result",
        test_date: Optional[datetime] = None,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> BatchTestResult:
        """Parse batch test results from CSV.

        Args:
            file_path: Path to CSV file
            batch_id: Batch identifier
            test_standard: Test standard applied
            module_id_col: Column name for module IDs
            result_col: Column name for pass/fail results
            test_date: Test execution date
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            BatchTestResult object
        """
        # Parse CSV
        result = self.csv_parser.parse(file_path)
        df = result.dataframe

        # Validate required columns
        if module_id_col not in df.columns:
            raise ValueError(f"Module ID column '{module_id_col}' not found")

        # Extract module IDs
        module_ids = df[module_id_col].astype(str).tolist()

        # Count pass/fail if result column exists
        pass_count = 0
        fail_count = 0

        if result_col in df.columns:
            # Normalize result values
            results_normalized = df[result_col].astype(str).str.lower()

            pass_count = results_normalized.isin(["pass", "passed", "ok", "1", "true"]).sum()
            fail_count = results_normalized.isin(["fail", "failed", "ng", "0", "false"]).sum()

        total_count = len(module_ids)

        # If no explicit pass/fail, assume all passed (or adjust logic as needed)
        if pass_count == 0 and fail_count == 0:
            pass_count = total_count

        # Calculate summary statistics
        summary_statistics = self._calculate_summary_statistics(df)

        # Extract test parameters
        test_parameters = self._extract_test_parameters(df)

        # Use provided test date or current time
        if test_date is None:
            test_date = datetime.now()

        return BatchTestResult(
            batch_id=batch_id,
            test_date=test_date,
            module_ids=module_ids,
            test_results=df,
            pass_count=int(pass_count),
            fail_count=int(fail_count),
            total_count=total_count,
            test_standard=test_standard,
            test_parameters=test_parameters,
            summary_statistics=summary_statistics,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_batch_json(
        self,
        file_path: Union[str, Path],
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> BatchTestResult:
        """Parse batch test results from JSON.

        Args:
            file_path: Path to JSON file
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            BatchTestResult object
        """
        # Parse JSON
        result = self.json_parser.parse(file_path, to_dataframe=True)
        data = result.data

        if not isinstance(data, dict):
            raise ValueError("JSON must contain a batch test object")

        # Extract metadata
        batch_id = data.get("batch_id", "unknown")
        test_standard = data.get("test_standard", "Unknown")

        # Parse test date
        test_date_str = data.get("test_date")
        test_date = (
            datetime.fromisoformat(test_date_str)
            if test_date_str
            else datetime.now()
        )

        # Extract module results
        results_data = data.get("results", [])
        if not results_data:
            raise ValueError("No test results found in JSON")

        # Convert to DataFrame
        df = pd.DataFrame(results_data)

        # Extract module IDs
        if "module_id" in df.columns:
            module_ids = df["module_id"].astype(str).tolist()
        elif "Module_ID" in df.columns:
            module_ids = df["Module_ID"].astype(str).tolist()
        else:
            # Generate module IDs
            module_ids = [f"Module_{i}" for i in range(len(df))]

        # Count pass/fail
        pass_count = data.get("pass_count", 0)
        fail_count = data.get("fail_count", 0)
        total_count = data.get("total_count", len(module_ids))

        # If counts not provided, calculate from results
        if pass_count == 0 and fail_count == 0 and "result" in df.columns:
            results_normalized = df["result"].astype(str).str.lower()
            pass_count = int(
                results_normalized.isin(["pass", "passed", "ok", "1", "true"]).sum()
            )
            fail_count = int(
                results_normalized.isin(["fail", "failed", "ng", "0", "false"]).sum()
            )

        # Calculate statistics
        summary_statistics = data.get(
            "summary_statistics", self._calculate_summary_statistics(df)
        )

        # Test parameters
        test_parameters = data.get("test_parameters", {})

        return BatchTestResult(
            batch_id=batch_id,
            test_date=test_date,
            module_ids=module_ids,
            test_results=df,
            pass_count=pass_count,
            fail_count=fail_count,
            total_count=total_count,
            test_standard=test_standard,
            test_parameters=test_parameters,
            summary_statistics=summary_statistics,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_batch_jsonl(
        self,
        file_path: Union[str, Path],
        batch_id: str,
        test_standard: str,
        test_date: Optional[datetime] = None,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> BatchTestResult:
        """Parse batch test results from JSONL (one test result per line).

        Args:
            file_path: Path to JSONL file
            batch_id: Batch identifier
            test_standard: Test standard
            test_date: Test execution date
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            BatchTestResult object
        """
        # Parse JSONL
        result = self.json_parser.parse(file_path, to_dataframe=True)

        if result.dataframe is None:
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(result.data)
        else:
            df = result.dataframe

        # Extract module IDs
        if "module_id" in df.columns:
            module_ids = df["module_id"].astype(str).tolist()
        else:
            module_ids = [f"Module_{i}" for i in range(len(df))]

        # Count pass/fail
        pass_count = 0
        fail_count = 0

        if "result" in df.columns:
            results_normalized = df["result"].astype(str).str.lower()
            pass_count = int(
                results_normalized.isin(["pass", "passed", "ok", "1", "true"]).sum()
            )
            fail_count = int(
                results_normalized.isin(["fail", "failed", "ng", "0", "false"]).sum()
            )

        total_count = len(module_ids)

        # Calculate statistics
        summary_statistics = self._calculate_summary_statistics(df)

        # Test parameters
        test_parameters = self._extract_test_parameters(df)

        # Use provided test date or current time
        if test_date is None:
            test_date = datetime.now()

        return BatchTestResult(
            batch_id=batch_id,
            test_date=test_date,
            module_ids=module_ids,
            test_results=df,
            pass_count=pass_count,
            fail_count=fail_count,
            total_count=total_count,
            test_standard=test_standard,
            test_parameters=test_parameters,
            summary_statistics=summary_statistics,
            iso17025_metadata=iso17025_metadata,
        )

    def _calculate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate summary statistics for numeric columns.

        Args:
            df: Test results DataFrame

        Returns:
            Dictionary of statistics
        """
        stats = {}

        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            col_data = df[col].dropna()

            if len(col_data) > 0:
                stats[f"{col}_mean"] = float(col_data.mean())
                stats[f"{col}_std"] = float(col_data.std())
                stats[f"{col}_min"] = float(col_data.min())
                stats[f"{col}_max"] = float(col_data.max())
                stats[f"{col}_median"] = float(col_data.median())

        return stats

    def _extract_test_parameters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract test parameters from DataFrame.

        Args:
            df: Test results DataFrame

        Returns:
            Dictionary of test parameters
        """
        params = {}

        # Look for common parameter columns
        param_columns = [
            "irradiance",
            "temperature",
            "humidity",
            "test_temperature",
            "test_voltage",
            "test_current",
        ]

        for col in param_columns:
            if col in df.columns:
                # If all values are same, it's a test parameter
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 1:
                    params[col] = float(unique_vals[0]) if isinstance(unique_vals[0], (int, float)) else str(unique_vals[0])

        return params

    def merge_batches(
        self, batches: List[BatchTestResult], merged_batch_id: str
    ) -> BatchTestResult:
        """Merge multiple batch test results.

        Args:
            batches: List of BatchTestResult objects
            merged_batch_id: ID for merged batch

        Returns:
            Merged BatchTestResult
        """
        if not batches:
            raise ValueError("No batches to merge")

        # Concatenate all DataFrames
        all_dfs = [batch.test_results for batch in batches]
        merged_df = pd.concat(all_dfs, ignore_index=True)

        # Merge module IDs
        all_module_ids = []
        for batch in batches:
            all_module_ids.extend(batch.module_ids)

        # Sum counts
        total_pass = sum(batch.pass_count for batch in batches)
        total_fail = sum(batch.fail_count for batch in batches)
        total_count = sum(batch.total_count for batch in batches)

        # Use most recent test date
        most_recent_date = max(batch.test_date for batch in batches)

        # Use first test standard (assuming all same)
        test_standard = batches[0].test_standard

        # Recalculate statistics
        summary_statistics = self._calculate_summary_statistics(merged_df)

        # Merge test parameters
        merged_params = {}
        for batch in batches:
            merged_params.update(batch.test_parameters)

        return BatchTestResult(
            batch_id=merged_batch_id,
            test_date=most_recent_date,
            module_ids=all_module_ids,
            test_results=merged_df,
            pass_count=total_pass,
            fail_count=total_fail,
            total_count=total_count,
            test_standard=test_standard,
            test_parameters=merged_params,
            summary_statistics=summary_statistics,
        )

    def export_batch_report(
        self,
        batch_result: BatchTestResult,
        output_path: Union[str, Path],
        format: str = "csv",
    ) -> None:
        """Export batch test results to file.

        Args:
            batch_result: BatchTestResult object
            output_path: Output file path
            format: Output format ('csv', 'json', 'excel')
        """
        output_path = Path(output_path)

        if format == "csv":
            batch_result.test_results.to_csv(output_path, index=False)
        elif format == "json":
            export_data = {
                "batch_id": batch_result.batch_id,
                "test_date": batch_result.test_date.isoformat(),
                "test_standard": batch_result.test_standard,
                "pass_count": batch_result.pass_count,
                "fail_count": batch_result.fail_count,
                "total_count": batch_result.total_count,
                "test_parameters": batch_result.test_parameters,
                "summary_statistics": batch_result.summary_statistics,
                "results": batch_result.test_results.to_dict(orient="records"),
            }

            import json

            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)

        elif format == "excel":
            batch_result.test_results.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
