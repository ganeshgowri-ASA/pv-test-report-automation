"""
Export Module

Provides production-ready export engines for multiple formats.
Supports PDF, Word, HTML, Excel, JSON, and XML with customization options.
"""

from .base_exporter import (
    BaseExporter,
    ExportFormat,
    ExportStatus,
    ExportOptions,
    ExportProgress,
    TemplateManager,
    ExportRegistry,
    create_exporter
)

from .pdf_exporter import PDFExporter, PDFEngine
from .word_exporter import WordExporter
from .html_exporter import HTMLExporter
from .excel_exporter import ExcelExporter, ExcelEngine
from .json_xml_exporter import JSONExporter, XMLExporter, create_api_response


__all__ = [
    # Base classes
    'BaseExporter',
    'ExportFormat',
    'ExportStatus',
    'ExportOptions',
    'ExportProgress',
    'TemplateManager',
    'ExportRegistry',
    'create_exporter',

    # Exporters
    'PDFExporter',
    'WordExporter',
    'HTMLExporter',
    'ExcelExporter',
    'JSONExporter',
    'XMLExporter',

    # Engines
    'PDFEngine',
    'ExcelEngine',

    # Utilities
    'create_api_response',
]


__version__ = '1.0.0'
