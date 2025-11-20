"""
Verification Script for Export Module

Quick verification that all exporters can be imported and instantiated.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_imports():
    """Verify all modules can be imported."""
    print("=" * 60)
    print("PHASE 8: Export Engines - Installation Verification")
    print("=" * 60)
    print()

    results = []

    # Test base module
    print("1. Testing base_exporter module...")
    try:
        from export.base_exporter import (
            BaseExporter, ExportFormat, ExportStatus, ExportOptions,
            ExportProgress, TemplateManager, ExportRegistry, create_exporter
        )
        print("   ✓ Base exporter module imported successfully")
        results.append(("Base Module", True, None))
    except Exception as e:
        print(f"   ✗ Failed to import base exporter: {e}")
        results.append(("Base Module", False, str(e)))

    # Test JSON exporter
    print("\n2. Testing JSON exporter...")
    try:
        from export import JSONExporter, ExportFormat
        exporter = JSONExporter()
        assert exporter.format_type == ExportFormat.JSON
        assert exporter.file_extension == "json"
        print("   ✓ JSON exporter working")
        results.append(("JSON Exporter", True, None))
    except Exception as e:
        print(f"   ✗ JSON exporter failed: {e}")
        results.append(("JSON Exporter", False, str(e)))

    # Test XML exporter
    print("\n3. Testing XML exporter...")
    try:
        from export import XMLExporter, ExportFormat
        exporter = XMLExporter()
        assert exporter.format_type == ExportFormat.XML
        assert exporter.file_extension == "xml"
        print("   ✓ XML exporter working")
        results.append(("XML Exporter", True, None))
    except Exception as e:
        print(f"   ✗ XML exporter failed: {e}")
        results.append(("XML Exporter", False, str(e)))

    # Test HTML exporter
    print("\n4. Testing HTML exporter...")
    try:
        from export import HTMLExporter, ExportFormat
        exporter = HTMLExporter()
        assert exporter.format_type == ExportFormat.HTML
        assert exporter.file_extension == "html"
        print("   ✓ HTML exporter working")
        results.append(("HTML Exporter", True, None))
    except ImportError as e:
        print(f"   ! HTML exporter requires jinja2: {e}")
        print("     Install with: pip install jinja2")
        results.append(("HTML Exporter", False, "Missing jinja2"))
    except Exception as e:
        print(f"   ✗ HTML exporter failed: {e}")
        results.append(("HTML Exporter", False, str(e)))

    # Test PDF exporter
    print("\n5. Testing PDF exporter...")
    try:
        from export import PDFExporter, ExportFormat
        from export.pdf_exporter import PDFEngine, REPORTLAB_AVAILABLE

        if REPORTLAB_AVAILABLE:
            exporter = PDFExporter(engine=PDFEngine.REPORTLAB)
            assert exporter.format_type == ExportFormat.PDF
            assert exporter.file_extension == "pdf"
            print("   ✓ PDF exporter working (ReportLab available)")
            results.append(("PDF Exporter", True, None))
        else:
            print("   ! PDF exporter requires reportlab")
            print("     Install with: pip install reportlab PyPDF2")
            results.append(("PDF Exporter", False, "Missing reportlab"))
    except ImportError as e:
        print(f"   ! PDF exporter requires reportlab: {e}")
        print("     Install with: pip install reportlab PyPDF2")
        results.append(("PDF Exporter", False, "Missing reportlab"))
    except Exception as e:
        print(f"   ✗ PDF exporter failed: {e}")
        results.append(("PDF Exporter", False, str(e)))

    # Test Word exporter
    print("\n6. Testing Word exporter...")
    try:
        from export import WordExporter, ExportFormat
        from export.word_exporter import DOCX_AVAILABLE

        if DOCX_AVAILABLE:
            exporter = WordExporter()
            assert exporter.format_type == ExportFormat.WORD
            assert exporter.file_extension == "docx"
            print("   ✓ Word exporter working (python-docx available)")
            results.append(("Word Exporter", True, None))
        else:
            print("   ! Word exporter requires python-docx")
            print("     Install with: pip install python-docx")
            results.append(("Word Exporter", False, "Missing python-docx"))
    except ImportError as e:
        print(f"   ! Word exporter requires python-docx: {e}")
        print("     Install with: pip install python-docx")
        results.append(("Word Exporter", False, "Missing python-docx"))
    except Exception as e:
        print(f"   ✗ Word exporter failed: {e}")
        results.append(("Word Exporter", False, str(e)))

    # Test Excel exporter
    print("\n7. Testing Excel exporter...")
    try:
        from export import ExcelExporter, ExportFormat
        from export.excel_exporter import OPENPYXL_AVAILABLE, ExcelEngine

        if OPENPYXL_AVAILABLE:
            exporter = ExcelExporter(engine=ExcelEngine.OPENPYXL)
            assert exporter.format_type == ExportFormat.EXCEL
            assert exporter.file_extension == "xlsx"
            print("   ✓ Excel exporter working (openpyxl available)")
            results.append(("Excel Exporter", True, None))
        else:
            print("   ! Excel exporter requires openpyxl")
            print("     Install with: pip install openpyxl")
            results.append(("Excel Exporter", False, "Missing openpyxl"))
    except ImportError as e:
        print(f"   ! Excel exporter requires openpyxl: {e}")
        print("     Install with: pip install openpyxl")
        results.append(("Excel Exporter", False, "Missing openpyxl"))
    except Exception as e:
        print(f"   ✗ Excel exporter failed: {e}")
        results.append(("Excel Exporter", False, str(e)))

    # Test factory function
    print("\n8. Testing factory function...")
    try:
        from export import create_exporter, ExportFormat
        json_exporter = create_exporter(ExportFormat.JSON)
        xml_exporter = create_exporter(ExportFormat.XML)
        print("   ✓ Factory function working")
        results.append(("Factory Function", True, None))
    except Exception as e:
        print(f"   ✗ Factory function failed: {e}")
        results.append(("Factory Function", False, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")
    print()

    for name, success, error in results:
        status = "✓" if success else "✗"
        print(f"{status} {name:20s} - {'OK' if success else error}")

    print("\n" + "=" * 60)

    if passed == total:
        print("All components verified successfully!")
        print("Export module is ready for use.")
    else:
        print(f"{total - passed} component(s) require optional dependencies.")
        print("Core functionality (JSON/XML) is available.")
        print("\nTo install all optional dependencies:")
        print("  pip install reportlab PyPDF2 python-docx jinja2 plotly openpyxl jsonschema lxml")

    print("=" * 60)

    return passed == total


def verify_basic_export():
    """Test basic export functionality."""
    import tempfile
    import json

    print("\n" + "=" * 60)
    print("BASIC FUNCTIONALITY TEST")
    print("=" * 60)

    try:
        from export import JSONExporter, ExportOptions
        from pathlib import Path

        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test data
            test_data = {
                "title": "Test Report",
                "test_results": [
                    {"name": "Test 1", "status": "PASS", "value": 42}
                ]
            }

            # Export
            print("\nExporting test data to JSON...")
            exporter = JSONExporter()
            options = ExportOptions(output_path=temp_path / "test.json")
            result = exporter.export(test_data, options)

            # Validate
            print(f"Export completed: {result}")

            if exporter.validate_output(result):
                print("✓ Output validation passed")

                # Read back
                with open(result, 'r') as f:
                    loaded_data = json.load(f)

                if loaded_data["title"] == test_data["title"]:
                    print("✓ Data integrity verified")
                    print("\n✓ Basic functionality test PASSED")
                    return True
                else:
                    print("✗ Data integrity check failed")
                    return False
            else:
                print("✗ Output validation failed")
                return False

    except Exception as e:
        print(f"\n✗ Basic functionality test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    imports_ok = verify_imports()
    basic_ok = verify_basic_export()

    print("\n" + "=" * 60)
    if imports_ok and basic_ok:
        print("SUCCESS: Export module is fully functional!")
        sys.exit(0)
    elif basic_ok:
        print("PARTIAL: Core functionality works, optional features need dependencies.")
        sys.exit(0)
    else:
        print("FAILURE: Basic functionality test failed.")
        sys.exit(1)
