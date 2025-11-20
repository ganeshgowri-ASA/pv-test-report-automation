"""
Document Processor for PV Test Reports (Session 07)

Processes PDF and Word documents, extracts text, tables, and metadata
for PV test reports following IEC, ISO, and NABL standards.
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pdfplumber
import pypdf
from docx import Document
from pydantic import BaseModel, Field, validator


class DocumentMetadata(BaseModel):
    """Metadata extracted from test report documents."""

    report_id: Optional[str] = None
    test_standard: Optional[str] = None
    test_date: Optional[datetime] = None
    lab_name: Optional[str] = None
    accreditation: Optional[str] = None
    module_manufacturer: Optional[str] = None
    module_model: Optional[str] = None
    module_serial: Optional[str] = None
    test_engineer: Optional[str] = None
    reviewer: Optional[str] = None
    issue_date: Optional[datetime] = None
    page_count: int = 0
    file_format: str = Field(..., description="pdf or docx")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TableData(BaseModel):
    """Structured table data from documents."""

    table_number: int
    caption: Optional[str] = None
    headers: List[str]
    rows: List[List[str]]
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SectionData(BaseModel):
    """Document section with structured content."""

    section_number: Optional[str] = None
    title: str
    content: str
    page_start: int
    page_end: int
    subsections: List["SectionData"] = Field(default_factory=list)
    tables: List[TableData] = Field(default_factory=list)

    class Config:
        # Allow forward references for recursive model
        arbitrary_types_allowed = True


class TestReportDocument(BaseModel):
    """Complete test report document structure."""

    file_path: str
    metadata: DocumentMetadata
    sections: List[SectionData]
    raw_text: str
    tables: List[TableData]
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DocumentProcessorConfig(BaseModel):
    """Configuration for document processor."""

    extract_images: bool = Field(default=False)
    extract_tables: bool = Field(default=True)
    extract_metadata: bool = Field(default=True)
    ocr_enabled: bool = Field(default=False)
    language: str = Field(default="eng")
    max_file_size_mb: int = Field(default=100)
    timeout_seconds: int = Field(default=300)


class DocumentProcessor:
    """
    Production-ready document processor for PV test reports.

    Supports:
    - PDF parsing with text and table extraction
    - Word document (.docx) processing
    - Metadata extraction
    - Section identification
    - Table extraction and structuring
    - Async batch processing
    - Progress tracking
    """

    # Common test standards patterns
    STANDARD_PATTERNS = {
        "IEC 61215": r"IEC\s*61215[-:]?\s*\d*",
        "IEC 61730": r"IEC\s*61730[-:]?\s*\d*",
        "IEC 61853": r"IEC\s*61853[-:]?\s*\d*",
        "IEC 62716": r"IEC\s*62716[-:]?\s*\d*",
        "IEC 60904": r"IEC\s*60904[-:]?\s*\d*",
        "ISO 17025": r"ISO[/\s]*17025:?\s*\d*",
        "ISO 9001": r"ISO[/\s]*9001:?\s*\d*",
    }

    def __init__(self, config: Optional[DocumentProcessorConfig] = None):
        """Initialize document processor."""
        self.config = config or DocumentProcessorConfig()
        self._progress_callback = None

    def set_progress_callback(self, callback):
        """Set callback for progress tracking."""
        self._progress_callback = callback

    def _report_progress(self, current: int, total: int, message: str = ""):
        """Report progress if callback is set."""
        if self._progress_callback:
            self._progress_callback(current, total, message)

    def process_pdf(self, file_path: Union[str, Path]) -> TestReportDocument:
        """
        Process PDF test report.

        Args:
            file_path: Path to PDF file

        Returns:
            TestReportDocument object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or too large
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File size {file_size_mb:.1f}MB exceeds limit "
                f"{self.config.max_file_size_mb}MB"
            )

        raw_text = ""
        tables = []
        page_count = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, 1):
                    self._report_progress(
                        page_num, page_count, f"Processing page {page_num}"
                    )

                    # Extract text
                    page_text = page.extract_text() or ""
                    raw_text += f"\n--- Page {page_num} ---\n{page_text}"

                    # Extract tables if enabled
                    if self.config.extract_tables:
                        page_tables = page.extract_tables()
                        for table_idx, table in enumerate(page_tables or []):
                            if table and len(table) > 0:
                                table_data = self._process_table(
                                    table, table_idx, page_num
                                )
                                tables.append(table_data)

        except Exception as e:
            raise ValueError(f"Failed to process PDF: {e}") from e

        # Extract metadata
        metadata = self._extract_metadata_from_text(raw_text, "pdf", page_count)

        # Identify sections
        sections = self._identify_sections(raw_text)

        # Extract structured data
        extracted_data = self._extract_test_data(raw_text, tables)

        return TestReportDocument(
            file_path=str(file_path),
            metadata=metadata,
            sections=sections,
            raw_text=raw_text,
            tables=tables,
            extracted_data=extracted_data,
        )

    def process_docx(self, file_path: Union[str, Path]) -> TestReportDocument:
        """
        Process Word (.docx) test report.

        Args:
            file_path: Path to Word document

        Returns:
            TestReportDocument object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File size {file_size_mb:.1f}MB exceeds limit "
                f"{self.config.max_file_size_mb}MB"
            )

        try:
            doc = Document(file_path)

            # Extract text
            raw_text = ""
            for para_num, para in enumerate(doc.paragraphs):
                self._report_progress(
                    para_num + 1,
                    len(doc.paragraphs),
                    f"Processing paragraph {para_num + 1}",
                )
                raw_text += para.text + "\n"

            # Extract tables
            tables = []
            if self.config.extract_tables:
                for table_idx, table in enumerate(doc.tables):
                    table_data = self._process_docx_table(table, table_idx)
                    tables.append(table_data)

            # Extract metadata
            page_count = len(raw_text.split("\n")) // 50  # Rough estimate
            metadata = self._extract_metadata_from_text(raw_text, "docx", page_count)

            # Add Word metadata
            core_props = doc.core_properties
            if core_props.author:
                metadata.test_engineer = core_props.author
            if core_props.created:
                metadata.issue_date = core_props.created
            if core_props.modified:
                metadata.custom_fields["modified_date"] = core_props.modified.isoformat()

            # Identify sections
            sections = self._identify_sections(raw_text)

            # Extract structured data
            extracted_data = self._extract_test_data(raw_text, tables)

            return TestReportDocument(
                file_path=str(file_path),
                metadata=metadata,
                sections=sections,
                raw_text=raw_text,
                tables=tables,
                extracted_data=extracted_data,
            )

        except Exception as e:
            raise ValueError(f"Failed to process Word document: {e}") from e

    def _process_table(
        self, table: List[List[str]], table_number: int, page_number: int
    ) -> TableData:
        """Process table extracted from PDF."""
        if not table or len(table) == 0:
            return TableData(
                table_number=table_number,
                headers=[],
                rows=[],
                page_number=page_number,
            )

        # First row is typically headers
        headers = [str(cell).strip() if cell else "" for cell in table[0]]

        # Remaining rows are data
        rows = []
        for row in table[1:]:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            rows.append(cleaned_row)

        return TableData(
            table_number=table_number,
            headers=headers,
            rows=rows,
            page_number=page_number,
        )

    def _process_docx_table(self, table, table_number: int) -> TableData:
        """Process table from Word document."""
        headers = []
        rows = []

        # Extract headers from first row
        if len(table.rows) > 0:
            headers = [cell.text.strip() for cell in table.rows[0].cells]

        # Extract data rows
        for row_idx, row in enumerate(table.rows[1:], 1):
            row_data = [cell.text.strip() for cell in row.cells]
            rows.append(row_data)

        return TableData(
            table_number=table_number, headers=headers, rows=rows
        )

    def _extract_metadata_from_text(
        self, text: str, file_format: str, page_count: int
    ) -> DocumentMetadata:
        """Extract metadata from document text using regex patterns."""
        metadata = DocumentMetadata(file_format=file_format, page_count=page_count)

        # Report ID patterns
        report_id_match = re.search(
            r"Report\s+(?:ID|No|Number)[\s:]+([A-Z0-9\-/]+)", text, re.IGNORECASE
        )
        if report_id_match:
            metadata.report_id = report_id_match.group(1)

        # Test standard
        for standard, pattern in self.STANDARD_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                metadata.test_standard = standard
                break

        # Lab name patterns
        lab_patterns = [
            r"Test(?:ing)?\s+Lab(?:oratory)?[\s:]+([^\n]+)",
            r"Lab(?:oratory)?[\s:]+([^\n]+)",
        ]
        for pattern in lab_patterns:
            lab_match = re.search(pattern, text, re.IGNORECASE)
            if lab_match:
                metadata.lab_name = lab_match.group(1).strip()
                break

        # Accreditation
        accred_match = re.search(
            r"Accreditation[\s:]+([^\n]+)", text, re.IGNORECASE
        )
        if accred_match:
            metadata.accreditation = accred_match.group(1).strip()

        # Module information
        mfr_match = re.search(
            r"Manufacturer[\s:]+([^\n]+)", text, re.IGNORECASE
        )
        if mfr_match:
            metadata.module_manufacturer = mfr_match.group(1).strip()

        model_match = re.search(r"Model[\s:]+([^\n]+)", text, re.IGNORECASE)
        if model_match:
            metadata.module_model = model_match.group(1).strip()

        serial_match = re.search(
            r"Serial\s+(?:Number|No)[\s:]+([^\n]+)", text, re.IGNORECASE
        )
        if serial_match:
            metadata.module_serial = serial_match.group(1).strip()

        # Test date
        date_patterns = [
            r"Test\s+Date[\s:]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Date\s+of\s+Test[\s:]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    # Try common date formats
                    for fmt in ["%d-%m-%Y", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%Y"]:
                        try:
                            metadata.test_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
                break

        return metadata

    def _identify_sections(self, text: str) -> List[SectionData]:
        """Identify document sections based on headings."""
        sections = []

        # Common section patterns for test reports
        section_patterns = [
            r"^\d+\.\s+([A-Z][^\n]+)",  # Numbered sections (1. Introduction)
            r"^([A-Z][A-Z\s]{3,}):?\s*$",  # ALL CAPS headings
            r"^Section\s+\d+[\s:]+([^\n]+)",  # Section 1: Title
        ]

        lines = text.split("\n")
        current_section = None
        current_content = []
        page_num = 1

        for line_num, line in enumerate(lines):
            # Track page numbers
            if "--- Page" in line:
                page_match = re.search(r"Page\s+(\d+)", line)
                if page_match:
                    page_num = int(page_match.group(1))
                continue

            # Check if line is a section header
            is_header = False
            for pattern in section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Save previous section
                    if current_section:
                        current_section.content = "\n".join(current_content)
                        current_section.page_end = page_num
                        sections.append(current_section)

                    # Start new section
                    title = match.group(1).strip()
                    current_section = SectionData(
                        title=title,
                        content="",
                        page_start=page_num,
                        page_end=page_num,
                    )
                    current_content = []
                    is_header = True
                    break

            if not is_header and line.strip():
                current_content.append(line)

        # Add final section
        if current_section:
            current_section.content = "\n".join(current_content)
            current_section.page_end = page_num
            sections.append(current_section)

        return sections

    def _extract_test_data(
        self, text: str, tables: List[TableData]
    ) -> Dict[str, Any]:
        """Extract structured test data from text and tables."""
        extracted = {}

        # Extract numerical test results
        patterns = {
            "voc": r"V[oO][cC][\s:=]+(\d+\.?\d*)\s*V",
            "isc": r"I[sS][cC][\s:=]+(\d+\.?\d*)\s*A",
            "pmax": r"P[mM][aA][xX][\s:=]+(\d+\.?\d*)\s*W",
            "vmp": r"V[mM][pP][\s:=]+(\d+\.?\d*)\s*V",
            "imp": r"I[mM][pP][\s:=]+(\d+\.?\d*)\s*A",
            "fill_factor": r"(?:FF|Fill\s+Factor)[\s:=]+(\d+\.?\d*)",
            "efficiency": r"Efficiency[\s:=]+(\d+\.?\d*)\s*%",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    extracted[key] = float(match.group(1))
                except ValueError:
                    pass

        # Extract from tables
        for table in tables:
            # Look for parameter-value tables
            if len(table.headers) >= 2:
                for row in table.rows:
                    if len(row) >= 2:
                        param = row[0].lower().strip()
                        value = row[1].strip()

                        # Try to convert to number
                        try:
                            # Remove units
                            value_clean = re.sub(r"[A-Za-z%°]", "", value).strip()
                            extracted[param] = float(value_clean)
                        except (ValueError, AttributeError):
                            extracted[param] = value

        return extracted

    async def process_batch_async(
        self, file_paths: List[Union[str, Path]]
    ) -> List[TestReportDocument]:
        """
        Asynchronously process multiple documents.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of TestReportDocument objects
        """
        tasks = []
        for file_path in file_paths:
            file_path = Path(file_path)
            if file_path.suffix.lower() == ".pdf":
                task = asyncio.to_thread(self.process_pdf, file_path)
            elif file_path.suffix.lower() in [".docx", ".doc"]:
                task = asyncio.to_thread(self.process_docx, file_path)
            else:
                continue

            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing {file_paths[idx]}: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def search_text(
        self, document: TestReportDocument, pattern: str, case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for pattern in document text.

        Returns:
            List of matches with context and location
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = []

        for match in re.finditer(pattern, document.raw_text, flags):
            # Get context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(document.raw_text), match.end() + 50)
            context = document.raw_text[start:end]

            matches.append(
                {
                    "match": match.group(0),
                    "context": context,
                    "position": match.start(),
                }
            )

        return matches
