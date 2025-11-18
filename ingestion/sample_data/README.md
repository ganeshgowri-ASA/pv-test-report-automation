# Sample Data Files

This directory contains sample data files for testing the ingestion module.

## Files

### test_schedule.xml
MS Project XML format file containing a sample PV module testing schedule.

**Content:**
- Equipment calibration
- Thermal cycling test (TC 200)
- Humidity freeze test (HF 10)
- Damp heat test (DH 1000)
- Report generation and approval workflow

**Format:** MS Project XML (compatible with GanttIngestion)

### test_matrix.json
Sample Smartsheet data export containing IEC 61215 test requirements matrix.

**Content:**
- Test IDs and names
- IEC requirements mapping
- Test status tracking
- Assigned personnel
- Due dates and completion percentages
- Comments and attachments metadata

**Format:** JSON (SmartsheetData model compatible)

### test_procedure.vsdx
**Note:** Due to binary format complexity, actual .vsdx files should be created using Microsoft Visio.

For testing purposes, you can:
1. Create a simple flowchart in Visio with process steps
2. Export as .vsdx format
3. Place in this directory

Sample structure for test procedures:
- Start/End nodes (rounded rectangles)
- Process steps (rectangles)
- Decision points (diamonds)
- Connectors with arrows

## Usage in Tests

These sample files are used by `test_visio_gantt.py` to validate:
- File parsing capabilities
- Data extraction accuracy
- Model validation
- Error handling

## Creating Additional Samples

To add more sample data:

1. **Gantt/MS Project:**
   - Use MS Project or compatible software
   - Export to XML format
   - Include various task types, dependencies, and resources

2. **Smartsheet:**
   - Export sheet data using Smartsheet API
   - Save as JSON following SmartsheetData model structure

3. **Visio:**
   - Create diagrams in Microsoft Visio
   - Save as .vsdx format
   - Include various shape types and connectors
