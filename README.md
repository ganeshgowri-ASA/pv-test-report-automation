# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### 🖼️ Image Data Ingestion & Processing Engine

Comprehensive image processing capabilities for PV test lab automation:

- **Multi-format Support**: JPEG, PNG, BMP, TIFF, GIF, RAW camera formats (CR2, NEF, ARW)
- **EL Image Processing**: Electroluminescence analysis with crack detection, cell segmentation, and health scoring
- **Visual Inspection**: Automated detection of discoloration, bubbles, burn marks, and frame damage
- **OCR Capabilities**: Extract readings from multimeters, chamber displays, and data loggers
- **Quality Validation**: Automated blur detection, lighting uniformity, and resolution checking
- **Defect Detection**: Advanced algorithms for cracks, dark spots, inactive cells, and more
- **ISO 17025 Traceability**: SHA-256 hash generation for complete audit trails
- **Batch Processing**: Parallel processing for high-throughput scenarios

See [ingestion/README.md](ingestion/README.md) for detailed documentation.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (for OCR functionality)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
```

### Basic Usage

```python
from ingestion.el_image_processor import ELImageProcessor

# Process EL image
processor = ELImageProcessor()
result = processor.process("path/to/el_image.jpg")

print(f"Health Score: {result.overall_health_score:.1f}/100")
print(f"Defects Found: {len(result.ingestion_result.defects_detected)}")
```

## Project Structure

```
pv-test-report-automation/
├── ingestion/                  # Image processing engine
│   ├── image_processor.py     # Base image processor
│   ├── el_image_processor.py  # EL-specific processing
│   ├── visual_inspector.py    # Visual inspection
│   ├── ocr_image_reader.py    # OCR functionality
│   ├── defect_detector.py     # Defect detection algorithms
│   ├── image_validators.py    # Quality validation
│   ├── test_image_processor.py # Unit tests
│   └── sample_images/         # Sample images for testing
├── requirements.txt           # Python dependencies
├── LICENSE                    # License file
└── README.md                  # This file
```

## Testing

```bash
# Run unit tests
python -m pytest ingestion/test_image_processor.py -v

# Generate sample images
cd ingestion/sample_images
python generate_samples.py
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Standards Compliance

This system is designed to support compliance with:

- **IEC Standards**: 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
- **Quality Standards**: ISO 17025, ISO 9001
- **Accreditation**: NABL, ILAC, BIS

## Support

For issues, questions, or feature requests, please use the GitHub issue tracker.
