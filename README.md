# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Electroluminescence (EL) Testing & Analysis Module

Complete EL image capture, processing, and defect detection system for photovoltaic modules.

### Features

#### Image Processing (`image_processor.py`)
- **Multi-format Image Loading**: Supports TIFF, PNG, and JPEG formats
- **Advanced Preprocessing**:
  - Gaussian blur and bilateral filtering for noise reduction
  - CLAHE (Contrast Limited Adaptive Histogram Equalization) for contrast enhancement
  - Edge-preserving denoising
- **Cell Segmentation**: Automatic grid-based cell segmentation with boundary detection
- **Defect Classification**:
  - Cracks (linear defects)
  - Broken cells (large area failures)
  - Inactive areas (dead zones)
  - Finger interruptions (busbar defects)
  - Micro-cracks (small linear defects)
  - Dark spots (point defects)
- **Defect Quantification**:
  - Area affected (pixels and percentage)
  - Location mapping with centroids
  - Severity classification (Critical, High, Medium, Low)
- **Before/After Comparison**: Compare initial and post-stress test images
- **Defect Progression Metrics**: Track defect evolution over time
- **Batch Processing**: Process multiple modules efficiently

#### Advanced Defect Detection (`defect_detector.py`)
- **ML-Based Crack Detection**:
  - Gabor filter bank for multi-orientation detection
  - Multiple edge detection algorithms (Canny, Sobel, Scharr, Prewitt)
  - Morphological enhancement and skeletonization
- **Micro-Crack Identification**:
  - Local adaptive thresholding
  - Enhanced edge detection with configurable sensitivity
  - Small feature extraction
- **Crack Feature Extraction**:
  - Length and width measurement
  - Orientation detection
  - Endpoint identification
  - Branching detection
  - Tortuosity calculation
- **Cell-Level Power Loss Estimation**:
  - Intensity-based analysis
  - Multiple estimation models (linear, exponential, quadratic)
  - Per-cell power degradation metrics
- **Defect Mapping**:
  - Heat map visualization overlaid on module layout
  - Severity-based color coding
  - Grid-based defect density analysis
- **Statistics Export**:
  - JSON and CSV formats
  - Comprehensive defect metrics
  - Power loss estimates per cell

#### Report Generation (`report_generator.py`)
- **HTML Test Reports**:
  - Professional styling with responsive design
  - Pass/fail status indicators
  - Score-based evaluation (0-100)
- **EL Image Visualization**:
  - Annotated images with defect highlights
  - Side-by-side before/after comparison
  - Color-coded defect types
- **Defect Summary Tables**:
  - Breakdown by type and severity
  - Statistical analysis
  - Critical cell identification
- **IEC 61215 MST Sequence Compliance**:
  - Automated pass/fail criteria evaluation
  - Maximum cell failures check
  - Inactive area threshold validation
  - Power loss limits verification
  - Defect progression monitoring
- **Comparison Charts**:
  - Defect count trends
  - Affected area analysis
  - Type distribution comparison
  - Progression rate visualization
- **Power Loss Charts**:
  - Per-cell power degradation
  - Normalized intensity distribution
  - Threshold indicators

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt
```

### Quick Start

```python
from src.tests.electroluminescence import (
    ELImageProcessor,
    AdvancedDefectDetector,
    ELReportGenerator
)

# 1. Process EL Image
processor = ELImageProcessor(
    cell_size=(156, 156),  # Cell size in mm
    grid_layout=(6, 10),   # 6 rows x 10 columns
    min_defect_area=50     # Minimum defect size in pixels
)

# Process single image
result = processor.process_image("path/to/el_image.tif")

print(f"Detected {len(result.defects)} defects in {result.metadata['total_cells']} cells")

# 2. Advanced Defect Detection
detector = AdvancedDefectDetector(
    min_crack_length=20,
    edge_detection_method='canny',
    power_loss_model='linear'
)

# Detect cracks with ML
crack_mask, crack_features = detector.detect_cracks_ml(
    result.processed_image,
    use_gabor_filters=True
)

print(f"Detected {len(crack_features)} crack structures")

# Detect micro-cracks
micro_cracks = detector.detect_micro_cracks(result.processed_image, sensitivity=0.8)

# Calculate statistics
statistics = detector.calculate_statistics(
    result.defects,
    result.segmented_cells,
    (6, 10)
)

# Generate defect map
defect_map = detector.generate_defect_map(
    result.original_image,
    result.defects,
    result.cell_boundaries,
    (6, 10)
)

# Export statistics
detector.export_statistics(statistics, "output/statistics.json", format='json')
detector.export_defects(result.defects, "output/defects.json")

# 3. Generate Report
report_gen = ELReportGenerator(
    output_dir="./el_reports",
    dpi=150
)

# Generate full HTML report
report_path = report_gen.generate_full_report(
    module_id="MODULE-001",
    initial_result=result,
    statistics=statistics
)

print(f"Report generated: {report_path}")
```

### Batch Processing Example

```python
from src.tests.electroluminescence import ELImageProcessor

processor = ELImageProcessor()

# Process multiple images
image_paths = [
    "images/module_001.tif",
    "images/module_002.tif",
    "images/module_003.tif"
]

results = processor.batch_process(image_paths)

for idx, result in enumerate(results):
    print(f"Module {idx+1}: {len(result.defects)} defects detected")
```

### Before/After Stress Test Comparison

```python
from src.tests.electroluminescence import ELImageProcessor, ELReportGenerator

processor = ELImageProcessor()

# Process initial and post-stress images
initial_result = processor.process_image("images/module_initial.tif")
post_stress_result = processor.process_image("images/module_post_stress.tif")

# Compare images
comparison_data = processor.compare_images(
    initial_result.original_image,
    post_stress_result.original_image,
    initial_result.defects,
    post_stress_result.defects
)

# Calculate progression metrics
progression = processor.calculate_defect_progression(
    initial_result.defects,
    post_stress_result.defects
)

print(f"New defects: {comparison_data['new_defects']}")
print(f"Defect increase rate: {comparison_data['defect_increase_rate']:.1f}%")
print(f"Area increase: {comparison_data['area_increase']:.2f}%")

# Generate comprehensive report
report_gen = ELReportGenerator()
report_path = report_gen.generate_full_report(
    module_id="MODULE-001",
    initial_result=initial_result,
    post_stress_result=post_stress_result,
    comparison_data=comparison_data
)
```

### Defect Types

The system classifies the following defect types:

- **Crack**: Linear defects across cells (vertical orientation)
- **Finger Interruption**: Linear defects in busbars (horizontal orientation)
- **Broken Cell**: Large area failures (>10,000 pixels)
- **Inactive Area**: Large circular dark regions
- **Micro-Crack**: Small linear defects (<200 pixels)
- **Dark Spot**: Point defects or unknown anomalies

### Severity Levels

Defects are classified into four severity levels based on affected area:

- **Critical**: >10% of cell area
- **High**: 5-10% of cell area
- **Medium**: 2-5% of cell area
- **Low**: <2% of cell area

### IEC 61215 Compliance

The report generator automatically evaluates modules against IEC 61215 MST sequence criteria:

- Maximum cell failures: 0 (default)
- Maximum inactive area: 5%
- Maximum power loss: 5%
- Maximum defect progression: 10%

These thresholds are configurable:

```python
from src.tests.electroluminescence import ELReportGenerator, IEC61215Criteria

criteria = IEC61215Criteria(
    max_crack_length_mm=50.0,
    max_inactive_area_percent=5.0,
    max_cell_failures=0,
    max_power_loss_percent=5.0,
    max_defect_progression_percent=10.0
)

report_gen = ELReportGenerator(criteria=criteria)
```

### Output Files

The system generates the following outputs:

1. **HTML Report** (`report.html`): Comprehensive test report with all visualizations
2. **Annotated Images**: EL images with defect highlights
3. **Comparison Charts**: Before/after analysis visualizations
4. **Defect Charts**: Type and severity distribution
5. **Power Loss Charts**: Cell-level degradation analysis
6. **Statistics Files**: JSON/CSV exports of defect data

### Architecture

```
src/tests/electroluminescence/
├── __init__.py              # Package initialization
├── image_processor.py       # Core image processing
├── defect_detector.py       # Advanced defect detection
└── report_generator.py      # Report generation
```

### Technology Stack

- **OpenCV**: Image processing and computer vision
- **NumPy**: Numerical computations
- **Pillow**: Image I/O and format support
- **scikit-image**: Advanced image processing algorithms
- **SciPy**: Scientific computing utilities
- **Matplotlib**: Visualization and charting

### Performance

- Single image processing: ~2-5 seconds (depending on resolution)
- Batch processing: Supports parallel processing of multiple modules
- Memory efficient: Streams large TIFF files
- Scalable: Handles modules with up to 120 cells (6x20 grid)

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src/tests/electroluminescence tests/
```

### License

MIT License - See LICENSE file for details

### Authors

PV Test Automation System Development Team

### Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.
