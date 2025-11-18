"""
OCR engine for processing scanned PDFs and images using Tesseract.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image

from ingestion.exceptions import (
    CorruptedFileError,
    DocumentParsingError,
    OCRError,
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


class OCREngine:
    """OCR engine for extracting text from scanned documents and images."""

    def __init__(self, file_path: str, language: str = "eng", dpi: int = 300):
        """
        Initialize OCR engine.

        Args:
            file_path: Path to PDF or image file
            language: Tesseract language code (default: 'eng')
            dpi: DPI for PDF to image conversion (default: 300)

        Raises:
            UnsupportedFormatError: If file format not supported
            OCRError: If Tesseract is not available
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.language = language
        self.dpi = dpi
        self.warnings: List[str] = []
        self.errors: List[str] = []

        # Check if file is PDF or image
        self.file_ext = self.file_path.suffix.lower()
        supported_formats = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]

        if self.file_ext not in supported_formats:
            raise UnsupportedFormatError(
                str(self.file_path), f"OCR supports: {', '.join(supported_formats)}"
            )

        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise OCRError(
                "Tesseract OCR is not installed or not in PATH. "
                "Install it from: https://github.com/tesseract-ocr/tesseract",
                str(self.file_path),
            )

    def pdf_to_images(self) -> List[Tuple[Image.Image, int]]:
        """
        Convert PDF pages to PIL images.

        Returns:
            List of (PIL Image, page_number) tuples

        Raises:
            OCRError: If PDF conversion fails
        """
        if self.file_ext != ".pdf":
            raise OCRError("Not a PDF file", str(self.file_path))

        images = []

        try:
            pdf_doc = fitz.open(str(self.file_path))

            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]

                # Render page to image with specified DPI
                # mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                zoom = self.dpi / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))

                images.append((pil_image, page_num))

            pdf_doc.close()

        except Exception as e:
            raise OCRError(f"Failed to convert PDF to images: {str(e)}", str(self.file_path))

        return images

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image: PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert("L")

        # Convert to numpy array
        img_array = np.array(image)

        # Apply thresholding for better contrast
        # Using Otsu's method via PIL
        from PIL import ImageOps

        # Auto-contrast
        image = ImageOps.autocontrast(image)

        # Optional: denoise (simple median filter approximation)
        # This is basic - for production, consider opencv
        # image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    def ocr_image(
        self, image: Image.Image, config: str = "--psm 1"
    ) -> Tuple[str, float]:
        """
        Perform OCR on a single image.

        Args:
            image: PIL Image
            config: Tesseract configuration string

        Returns:
            Tuple of (extracted text, confidence score 0-1)

        Raises:
            OCRError: If OCR fails
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Get OCR data with confidence
            ocr_data = pytesseract.image_to_data(
                processed_image, lang=self.language, config=config, output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(
                processed_image, lang=self.language, config=config
            )

            # Calculate average confidence
            confidences = [
                int(conf) for conf in ocr_data["conf"] if conf != "-1" and str(conf).isdigit()
            ]

            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            )

            return text.strip(), avg_confidence

        except Exception as e:
            raise OCRError(f"OCR processing failed: {str(e)}", str(self.file_path))

    def detect_tables_in_image(self, image: Image.Image) -> List[TableData]:
        """
        Attempt to detect and extract tables from image using OCR.

        Args:
            image: PIL Image

        Returns:
            List of TableData objects (may be empty)

        Note:
            This is a basic implementation. For production, consider using
            specialized table detection models like TableTransformer.
        """
        tables = []

        try:
            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(
                self.preprocess_image(image),
                lang=self.language,
                output_type=pytesseract.Output.DICT,
            )

            # Basic table detection heuristic:
            # Look for grid-like structure in text positions
            # This is simplified - real table detection is much more complex

            # For now, try to extract text line by line
            lines = []
            current_line = []
            last_top = -1

            for i in range(len(ocr_data["text"])):
                text = ocr_data["text"][i].strip()
                if not text:
                    continue

                top = ocr_data["top"][i]

                # New line if vertical position changed significantly
                if last_top != -1 and abs(top - last_top) > 10:
                    if current_line:
                        lines.append(current_line)
                    current_line = [text]
                else:
                    current_line.append(text)

                last_top = top

            if current_line:
                lines.append(current_line)

            # If we have regular columnar data, treat as table
            if len(lines) > 2:
                # Check if lines have similar column counts
                col_counts = [len(line) for line in lines]
                avg_cols = sum(col_counts) / len(col_counts)

                if max(col_counts) - min(col_counts) <= 2:  # Relatively consistent
                    # Treat first line as header
                    headers = lines[0]
                    data = lines[1:]

                    # Pad rows to match header length
                    max_cols = len(headers)
                    data = [row + [""] * (max_cols - len(row)) for row in data]

                    table = TableData(data=data, headers=headers, confidence=0.7)
                    tables.append(table)

        except Exception as e:
            self.warnings.append(f"Table detection failed: {str(e)}")

        return tables

    def extract_text_from_pdf(self) -> Tuple[str, float, List[ParagraphData]]:
        """
        Extract text from scanned PDF using OCR.

        Returns:
            Tuple of (full text, average confidence, paragraphs list)
        """
        if self.file_ext != ".pdf":
            raise OCRError("Not a PDF file", str(self.file_path))

        all_text = []
        all_confidences = []
        all_paragraphs = []
        para_index = 0

        images = self.pdf_to_images()

        for image, page_num in images:
            try:
                text, confidence = self.ocr_image(image)

                if text:
                    all_text.append(f"--- Page {page_num + 1} ---\n{text}")
                    all_confidences.append(confidence)

                    # Split into paragraphs
                    for para in text.split("\n\n"):
                        if para.strip():
                            all_paragraphs.append(
                                ParagraphData(text=para.strip(), paragraph_index=para_index)
                            )
                            para_index += 1
                else:
                    self.warnings.append(f"No text extracted from page {page_num + 1}")

            except Exception as e:
                self.errors.append(f"OCR failed for page {page_num + 1}: {str(e)}")

        full_text = "\n\n".join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        return full_text, avg_confidence, all_paragraphs

    def extract_text_from_image(self) -> Tuple[str, float]:
        """
        Extract text from single image file.

        Returns:
            Tuple of (text, confidence)
        """
        try:
            image = Image.open(str(self.file_path))
            return self.ocr_image(image)
        except Exception as e:
            raise OCRError(f"Failed to process image: {str(e)}", str(self.file_path))

    def calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of the file."""
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_metadata(self) -> DocumentMetadata:
        """Extract basic metadata from file."""
        file_size = self.file_path.stat().st_size

        page_count = 1
        if self.file_ext == ".pdf":
            try:
                pdf_doc = fitz.open(str(self.file_path))
                page_count = len(pdf_doc)
                pdf_doc.close()
            except Exception:
                pass

        return DocumentMetadata(
            page_count=page_count, file_size_bytes=file_size, language=self.language
        )

    def parse(self) -> DocumentIngestionResult:
        """
        Parse document using OCR.

        Returns:
            DocumentIngestionResult with OCR-extracted data

        Raises:
            OCRError: If OCR processing fails
        """
        try:
            if self.file_ext == ".pdf":
                text_content, ocr_confidence, paragraphs = self.extract_text_from_pdf()
                tables = []  # TODO: Implement table detection for scanned PDFs
            else:
                # Single image
                text_content, ocr_confidence = self.extract_text_from_image()
                paragraphs = [
                    ParagraphData(text=para.strip(), paragraph_index=idx)
                    for idx, para in enumerate(text_content.split("\n\n"))
                    if para.strip()
                ]
                tables = []

            metadata = self.extract_metadata()
            file_hash = self.calculate_file_hash()

            # Add confidence warning
            if ocr_confidence < 0.7:
                self.warnings.append(
                    f"Low OCR confidence ({ocr_confidence:.2%}). Results may be inaccurate."
                )

            result = DocumentIngestionResult(
                text_content=text_content,
                tables=tables,
                images=[],  # OCR doesn't extract embedded images
                paragraphs=paragraphs,
                metadata=metadata,
                extraction_method=ExtractionMethod.OCR,
                ocr_confidence=ocr_confidence,
                file_hash=file_hash,
                file_path=str(self.file_path),
                warnings=self.warnings,
                errors=self.errors,
            )

            return result

        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"OCR parsing failed: {str(e)}", str(self.file_path))


def ocr_document(file_path: str, language: str = "eng", dpi: int = 300) -> DocumentIngestionResult:
    """
    Convenience function to OCR a document.

    Args:
        file_path: Path to PDF or image file
        language: Tesseract language code
        dpi: DPI for PDF rendering

    Returns:
        DocumentIngestionResult with OCR data
    """
    engine = OCREngine(file_path, language=language, dpi=dpi)
    return engine.parse()


# Add missing import
import io
