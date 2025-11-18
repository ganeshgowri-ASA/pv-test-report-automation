# PV Test Report Automation - Image Processing Engine

Comprehensive image data ingestion and processing engine for PV (photovoltaic) test lab automation.

## Features

### 🖼️ Image Format Support
- **Standard Formats**: JPEG, PNG, BMP, TIFF, GIF
- **RAW Camera Formats**: CR2, NEF, ARW, DNG
- **Multi-page TIFF**: Full support for multi-page TIFF handling
- **EXIF Metadata**: Extraction of date, camera model, GPS coordinates
- **Quality Validation**: Resolution, blur, lighting, contrast checks

### ⚡ Electroluminescence (EL) Image Processing
- Grayscale conversion and normalization
- Automated cell segmentation (identify individual solar cells)
- Crack detection and classification
  - Finger interruption vs. cell cracks
  - Severity scoring (minor, moderate, severe)
- Dark spot and inactive area detection
- Inactive cell identification
- Overall module health scoring (0-100)
- Before/after degradation comparison

### 👁️ Visual Inspection Processing
- Automatic color correction and white balance
- Discoloration detection (browning, yellowing)
- Bubble and delamination detection
- Burn mark identification
- Junction box damage assessment
- Frame and edge damage detection
- Image enhancement for better visibility

### 📊 I-V Curve Chart Extraction
- Extract I-V curve plots from images
- Digitize curves using computer vision
- Extract key parameters (Voc, Isc, Vmp, Imp)
- Calculate fill factor and Pmax
- Multi-curve comparison support

### 🔍 Image Quality Validation
- Blur detection using Laplacian variance
- Lighting uniformity checking
- Resolution requirements enforcement
- Contrast and brightness validation
- Motion blur detection
- Color calibration verification

### 🔤 OCR for Equipment Displays
- Digital multimeter reading extraction
- Environmental chamber display parsing (temp, humidity)
- Seven-segment LED display reading
- Data logger screen capture processing
- Confidence scoring for OCR accuracy
- Automatic numeric value extraction

### 📝 Image Annotation & Overlay
- Defect marking and labeling
- Measurement scales and rulers
- Timestamp and metadata watermarking
- Comparison annotations (pass/fail markers)
- Health score overlays

### ⚙️ Batch Processing
- Parallel image processing
- Time-series image sequence analysis
- Batch quality validation
- Progress tracking for large batches

## Installation

### System Requirements

**Tesseract OCR** (required for OCR functionality):

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Image Processing

```python
from ingestion.image_processor import ImageProcessor

# Initialize processor
processor = ImageProcessor()

# Process image with quality validation
result = processor.process_image(
    "path/to/image.jpg",
    validate_quality=True
)

print(f"File hash (SHA-256): {result.file_hash}")
print(f"Quality passed: {result.quality_passed}")
if not result.quality_passed:
    print(f"Quality errors: {result.quality_metrics.quality_errors}")
```

### EL Image Processing

```python
from ingestion.el_image_processor import ELImageProcessor

# Initialize EL processor
processor = ELImageProcessor()

# Process EL image
result = processor.process(
    "path/to/el_image.jpg",
    detect_defects=True,
    segment_cells=True
)

# View results
print(f"Cells detected: {result.cell_count}")
print(f"Cracks found: {len(result.cracks_detected)}")
print(f"Dark spots found: {len(result.dark_spots_detected)}")
print(f"Inactive cells: {len(result.inactive_cells)}")
print(f"Health score: {result.overall_health_score:.1f}/100")

# Defect details
for defect in result.cracks_detected:
    print(f"Crack at {defect.location}, severity: {defect.severity}, confidence: {defect.confidence:.2f}")
```

### Visual Inspection

```python
from ingestion.visual_inspector import VisualInspector

# Initialize visual inspector
inspector = VisualInspector()

# Process visual inspection image
result = inspector.process(
    "path/to/visual_image.jpg",
    detect_defects=True,
    apply_color_correction=True
)

# View results
print(f"Total defects: {len(result.ingestion_result.defects_detected)}")
print(f"Discoloration areas: {len(result.discoloration_areas)}")
print(f"Bubbles: {len(result.bubbles_detected)}")
print(f"Burn marks: {len(result.burn_marks)}")
print(f"Frame damage: {len(result.frame_damage)}")

if result.junction_box_damage:
    print(f"Junction box damage detected: {result.junction_box_damage.severity}")
```

### OCR for Equipment Displays

```python
from ingestion.ocr_image_reader import OCRImageReader
import cv2

# Initialize OCR reader
reader = OCRImageReader()

# Read multimeter display
image = cv2.imread("path/to/multimeter.jpg")
result = reader.read_multimeter(image)

print(f"OCR Text: {result.text}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Extracted values: {result.extracted_values}")

# Read chamber display
result = reader.read_chamber_display(image)
if 'temperature' in result.extracted_values:
    print(f"Temperature: {result.extracted_values['temperature']}°C")
if 'humidity' in result.extracted_values:
    print(f"Humidity: {result.extracted_values['humidity']}%")
```

### Defect Detection Only

```python
from ingestion.defect_detector import detect_defects
import cv2

# Load image
image = cv2.imread("path/to/image.jpg")

# Detect all defect types
defects = detect_defects(
    image,
    defect_types=["crack", "dark_spot", "discoloration", "bubble"]
)

# Process defects
for defect in defects:
    print(f"{defect.type}: {defect.severity} at {defect.location}")
```

### Degradation Analysis

```python
from ingestion.el_image_processor import ELImageProcessor

processor = ELImageProcessor()

# Compare before/after images
degradation = processor.compare_degradation(
    before_image="module_before.jpg",
    after_image="module_after.jpg"
)

print(f"Health change: {degradation['health_score_change']:.1f}")
print(f"New cracks: {degradation['new_cracks']}")
print(f"New dark spots: {degradation['new_dark_spots']}")
print(f"New inactive cells: {degradation['new_inactive_cells']}")
print(f"Degraded: {degradation['degraded']}")
```

### Create Annotated Images

```python
from ingestion.el_image_processor import ELImageProcessor, create_annotated_image
import cv2

# Process image
processor = ELImageProcessor()
result = processor.process("el_image.jpg")

# Create annotated version
original = cv2.imread("el_image.jpg")
annotated = create_annotated_image(
    original,
    result,
    show_cells=True,
    show_defects=True
)

# Save annotated image
cv2.imwrite("el_image_annotated.jpg", annotated)
```

## Architecture

### Module Structure

```
ingestion/
├── __init__.py                 # Models, exceptions, exports
├── image_processor.py          # Base image processor
├── image_validators.py         # Quality validation
├── defect_detector.py          # Defect detection algorithms
├── el_image_processor.py       # EL-specific processing
├── visual_inspector.py         # Visual inspection
├── ocr_image_reader.py         # OCR functionality
├── test_image_processor.py     # Unit tests
└── sample_images/              # Sample images for testing
    ├── README.md
    ├── generate_samples.py
    └── *.jpg                   # Generated sample images
```

### Data Models

All results use Pydantic models for type safety and validation:

- **`Defect`**: Individual defect representation
- **`ImageMetadata`**: EXIF and file metadata
- **`QualityMetrics`**: Image quality assessment
- **`OCRResult`**: OCR extraction results
- **`ImageIngestionResult`**: Base ingestion result
- **`ELImageResult`**: EL-specific results
- **`VisualInspectionResult`**: Visual inspection results
- **`IVCurveData`**: I-V curve extraction data

### Custom Exceptions

- **`ImageProcessingError`**: Base exception
- **`ImageFormatError`**: Unsupported/corrupted format
- **`ImageQualityError`**: Quality validation failure
- **`MetadataExtractionError`**: Metadata extraction failure
- **`DefectDetectionError`**: Defect detection failure
- **`OCRError`**: OCR processing failure

## Quality Thresholds

Default quality validation thresholds:

```python
# Blur detection
MIN_BLUR_THRESHOLD = 100.0  # Laplacian variance

# Resolution
MIN_RESOLUTION_EL = (1920, 1080)
MIN_RESOLUTION_VISUAL = (1280, 720)

# Lighting
MIN_LIGHTING_UNIFORMITY = 0.7  # 0-1 scale

# Contrast
MIN_CONTRAST = 20.0  # RMS contrast

# Brightness
BRIGHTNESS_RANGE = (30.0, 225.0)
```

### Custom Thresholds

```python
from ingestion.image_validators import ImageValidator
from ingestion.image_processor import ImageProcessor

# Create validator with custom thresholds
validator = ImageValidator(
    min_blur_threshold=120.0,
    min_resolution=(2048, 1536),
    min_lighting_uniformity=0.8,
    min_contrast=25.0,
    brightness_range=(40.0, 215.0)
)

# Use custom validator
processor = ImageProcessor(validator=validator)
```

## ISO 17025 Traceability

All processed images include SHA-256 hash for traceability:

```python
result = processor.process_image("image.jpg")
print(f"Traceable hash: {result.file_hash}")

# Hash is deterministic - same file always produces same hash
# Store hash in database for complete audit trail
```

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest ingestion/test_image_processor.py -v

# Run with coverage
python -m pytest ingestion/test_image_processor.py --cov=ingestion --cov-report=html

# Run specific test class
python -m pytest ingestion/test_image_processor.py::TestELImageProcessor -v
```

### Generate Sample Images

```bash
cd ingestion/sample_images
python generate_samples.py
```

## Performance Considerations

### Memory Management

For large images or batch processing:

```python
# Process in batches
import gc

for image_path in image_paths:
    result = processor.process_image(image_path)
    # Process result
    gc.collect()  # Force garbage collection
```

### Parallel Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
from ingestion.el_image_processor import ELImageProcessor

processor = ELImageProcessor()

def process_single(image_path):
    return processor.process(image_path)

# Process multiple images in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_single, image_paths))
```

## Advanced Usage

### Custom Defect Detectors

```python
from ingestion.defect_detector import DefectDetector, Defect
import cv2
import numpy as np

class CustomDefectDetector(DefectDetector):
    def detect_defects(self, image: np.ndarray) -> list[Defect]:
        # Implement custom detection logic
        defects = []
        # ... detection code ...
        return defects

# Use custom detector
detector = CustomDefectDetector()
defects = detector.detect_defects(image)
```

### Region of Interest Processing

```python
from ingestion.ocr_image_reader import OCRImageReader
import cv2

reader = OCRImageReader()
image = cv2.imread("display.jpg")

# Process specific region only
roi = (100, 100, 400, 200)  # x, y, w, h
result = reader.read_text(image, region=roi)
```

## Troubleshooting

### Tesseract Not Found

```python
from ingestion.ocr_image_reader import OCRImageReader

# Specify tesseract path explicitly
reader = OCRImageReader(tesseract_cmd='/usr/local/bin/tesseract')
```

### Low OCR Accuracy

1. Enable preprocessing:
```python
reader = OCRImageReader(preprocess=True)
```

2. Use specialized readers:
```python
# For seven-segment displays
result = reader.read_seven_segment_display(image)

# For multimeters
result = reader.read_multimeter(image)
```

### Memory Issues with Large Images

Resize before processing:

```python
import cv2

# Load and resize
image = cv2.imread("large_image.jpg")
resized = cv2.resize(image, (1920, 1080))

# Process resized image
result = processor.process_image_from_array(resized)
```

## Contributing

1. Add new defect detectors in `defect_detector.py`
2. Extend image processors in `el_image_processor.py` or `visual_inspector.py`
3. Add unit tests in `test_image_processor.py`
4. Update this README with new features

## License

See LICENSE file in repository root.

## Support

For issues and feature requests, please use the GitHub issue tracker.
