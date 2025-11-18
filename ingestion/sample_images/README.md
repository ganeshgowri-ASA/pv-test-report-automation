# Sample Images for Testing

This directory contains sample images for testing the PV test report automation image processing engine.

## Sample Image Types

### Electroluminescence (EL) Images

- **el_normal.jpg** - Normal EL image of a healthy PV module
- **el_cracked.jpg** - EL image showing cell cracks
- **el_dark_spots.jpg** - EL image with dark spots/inactive areas
- **el_degraded.jpg** - EL image showing module degradation

### Visual Inspection Images

- **visual_normal.jpg** - Normal visual inspection of PV module
- **visual_discoloration.jpg** - Module showing browning/yellowing
- **visual_bubbles.jpg** - Module with bubbles/delamination
- **visual_burn_marks.jpg** - Module with burn marks
- **visual_junction_box.jpg** - Junction box damage

### Equipment Display Images

- **multimeter_reading.jpg** - Digital multimeter display
- **chamber_display.jpg** - Environmental chamber display
- **seven_segment.jpg** - Seven-segment LED display
- **data_logger.jpg** - Data logger screen capture

## Generating Sample Images

To generate synthetic sample images for testing, run:

```python
python generate_samples.py
```

This will create all sample images in this directory.

## Using Sample Images in Tests

```python
from ingestion.el_image_processor import ELImageProcessor

# Process EL image
processor = ELImageProcessor()
result = processor.process("ingestion/sample_images/el_normal.jpg")

print(f"Health Score: {result.overall_health_score}")
print(f"Defects Found: {len(result.ingestion_result.defects_detected)}")
```

## Notes

- Sample images are synthetic and generated programmatically
- For production testing, use actual PV module images
- Images are optimized for testing specific defect types
- All images meet minimum resolution requirements (1920x1080 for EL, 1280x720 for visual)
