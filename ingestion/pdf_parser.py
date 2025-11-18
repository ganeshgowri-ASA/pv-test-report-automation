"""
PDF document parser with support for native PDFs, table extraction, and image extraction.
"""

import hashlib
import io
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from PyPDF2 import PdfReader

from ingestion.exceptions import (
    CorruptedFileError,
    DocumentParsingError,
    PasswordProtectedError,
    TableExtractionError,
    UnsupportedFormatError,
)
from ingestion.models import (
    DocumentIngestionResult,
    DocumentMetadata,
    ExtractionMethod,
    ImageData,
    ParagraphData,
    TableData,
)


class PDFIngestion:
    """Comprehensive PDF parser with text, table, and image extraction."""

    def __init__(self, file_path: str, password: Optional[str] = None):
        """
        Initialize PDF parser.

        Args:
            file_path: Path to PDF file
            password: Optional password for encrypted PDFs

        Raises:
            UnsupportedFormatError: If file is not a PDF
            CorruptedFileError: If PDF is corrupted
            PasswordProtectedError: If PDF requires password
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.file_path.suffix.lower() != ".pdf":
            raise UnsupportedFormatError(str(self.file_path), "File is not a PDF")

        self.password = password
        self.warnings: List[str] = []
        self.errors: List[str] = []

        # Initialize PDF readers
        try:
            self.pdf_reader = PdfReader(str(self.file_path))

            # Check if encrypted
            if self.pdf_reader.is_encrypted:
                if password:
                    decrypt_result = self.pdf_reader.decrypt(password)
                    if decrypt_result == 0:
                        raise PasswordProtectedError(str(self.file_path))
                else:
                    raise PasswordProtectedError(str(self.file_path))

        except PasswordProtectedError:
            raise
        except Exception as e:
            raise CorruptedFileError(str(self.file_path), str(e))

        # Initialize pdfplumber for table extraction
        try:
            self.plumber_pdf = pdfplumber.open(str(self.file_path), password=password)
        except Exception as e:
            self.warnings.append(f"pdfplumber initialization failed: {str(e)}")
            self.plumber_pdf = None

        # Initialize PyMuPDF for image extraction
        try:
            self.fitz_doc = fitz.open(str(self.file_path))
        except Exception as e:
            self.warnings.append(f"PyMuPDF initialization failed: {str(e)}")
            self.fitz_doc = None

    def extract_text(self) -> str:
        """
        Extract all text content from PDF.

        Returns:
            Complete text content from all pages
        """
        text_parts = []

        try:
            for page in self.pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
        except Exception as e:
            self.errors.append(f"Text extraction failed: {str(e)}")

        return "\n\n".join(text_parts)

    def extract_text_by_page(self) -> List[str]:
        """
        Extract text from each page separately.

        Returns:
            List of text content per page
        """
        pages_text = []

        try:
            for page_num, page in enumerate(self.pdf_reader.pages):
                page_text = page.extract_text()
                pages_text.append(page_text.strip() if page_text else "")
        except Exception as e:
            self.errors.append(f"Page-by-page text extraction failed: {str(e)}")

        return pages_text

    def extract_tables(
        self, page_number: Optional[int] = None
    ) -> List[TableData]:
        """
        Extract tables from PDF using pdfplumber.

        Args:
            page_number: Optional specific page to extract from (0-indexed).
                        If None, extracts from all pages.

        Returns:
            List of TableData objects

        Raises:
            TableExtractionError: If table extraction fails
        """
        if not self.plumber_pdf:
            raise TableExtractionError(
                "pdfplumber not available for table extraction", str(self.file_path)
            )

        tables_data = []
        table_index = 0

        try:
            pages_to_process = (
                [self.plumber_pdf.pages[page_number]]
                if page_number is not None
                else self.plumber_pdf.pages
            )

            for page_idx, page in enumerate(pages_to_process):
                actual_page_num = page_number if page_number is not None else page_idx

                try:
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) == 0:
                            continue

                        # First row as headers
                        headers = table[0] if table else None
                        data = table[1:] if len(table) > 1 else []

                        # Clean up None values
                        if headers:
                            headers = [str(h).strip() if h else "" for h in headers]
                        data = [
                            [str(cell).strip() if cell else "" for cell in row]
                            for row in data
                        ]

                        if data:  # Only add if has data rows
                            table_data = TableData(
                                data=data,
                                headers=headers,
                                page_number=actual_page_num,
                                table_index=table_index,
                                confidence=1.0,
                            )
                            tables_data.append(table_data)
                            table_index += 1

                except Exception as e:
                    self.warnings.append(
                        f"Failed to extract tables from page {actual_page_num}: {str(e)}"
                    )

        except Exception as e:
            raise TableExtractionError(str(e), str(self.file_path), page_number)

        return tables_data

    def extract_tables_with_tabula(
        self, page_number: Optional[int] = None
    ) -> List[TableData]:
        """
        Alternative table extraction using tabula-py (better for complex tables).

        Args:
            page_number: Optional specific page (1-indexed for tabula)

        Returns:
            List of TableData objects
        """
        try:
            import tabula
        except ImportError:
            self.warnings.append("tabula-py not available")
            return []

        tables_data = []

        try:
            # tabula uses 1-indexed pages
            pages = str(page_number + 1) if page_number is not None else "all"

            # Extract tables as list of DataFrames
            dfs = tabula.read_pdf(
                str(self.file_path), pages=pages, multiple_tables=True, silent=True
            )

            for idx, df in enumerate(dfs):
                if df.empty:
                    continue

                # Convert DataFrame to table data
                headers = df.columns.tolist()
                data = df.values.tolist()

                # Clean data
                headers = [str(h).strip() for h in headers]
                data = [[str(cell).strip() if cell else "" for cell in row] for row in data]

                table_data = TableData(
                    data=data,
                    headers=headers,
                    page_number=page_number,
                    table_index=idx,
                    confidence=1.0,
                )
                tables_data.append(table_data)

        except Exception as e:
            self.warnings.append(f"tabula-py extraction failed: {str(e)}")

        return tables_data

    def extract_images(self) -> List[ImageData]:
        """
        Extract embedded images from PDF.

        Returns:
            List of ImageData objects
        """
        if not self.fitz_doc:
            self.warnings.append("PyMuPDF not available for image extraction")
            return []

        images_data = []

        try:
            for page_num in range(len(self.fitz_doc)):
                page = self.fitz_doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = self.fitz_doc.extract_image(xref)

                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]  # png, jpeg, etc.

                        # Get dimensions
                        try:
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            width, height = pil_image.size
                        except Exception:
                            width, height = 0, 0

                        image_data = ImageData(
                            image_bytes=image_bytes,
                            format=image_ext.upper(),
                            width=width,
                            height=height,
                            page_number=page_num,
                        )
                        images_data.append(image_data)

                    except Exception as e:
                        self.warnings.append(
                            f"Failed to extract image {img_index} from page {page_num}: {str(e)}"
                        )

        except Exception as e:
            self.errors.append(f"Image extraction failed: {str(e)}")

        return images_data

    def extract_metadata(self) -> DocumentMetadata:
        """
        Extract PDF metadata and document properties.

        Returns:
            DocumentMetadata object
        """
        metadata_dict = self.pdf_reader.metadata if self.pdf_reader.metadata else {}

        # Parse dates
        creation_date = None
        modification_date = None

        try:
            if "/CreationDate" in metadata_dict:
                creation_date = self._parse_pdf_date(metadata_dict["/CreationDate"])
            if "/ModDate" in metadata_dict:
                modification_date = self._parse_pdf_date(metadata_dict["/ModDate"])
        except Exception as e:
            self.warnings.append(f"Date parsing failed: {str(e)}")

        # Extract keywords
        keywords = []
        if "/Keywords" in metadata_dict:
            keywords_str = metadata_dict.get("/Keywords", "")
            if keywords_str:
                keywords = [k.strip() for k in str(keywords_str).split(",")]

        # Get file size
        file_size = self.file_path.stat().st_size

        metadata = DocumentMetadata(
            author=metadata_dict.get("/Author"),
            creation_date=creation_date,
            modification_date=modification_date,
            title=metadata_dict.get("/Title"),
            subject=metadata_dict.get("/Subject"),
            keywords=keywords,
            producer=metadata_dict.get("/Producer"),
            page_count=len(self.pdf_reader.pages),
            file_size_bytes=file_size,
        )

        return metadata

    def _parse_pdf_date(self, pdf_date_str: str) -> Optional[datetime]:
        """Parse PDF date format (D:YYYYMMDDHHmmSS)."""
        if not pdf_date_str:
            return None

        try:
            # Remove D: prefix and timezone
            date_str = str(pdf_date_str).replace("D:", "").split("+")[0].split("-")[0]

            # Parse based on length
            if len(date_str) >= 14:
                return datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], "%Y%m%d")
        except Exception:
            pass

        return None

    def is_scanned_pdf(self, threshold: int = 100) -> bool:
        """
        Heuristic to detect if PDF is scanned (needs OCR).

        Args:
            threshold: Minimum character count to consider as native PDF

        Returns:
            True if likely scanned, False otherwise
        """
        text = self.extract_text()
        char_count = len(text.strip())

        # If very little text extracted, likely scanned
        return char_count < threshold

    def calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of the file."""
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def parse(
        self, use_ocr_if_scanned: bool = False
    ) -> DocumentIngestionResult:
        """
        Parse complete PDF document.

        Args:
            use_ocr_if_scanned: If True and PDF appears scanned, use OCR

        Returns:
            DocumentIngestionResult with all extracted data

        Raises:
            DocumentParsingError: If parsing fails
        """
        try:
            # Check if scanned
            is_scanned = self.is_scanned_pdf()

            if is_scanned and use_ocr_if_scanned:
                # Delegate to OCR engine
                from ingestion.ocr_engine import OCREngine

                ocr_engine = OCREngine(str(self.file_path))
                return ocr_engine.parse()

            # Extract data
            text_content = self.extract_text()
            tables = self.extract_tables()
            images = self.extract_images()
            metadata = self.extract_metadata()
            file_hash = self.calculate_file_hash()

            # Create paragraph data from text
            paragraphs = []
            for idx, para in enumerate(text_content.split("\n\n")):
                if para.strip():
                    paragraphs.append(
                        ParagraphData(text=para.strip(), paragraph_index=idx)
                    )

            if is_scanned:
                self.warnings.append(
                    "PDF appears to be scanned. Consider using OCR for better extraction."
                )

            result = DocumentIngestionResult(
                text_content=text_content,
                tables=tables,
                images=images,
                paragraphs=paragraphs,
                metadata=metadata,
                extraction_method=ExtractionMethod.NATIVE,
                ocr_confidence=1.0,
                file_hash=file_hash,
                file_path=str(self.file_path),
                warnings=self.warnings,
                errors=self.errors,
            )

            return result

        except Exception as e:
            raise DocumentParsingError(f"Failed to parse PDF: {str(e)}", str(self.file_path))

    def __del__(self):
        """Clean up resources."""
        if self.plumber_pdf:
            try:
                self.plumber_pdf.close()
            except Exception:
                pass

        if self.fitz_doc:
            try:
                self.fitz_doc.close()
            except Exception:
                pass


def parse_pdf_document(
    file_path: str, password: Optional[str] = None, use_ocr: bool = False
) -> DocumentIngestionResult:
    """
    Convenience function to parse a PDF document.

    Args:
        file_path: Path to PDF file
        password: Optional password for encrypted PDFs
        use_ocr: Use OCR if PDF appears scanned

    Returns:
        DocumentIngestionResult with extracted data
    """
    parser = PDFIngestion(file_path, password=password)
    return parser.parse(use_ocr_if_scanned=use_ocr)
