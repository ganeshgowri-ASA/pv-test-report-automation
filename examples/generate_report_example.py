#!/usr/bin/env python3
"""
Example script demonstrating the LaTeX report generation system.

This script shows how to:
1. Load or create test data
2. Configure branding
3. Generate a professional PDF report
4. Validate the report
5. Export LaTeX source for debugging

Usage:
    python examples/generate_report_example.py
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.export.latex.report_builder import ReportBuilder
from src.export.latex.pdf_compiler import LaTeXEngine
from data.sample.sample_test_data import create_sample_report, create_sample_branding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to demonstrate report generation."""

    print("=" * 70)
    print("PV Test Report Automation - LaTeX Report Generation Example")
    print("=" * 70)
    print()

    # Step 1: Create sample test data
    print("Step 1: Creating sample test data...")
    test_report = create_sample_report()

    print(f"  ✓ Report Number: {test_report.metadata.report_number}")
    print(f"  ✓ Module: {test_report.module_info.manufacturer} {test_report.module_info.model}")
    print(f"  ✓ Test Sequences: {len(test_report.test_sequences)}")
    print(f"  ✓ Overall Result: {test_report.get_overall_result()}")
    print()

    # Step 2: Validate report data
    print("Step 2: Validating report data...")
    report_builder = ReportBuilder(
        output_dir="output/reports",
        latex_engine=LaTeXEngine.PDFLATEX
    )

    validation_issues = report_builder.validate_report_data(test_report)

    if validation_issues:
        print("  ⚠ Validation warnings:")
        for issue in validation_issues:
            print(f"    - {issue}")
    else:
        print("  ✓ Report data is valid")
    print()

    # Step 3: Display report statistics
    print("Step 3: Report statistics...")
    stats = report_builder.generate_summary_statistics(test_report)

    print(f"  • Total tests: {stats['total']}")
    print(f"  • Passed: {stats['passed']}")
    print(f"  • Failed: {stats['failed']}")
    print(f"  • Pass rate: {stats['pass_rate']:.1f}%")
    print(f"  • Total measurements: {stats['total_measurements']}")
    print(f"  • Charts: {stats['num_charts']}")
    print()

    # Step 4: Apply custom branding
    print("Step 4: Applying custom branding...")
    branding = create_sample_branding()
    report_builder.branding = branding
    print(f"  ✓ Primary color: {branding.primary_color}")
    print(f"  ✓ Watermark: {branding.watermark_text}")
    print()

    # Step 5: Export LaTeX source (for debugging)
    print("Step 5: Exporting LaTeX source...")
    try:
        tex_path = report_builder.export_latex_source(
            test_report,
            output_filename="sample_report.tex"
        )
        print(f"  ✓ LaTeX source exported to: {tex_path}")
    except Exception as e:
        print(f"  ⚠ Failed to export LaTeX: {e}")
    print()

    # Step 6: Generate PDF report
    print("Step 6: Generating PDF report...")
    print("  This may take a minute as it compiles LaTeX to PDF...")

    try:
        # Check if LaTeX is installed
        available_engines = report_builder.pdf_compiler.get_available_engines()

        if not available_engines:
            print("  ⚠ No LaTeX engines found on this system!")
            print("  Please install LaTeX (TeX Live, MiKTeX, etc.) to generate PDFs.")
            print()
            print("  Installation instructions:")
            print("    • Ubuntu/Debian: sudo apt-get install texlive-full")
            print("    • macOS: brew install --cask mactex")
            print("    • Windows: Download MiKTeX from https://miktex.org/")
            print()
            print("  LaTeX source has been exported for manual compilation.")
            return

        print(f"  Available LaTeX engines: {[e.value for e in available_engines]}")

        # Generate the report
        pdf_path = report_builder.generate_report(
            test_report,
            output_filename="sample_report.pdf"
        )

        print(f"  ✓ PDF report generated successfully!")
        print(f"  ✓ Location: {pdf_path}")
        print()

        # Display file size
        pdf_size = Path(pdf_path).stat().st_size / 1024  # KB
        print(f"  • File size: {pdf_size:.1f} KB")

    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}", exc_info=True)
        print(f"  ✗ Error generating PDF: {e}")
        print()
        print("  Troubleshooting:")
        print("  1. Ensure LaTeX is installed and in your PATH")
        print("  2. Check the LaTeX source file for syntax errors")
        print("  3. Review the log file for compilation errors")
        print()
        return

    # Step 7: Summary
    print("=" * 70)
    print("Report Generation Complete!")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  • PDF Report: output/reports/sample_report.pdf")
    print(f"  • LaTeX Source: output/reports/sample_report.tex")
    print()
    print("Next steps:")
    print("  1. Open the PDF to review the report")
    print("  2. Customize the template in src/export/latex/templates/")
    print("  3. Modify branding in the BrandingConfig")
    print("  4. Add your own test data")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
