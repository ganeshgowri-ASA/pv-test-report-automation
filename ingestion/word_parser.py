"""
Word document (.docx, .doc) parser for extracting structured data.
"""

import hashlib
import io
import os
from pathlib import Path
from typing import List, Optional

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from ingestion.exceptions import (
    CorruptedFileError,
    DocumentParsingError,
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


class WordDocumentParser:
    """Parser for Microsoft Word documents (.docx format)."""

    def __init__(self, file_path: str):
        """
        Initialize Word document parser.

        Args:
            file_path: Path to the Word document

        Raises:
            UnsupportedFormatError: If file format is not supported
            CorruptedFileError: If file cannot be opened
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file extension
        if self.file_path.suffix.lower() not in [".docx"]:
            raise UnsupportedFormatError(
                str(self.file_path), f"Format {self.file_path.suffix} not supported. Use .docx files."
            )

        try:
            self.document = Document(str(self.file_path))
        except Exception as e:
            raise CorruptedFileError(str(self.file_path), str(e))

        self.warnings: List[str] = []
        self.errors: List[str] = []

    def extract_text(self) -> str:
        """
        Extract all text content from document.

        Returns:
            Complete text content with paragraph separation
        """
        paragraphs = []
        for paragraph in self.document.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)

    def extract_paragraphs(self) -> List[ParagraphData]:
        """
        Extract paragraphs with formatting information.

        Returns:
            List of ParagraphData objects with formatting metadata
        """
        paragraphs_data = []

        for idx, paragraph in enumerate(self.document.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue

            # Check for heading
            is_heading = paragraph.style.name.startswith("Heading")
            heading_level = None
            if is_heading:
                try:
                    heading_level = int(paragraph.style.name.split()[-1])
                except (ValueError, IndexError):
                    heading_level = 1

            # Check text formatting (check first run if available)
            is_bold = False
            is_italic = False
            font_size = None

            if paragraph.runs:
                first_run = paragraph.runs[0]
                is_bold = first_run.bold or False
                is_italic = first_run.italic or False
                if first_run.font.size:
                    font_size = first_run.font.size.pt

            para_data = ParagraphData(
                text=text,
                is_bold=is_bold,
                is_italic=is_italic,
                is_heading=is_heading,
                heading_level=heading_level,
                font_size=font_size,
                paragraph_index=idx,
            )
            paragraphs_data.append(para_data)

        return paragraphs_data

    def extract_tables(self) -> List[TableData]:
        """
        Extract all tables from document.

        Returns:
            List of TableData objects
        """
        tables_data = []

        for table_idx, table in enumerate(self.document.tables):
            try:
                # Extract table data
                data = []
                headers = None

                for row_idx, row in enumerate(table.rows):
                    row_data = [cell.text.strip() for cell in row.cells]

                    # First row as headers if it looks like headers
                    if row_idx == 0:
                        # Check if first row has bold text or is different
                        if self._is_header_row(row):
                            headers = row_data
                            continue

                    data.append(row_data)

                if data:  # Only add if table has data
                    table_data = TableData(
                        data=data, headers=headers, table_index=table_idx, confidence=1.0
                    )
                    tables_data.append(table_data)

            except Exception as e:
                self.warnings.append(f"Failed to extract table {table_idx}: {str(e)}")

        return tables_data

    def _is_header_row(self, row) -> bool:
        """Check if a table row appears to be a header row."""
        # Check if cells in first row have bold text
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    if run.bold:
                        return True
        return False

    def extract_images(self) -> List[ImageData]:
        """
        Extract embedded images from document.

        Returns:
            List of ImageData objects
        """
        images_data = []

        # Access document relationships to get images
        try:
            for rel in self.document.part.rels.values():
                if "image" in rel.target_ref:
                    try:
                        image_part = rel.target_part
                        image_bytes = image_part.blob

                        # Determine format from content type
                        content_type = image_part.content_type
                        format_map = {
                            "image/png": "PNG",
                            "image/jpeg": "JPEG",
                            "image/jpg": "JPEG",
                            "image/gif": "GIF",
                            "image/bmp": "BMP",
                        }
                        image_format = format_map.get(content_type, "UNKNOWN")

                        # Try to get image dimensions
                        try:
                            from PIL import Image

                            img = Image.open(io.BytesIO(image_bytes))
                            width, height = img.size
                        except Exception:
                            width, height = 0, 0
                            self.warnings.append(
                                f"Could not determine dimensions for image {len(images_data)}"
                            )

                        image_data = ImageData(
                            image_bytes=image_bytes,
                            format=image_format,
                            width=width,
                            height=height,
                        )
                        images_data.append(image_data)

                    except Exception as e:
                        self.warnings.append(f"Failed to extract image: {str(e)}")

        except Exception as e:
            self.warnings.append(f"Error accessing document images: {str(e)}")

        return images_data

    def extract_metadata(self) -> DocumentMetadata:
        """
        Extract document properties and metadata.

        Returns:
            DocumentMetadata object
        """
        core_props = self.document.core_properties

        # Get file size
        file_size = self.file_path.stat().st_size

        # Count pages (approximation - Word doesn't expose page count directly)
        # We'll count paragraphs + tables as a rough estimate
        page_count = max(1, (len(self.document.paragraphs) + len(self.document.tables)) // 25)

        metadata = DocumentMetadata(
            author=core_props.author,
            creation_date=core_props.created,
            modification_date=core_props.modified,
            title=core_props.title,
            subject=core_props.subject,
            keywords=core_props.keywords.split(",") if core_props.keywords else [],
            page_count=page_count,
            file_size_bytes=file_size,
        )

        return metadata

    def extract_comments(self) -> List[str]:
        """
        Extract comments from document.

        Returns:
            List of comment texts
        """
        comments = []
        try:
            # Comments are in document part relationships
            if hasattr(self.document.part, "comments_part"):
                comments_part = self.document.part.comments_part
                if comments_part:
                    for comment in comments_part.element.findall(".//{*}comment"):
                        comment_text = "".join(
                            t.text for t in comment.findall(".//{*}t") if t.text
                        )
                        if comment_text.strip():
                            comments.append(comment_text.strip())
        except Exception as e:
            self.warnings.append(f"Could not extract comments: {str(e)}")

        return comments

    def calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of the file."""
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def parse(self) -> DocumentIngestionResult:
        """
        Parse complete Word document and extract all data.

        Returns:
            DocumentIngestionResult with all extracted data

        Raises:
            DocumentParsingError: If parsing fails
        """
        try:
            text_content = self.extract_text()
            tables = self.extract_tables()
            images = self.extract_images()
            paragraphs = self.extract_paragraphs()
            metadata = self.extract_metadata()
            file_hash = self.calculate_file_hash()

            # Extract comments and add to warnings if present
            comments = self.extract_comments()
            if comments:
                self.warnings.append(
                    f"Document contains {len(comments)} comments (track changes may be present)"
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
            raise DocumentParsingError(f"Failed to parse Word document: {str(e)}", str(self.file_path))


def parse_word_document(file_path: str) -> DocumentIngestionResult:
    """
    Convenience function to parse a Word document.

    Args:
        file_path: Path to Word document

    Returns:
        DocumentIngestionResult with extracted data
    """
    parser = WordDocumentParser(file_path)
    return parser.parse()
