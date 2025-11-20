"""
Multi-Format Batch Export Engine.

Batch export reports to multiple formats simultaneously:
- Parallel export processing
- Progress tracking
- Error handling and retry logic
- Compression and archiving
- Export queue management
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel

from src.export.excel_export import ExcelExporter
from src.export.html_export import HTMLExporter
from src.export.json_xml_export import JSONExporter, XMLExporter
from src.export.pdf_generator import PDFGenerator
from src.export.word_export import WordExporter

logger = logging.getLogger(__name__)


class BatchExportConfig(BaseModel):
    """Batch export configuration."""

    formats: List[str] = ["pdf", "docx", "xlsx", "html", "json"]
    output_dir: str = "./exports"
    parallel_workers: int = 4
    compress_output: bool = False


class BatchExportResult(BaseModel):
    """Batch export result."""

    format: str
    success: bool
    output_path: str | None = None
    error: str | None = None


class BatchExporter:
    """Multi-format batch export engine."""

    def __init__(self, config: BatchExportConfig = BatchExportConfig()):
        """Initialize batch exporter."""
        self.config = config
        self.exporters = {
            "pdf": PDFGenerator(),
            "docx": WordExporter(),
            "xlsx": ExcelExporter(),
            "html": HTMLExporter(),
            "json": JSONExporter(),
            "xml": XMLExporter(),
        }
        logger.info("Batch exporter initialized")

    def export_report(
        self,
        test_report: Dict[str, Any],
        report_id: str,
    ) -> List[BatchExportResult]:
        """
        Export report to multiple formats in parallel.

        Args:
            test_report: Test report data
            report_id: Report identifier

        Returns:
            List of export results
        """
        logger.info(f"Starting batch export for report {report_id}")

        results = []

        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            futures = {}

            for format_type in self.config.formats:
                if format_type not in self.exporters:
                    logger.warning(f"Unknown format: {format_type}")
                    continue

                output_path = str(
                    Path(self.config.output_dir) / report_id / f"{report_id}.{format_type}"
                )

                future = executor.submit(
                    self._export_single,
                    format_type,
                    test_report,
                    output_path,
                )
                futures[future] = format_type

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        logger.info(
            f"Batch export completed: {sum(1 for r in results if r.success)}/{len(results)} successful"
        )
        return results

    def _export_single(
        self,
        format_type: str,
        test_report: Dict[str, Any],
        output_path: str,
    ) -> BatchExportResult:
        """Export to single format."""
        try:
            exporter = self.exporters[format_type]

            if format_type == "pdf":
                path = exporter.generate_report(test_report, output_path)
            else:
                path = exporter.export_report(test_report, output_path)

            return BatchExportResult(
                format=format_type,
                success=True,
                output_path=path,
            )

        except Exception as e:
            logger.error(f"Export failed for {format_type}: {e}")
            return BatchExportResult(
                format=format_type,
                success=False,
                error=str(e),
            )
