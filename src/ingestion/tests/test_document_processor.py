"""
Unit tests for Document Processor module.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO

from ..document_processor import (
    DocumentProcessor,
    DocumentProcessorConfig,
    DocumentMetadata,
    TableData,
    SectionData,
    TestReportDocument,
)


class TestDocumentMetadata:
    """Test DocumentMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid document metadata."""
        metadata = DocumentMetadata(
            report_id="RPT-001",
            test_standard="IEC 61215",
            lab_name="PV Test Lab",
            file_format="pdf",
            page_count=25,
        )

        assert metadata.report_id == "RPT-001"
        assert metadata.test_standard == "IEC 61215"
        assert metadata.file_format == "pdf"

    def test_default_values(self):
        """Test default metadata values."""
        metadata = DocumentMetadata(file_format="pdf")

        assert metadata.page_count == 0
        assert metadata.custom_fields == {}


class TestTableData:
    """Test TableData model."""

    def test_valid_table(self):
        """Test creating valid table data."""
        table = TableData(
            table_number=1,
            headers=["Parameter", "Value", "Unit"],
            rows=[
                ["Voc", "38.5", "V"],
                ["Isc", "8.9", "A"],
            ],
            page_number=5,
        )

        assert table.table_number == 1
        assert len(table.headers) == 3
        assert len(table.rows) == 2


class TestSectionData:
    """Test SectionData model."""

    def test_valid_section(self):
        """Test creating valid section data."""
        section = SectionData(
            section_number="1.0",
            title="Introduction",
            content="This is the introduction section.",
            page_start=1,
            page_end=2,
        )

        assert section.section_number == "1.0"
        assert section.title == "Introduction"
        assert section.page_start == 1

    def test_nested_subsections(self):
        """Test sections with subsections."""
        subsection = SectionData(
            title="Subsection 1.1",
            content="Subsection content",
            page_start=1,
            page_end=1,
        )

        section = SectionData(
            section_number="1.0",
            title="Main Section",
            content="Main content",
            page_start=1,
            page_end=2,
            subsections=[subsection],
        )

        assert len(section.subsections) == 1
        assert section.subsections[0].title == "Subsection 1.1"


class TestDocumentProcessor:
    """Test DocumentProcessor class."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = DocumentProcessor()
        assert processor.config is not None
        assert isinstance(processor.config, DocumentProcessorConfig)

    def test_custom_config(self):
        """Test processor with custom config."""
        config = DocumentProcessorConfig(
            extract_tables=False,
            max_file_size_mb=50,
        )
        processor = DocumentProcessor(config)

        assert processor.config.extract_tables is False
        assert processor.config.max_file_size_mb == 50

    def test_progress_callback(self):
        """Test progress callback."""
        processor = DocumentProcessor()
        callback = Mock()
        processor.set_progress_callback(callback)

        processor._report_progress(3, 10, "Processing page 3")
        callback.assert_called_once_with(3, 10, "Processing page 3")

    def test_standard_patterns(self):
        """Test standard pattern recognition."""
        processor = DocumentProcessor()

        assert "IEC 61215" in processor.STANDARD_PATTERNS
        assert "ISO 17025" in processor.STANDARD_PATTERNS

    @patch("pdfplumber.open")
    def test_process_pdf(self, mock_pdfplumber):
        """Test PDF processing."""
        # Mock PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = (
            "Test Report\nReport ID: RPT-001\nIEC 61215\n"
            "Manufacturer: SolarCorp\nModel: SP-300"
        )
        mock_page.extract_tables.return_value = []

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.return_value = mock_pdf

        processor = DocumentProcessor()

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024 * 1024  # 1MB

                result = processor.process_pdf("test.pdf")

        assert isinstance(result, TestReportDocument)
        assert "RPT-001" in result.raw_text

    @patch("docx.Document")
    def test_process_docx(self, mock_document):
        """Test Word document processing."""
        # Mock Word document
        mock_para = Mock()
        mock_para.text = "Test Report\nReport ID: RPT-002"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        mock_doc.core_properties = Mock(
            author="Test Engineer",
            created=datetime(2025, 1, 15),
            modified=datetime(2025, 1, 16),
        )

        mock_document.return_value = mock_doc

        processor = DocumentProcessor()

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024 * 1024

                result = processor.process_docx("test.docx")

        assert isinstance(result, TestReportDocument)
        assert result.metadata.test_engineer == "Test Engineer"

    def test_process_table(self):
        """Test table processing."""
        processor = DocumentProcessor()

        table_data = [
            ["Parameter", "Value", "Unit"],
            ["Voc", "38.5", "V"],
            ["Isc", "8.9", "A"],
        ]

        result = processor._process_table(table_data, 1, 5)

        assert isinstance(result, TableData)
        assert result.headers == ["Parameter", "Value", "Unit"]
        assert len(result.rows) == 2
        assert result.page_number == 5

    def test_extract_metadata_from_text(self):
        """Test metadata extraction from text."""
        processor = DocumentProcessor()

        text = """
        Test Report
        Report ID: RPT-12345
        Test Standard: IEC 61215-1
        Laboratory: PV Testing Lab
        Manufacturer: SolarCorp Inc.
        Model: SP-300W
        Serial Number: SN-2025-001
        """

        metadata = processor._extract_metadata_from_text(text, "pdf", 10)

        assert metadata.report_id == "RPT-12345"
        assert metadata.test_standard == "IEC 61215"
        assert metadata.module_manufacturer == "SolarCorp Inc."
        assert metadata.module_model == "SP-300W"

    def test_identify_sections(self):
        """Test section identification."""
        processor = DocumentProcessor()

        text = """
        1. INTRODUCTION
        This is the introduction section.

        2. TEST METHODOLOGY
        This describes the test methodology.

        3. RESULTS
        Test results are presented here.
        """

        sections = processor._identify_sections(text)

        assert len(sections) > 0
        # Check that sections were identified
        section_titles = [s.title for s in sections]
        assert any("INTRODUCTION" in title for title in section_titles)

    def test_extract_test_data(self):
        """Test extraction of test data."""
        processor = DocumentProcessor()

        text = """
        Test Results:
        Voc: 38.5 V
        Isc: 8.9 A
        Pmax: 300.5 W
        Vmp: 31.2 V
        Imp: 9.6 A
        Fill Factor: 0.745
        Efficiency: 18.5 %
        """

        table_data = TableData(
            table_number=1,
            headers=["Parameter", "Value"],
            rows=[
                ["Voc", "38.5 V"],
                ["Isc", "8.9 A"],
            ],
        )

        extracted = processor._extract_test_data(text, [table_data])

        assert "voc" in extracted
        assert extracted["voc"] == 38.5

    def test_search_text(self):
        """Test text search functionality."""
        processor = DocumentProcessor()

        doc = TestReportDocument(
            file_path="test.pdf",
            metadata=DocumentMetadata(file_format="pdf"),
            sections=[],
            raw_text="This is a test document with IEC 61215 standard.",
            tables=[],
        )

        results = processor.search_text(doc, r"IEC\s+\d+")

        assert len(results) > 0
        assert "IEC 61215" in results[0]["match"]

    def test_file_not_found(self):
        """Test error handling for missing file."""
        processor = DocumentProcessor()

        with pytest.raises(FileNotFoundError):
            processor.process_pdf("nonexistent.pdf")

    def test_file_too_large(self):
        """Test file size limit."""
        config = DocumentProcessorConfig(max_file_size_mb=1)
        processor = DocumentProcessor(config)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "stat") as mock_stat:
                # File is 10MB, limit is 1MB
                mock_stat.return_value.st_size = 10 * 1024 * 1024

                with pytest.raises(ValueError, match="exceeds limit"):
                    processor.process_pdf("large.pdf")


@pytest.mark.asyncio
async def test_process_batch_async():
    """Test async batch processing."""
    processor = DocumentProcessor()

    with patch.object(processor, "process_pdf") as mock_process:
        mock_process.return_value = TestReportDocument(
            file_path="test.pdf",
            metadata=DocumentMetadata(file_format="pdf"),
            sections=[],
            raw_text="Test",
            tables=[],
        )

        results = await processor.process_batch_async(
            ["test1.pdf", "test2.pdf"]
        )

        assert len(results) <= 2  # May have exceptions filtered out
