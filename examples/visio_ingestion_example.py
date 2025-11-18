"""
Example: Visio Diagram Ingestion

This example demonstrates how to ingest Visio (.vsdx) files and extract
diagram shapes, connections, and metadata.
"""

from pathlib import Path

from src.ingestion.visio import VisioIngestionModule
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger(log_file="logs/visio_ingestion.log")
logger = get_logger(__name__)


def main():
    """Main function demonstrating Visio ingestion."""

    # Initialize the Visio ingestion module
    visio_module = VisioIngestionModule()

    # Path to your Visio file
    visio_file_path = "data/test_procedure_flow.vsdx"

    try:
        # Validate the file first
        file_path = Path(visio_file_path)
        visio_module.validate_file(file_path)
        logger.info(f"File validation successful: {visio_file_path}")

        # Extract metadata without full ingestion
        metadata = visio_module.extract_metadata(file_path)
        logger.info(f"Metadata: {metadata}")

        # Perform full ingestion
        logger.info("Starting Visio ingestion...")
        result = visio_module.ingest(file_path)

        # Check ingestion status
        logger.info(f"Ingestion status: {result.status.value}")
        logger.info(f"Diagram name: {result.diagram_name}")
        logger.info(f"Total pages: {len(result.pages)}")
        logger.info(f"Total shapes: {len(result.shapes)}")

        # Process each page
        for page in result.pages:
            logger.info(f"\nPage: {page.page_name}")
            logger.info(f"  Dimensions: {page.page_width} x {page.page_height}")
            logger.info(f"  Shapes: {len(page.shapes)}")

            # Process shapes on the page
            for shape in page.shapes:
                logger.info(f"    - {shape.name} ({shape.shape_type.value})")
                if shape.text:
                    logger.info(f"      Text: {shape.text}")
                if shape.connected_to:
                    logger.info(f"      Connected to: {shape.connected_to}")

        # Save SVG export
        svg_output_path = Path("output") / f"{result.diagram_name}.svg"
        svg_output_path.parent.mkdir(exist_ok=True)
        svg_output_path.write_text(result.svg_export)
        logger.info(f"\nSVG export saved to: {svg_output_path}")

        # Report errors if any
        if result.errors:
            logger.warning(f"Errors encountered: {len(result.errors)}")
            for error in result.errors:
                logger.warning(f"  - {error}")

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
