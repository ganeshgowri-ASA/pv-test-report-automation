# EL Testing Examples

This directory contains example scripts demonstrating the electroluminescence testing system.

## Examples

### 1. Simple Demo (`el_simple_demo.py`)

A simple example showing basic EL image processing and report generation.

```bash
python el_simple_demo.py path/to/el_image.tif
```

**Features demonstrated:**
- Image loading and preprocessing
- Cell segmentation
- Defect detection and classification
- Statistics calculation
- HTML report generation
- Statistics export

### 2. Batch Processing (`el_batch_processing.py`)

Comprehensive batch processing of multiple EL images with full customization options.

```bash
python el_batch_processing.py --input-dir ./images --output-dir ./results
```

**Options:**
- `--input-dir`: Directory containing EL images (required)
- `--output-dir`: Output directory (default: ./el_results)
- `--grid-rows`: Number of cell rows (default: 6)
- `--grid-cols`: Number of cell columns (default: 10)
- `--min-defect-area`: Minimum defect area in pixels (default: 50)
- `--edge-detection`: Edge detection method (canny/sobel/scharr/prewitt)
- `--power-loss-model`: Power loss model (linear/exponential/quadratic)
- `--use-gabor`: Use Gabor filters for crack detection (slower but more accurate)
- `--export-stats`: Export detailed statistics to JSON/CSV

**Example:**
```bash
python el_batch_processing.py \
    --input-dir ./test_images \
    --output-dir ./batch_results \
    --grid-rows 6 \
    --grid-cols 10 \
    --edge-detection canny \
    --use-gabor \
    --export-stats
```

**Features demonstrated:**
- Batch processing of multiple modules
- Advanced crack detection with Gabor filters
- Micro-crack identification
- Defect map generation
- Statistics export (JSON/CSV)
- Processing time tracking
- Summary report for all modules

### 3. Before/After Comparison (`el_comparison_demo.py`)

Compare EL images before and after stress testing to track defect progression.

```bash
python el_comparison_demo.py \
    --before initial.tif \
    --after post_stress.tif \
    --module-id MODULE-001
```

**Options:**
- `--before`: Path to initial/before EL image (required)
- `--after`: Path to post-stress/after EL image (required)
- `--module-id`: Module identifier (required)
- `--output-dir`: Output directory (default: ./el_comparison_results)
- `--grid-rows`: Number of cell rows (default: 6)
- `--grid-cols`: Number of cell columns (default: 10)

**Example:**
```bash
python el_comparison_demo.py \
    --before images/module_001_initial.tif \
    --after images/module_001_post_tc200.tif \
    --module-id MODULE-001 \
    --output-dir ./comparison_results
```

**Features demonstrated:**
- Before/after image comparison
- Defect progression tracking
- Power loss analysis
- IEC 61215 compliance checking
- Defect increase rate calculation
- Cell-level degradation tracking
- Comprehensive comparison report

## Sample Workflow

### Quick Test
```bash
# Process a single image
python el_simple_demo.py test_image.tif
```

### Production Batch Processing
```bash
# Process all modules from a test batch
python el_batch_processing.py \
    --input-dir /data/test_batch_2024_01/el_images \
    --output-dir /results/test_batch_2024_01 \
    --use-gabor \
    --export-stats
```

### Stress Test Analysis
```bash
# Compare before and after thermal cycling
python el_comparison_demo.py \
    --before /data/module_123/el_initial.tif \
    --after /data/module_123/el_post_tc200.tif \
    --module-id MODULE-123 \
    --output-dir /results/module_123_tc200
```

## Output Structure

Each example generates organized output:

```
output_directory/
├── MODULE-001_20240118_143022/
│   ├── report.html                 # Main HTML report
│   ├── images/
│   │   ├── initial_annotated.png   # Annotated EL image
│   │   ├── comparison_charts.png   # Comparison visualizations
│   │   ├── defect_charts.png       # Defect analysis charts
│   │   └── power_loss_chart.png    # Power loss analysis
│   └── statistics/
│       ├── statistics.json         # Full statistics (JSON)
│       ├── statistics.csv          # Summary statistics (CSV)
│       └── defects.json            # Detailed defect list
```

## Requirements

Ensure all dependencies are installed:

```bash
pip install -r ../requirements.txt
```

## Tips

1. **For best accuracy**: Use `--use-gabor` flag in batch processing (slower but more accurate crack detection)

2. **For large datasets**: Process in batches to manage memory usage

3. **For production use**: Always export statistics with `--export-stats` for traceability

4. **For comparison analysis**: Use consistent grid layout settings for before/after images

5. **For reporting**: Open the generated HTML reports in a modern web browser for best visualization

## Troubleshooting

### "No image files found"
- Check that your images have supported extensions (.tif, .tiff, .png, .jpg, .jpeg)
- Verify the input directory path is correct

### "Failed to load image"
- Ensure image files are not corrupted
- Try converting TIFF files to PNG if issues persist
- Check file permissions

### Memory issues with large images
- Process images individually rather than in large batches
- Reduce image resolution if appropriate
- Use a machine with more RAM

### Processing is slow
- Remove `--use-gabor` flag for faster processing (slightly less accurate)
- Reduce `--min-defect-area` threshold
- Process fewer images at once

## Support

For issues or questions:
1. Check the main README.md for detailed API documentation
2. Review the inline code documentation
3. Open an issue on the project repository
