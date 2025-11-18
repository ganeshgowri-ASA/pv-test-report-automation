"""
Example: Smartsheet API Ingestion

This example demonstrates how to ingest data from Smartsheet via API,
including sheets, columns, rows, and metadata.
"""

import json
import os
from pathlib import Path

from src.ingestion.smartsheet import SmartsheetIngestionModule
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger(log_file="logs/smartsheet_ingestion.log")
logger = get_logger(__name__)


def main():
    """Main function demonstrating Smartsheet ingestion."""

    # Check for API key
    api_key = os.getenv("SMARTSHEET_API_KEY")
    if not api_key:
        logger.error("SMARTSHEET_API_KEY environment variable not set")
        logger.info("Please set your Smartsheet API key:")
        logger.info("  export SMARTSHEET_API_KEY='your_api_key_here'")
        return

    # Initialize the Smartsheet ingestion module
    smartsheet_module = SmartsheetIngestionModule()

    try:
        # Example 1: List available workspaces
        logger.info("Listing available workspaces...")
        workspaces = smartsheet_module.list_workspaces()
        logger.info(f"Found {len(workspaces)} workspaces:")
        for ws in workspaces:
            logger.info(f"  - {ws['name']} (ID: {ws['id']})")

        # Example 2: List sheets in a workspace
        if workspaces:
            workspace_id = workspaces[0]['id']
            logger.info(f"\nListing sheets in workspace '{workspaces[0]['name']}'...")
            sheets = smartsheet_module.list_sheets_in_workspace(workspace_id)
            logger.info(f"Found {len(sheets)} sheets:")
            for sheet in sheets:
                logger.info(f"  - {sheet['name']} (ID: {sheet['id']})")

        # Example 3: Ingest a specific sheet
        # Replace with your actual sheet ID or URL
        sheet_id = "YOUR_SHEET_ID_HERE"  # or use sheet URL

        # You can also use the sheet ID from the list above
        if workspaces and sheets:
            sheet_id = sheets[0]['id']
            logger.info(f"\nIngesting sheet: {sheets[0]['name']}")

        # Extract metadata first
        logger.info("Extracting metadata...")
        metadata = smartsheet_module.extract_metadata(sheet_id)
        logger.info(f"Sheet metadata: {metadata}")

        # Perform full ingestion
        logger.info("Starting Smartsheet ingestion...")
        result = smartsheet_module.ingest(
            sheet_id,
            include_attachments=False,  # Set to True if you need attachments
            include_discussions=False   # Set to True if you need comments
        )

        # Check ingestion status
        logger.info(f"Ingestion status: {result.status.value}")
        logger.info(f"Sheet name: {result.sheet_name}")
        logger.info(f"Sheet ID: {result.sheet_id}")
        logger.info(f"Total rows: {result.total_rows}")
        logger.info(f"Total columns: {result.total_columns}")

        # Display column structure
        logger.info("\nColumn Structure:")
        for column in result.columns:
            primary_marker = " (PRIMARY)" if column.primary else ""
            logger.info(f"  - {column.title}: {column.column_type}{primary_marker}")
            if column.options:
                logger.info(f"    Options: {', '.join(column.options)}")

        # Display row data
        logger.info(f"\nRow Data (showing first 10 rows):")
        for row in result.rows[:10]:
            logger.info(f"  Row {row.row_number}:")

            # Create a mapping of column_id to column title
            column_map = {col.column_id: col.title for col in result.columns}

            for cell in row.cells:
                column_title = column_map.get(cell.column_id, cell.column_id)
                value = cell.display_value or cell.value
                logger.info(f"    {column_title}: {value}")

        # Analyze hierarchical structure
        logger.info("\nHierarchical Structure:")
        root_rows = [row for row in result.rows if row.parent_id is None]
        logger.info(f"  Root-level rows: {len(root_rows)}")

        child_rows = [row for row in result.rows if row.parent_id is not None]
        logger.info(f"  Child rows: {len(child_rows)}")

        # Save detailed report as JSON
        output_path = Path("output") / f"{result.sheet_name.replace(' ', '_')}_smartsheet.json"
        output_path.parent.mkdir(exist_ok=True)

        # Build column map for easier reading
        column_titles = {col.column_id: col.title for col in result.columns}

        report = {
            'sheet_name': result.sheet_name,
            'sheet_id': result.sheet_id,
            'total_rows': result.total_rows,
            'total_columns': result.total_columns,
            'columns': [
                {
                    'title': col.title,
                    'type': col.column_type,
                    'primary': col.primary,
                    'options': col.options
                }
                for col in result.columns
            ],
            'rows': [
                {
                    'row_number': row.row_number,
                    'parent_id': row.parent_id,
                    'data': {
                        column_titles.get(cell.column_id, cell.column_id):
                            cell.display_value or cell.value
                        for cell in row.cells
                    }
                }
                for row in result.rows
            ],
            'metadata': result.metadata
        }

        output_path.write_text(json.dumps(report, indent=2, default=str))
        logger.info(f"\nDetailed report saved to: {output_path}")

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
