"""
Electroluminescence (EL) Testing Module

This module provides comprehensive EL image processing and defect detection
for photovoltaic modules.

Components:
    - image_processor: Image loading, preprocessing, segmentation, and defect classification
    - defect_detector: Advanced ML-based crack detection and defect analysis
    - report_generator: Comprehensive test report generation with visualizations

Usage:
    from src.tests.electroluminescence import ELImageProcessor, AdvancedDefectDetector, ELReportGenerator

    # Process EL image
    processor = ELImageProcessor()
    result = processor.process_image("path/to/el_image.tif")

    # Advanced defect detection
    detector = AdvancedDefectDetector()
    crack_mask, crack_features = detector.detect_cracks_ml(result.processed_image)

    # Generate report
    report_gen = ELReportGenerator()
    report_path = report_gen.generate_full_report("MODULE-001", result)
"""

from .image_processor import (
    ELImageProcessor,
    ProcessingResult,
    Defect,
    DefectType,
    DefectSeverity
)

from .defect_detector import (
    AdvancedDefectDetector,
    DefectStatistics,
    PowerLossEstimate,
    CrackFeatures
)

from .report_generator import (
    ELReportGenerator,
    IEC61215Criteria,
    TestResult
)

__all__ = [
    'ELImageProcessor',
    'ProcessingResult',
    'Defect',
    'DefectType',
    'DefectSeverity',
    'AdvancedDefectDetector',
    'DefectStatistics',
    'PowerLossEstimate',
    'CrackFeatures',
    'ELReportGenerator',
    'IEC61215Criteria',
    'TestResult'
]
