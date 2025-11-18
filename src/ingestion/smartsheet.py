"""
Smartsheet API ingestion module.

Integrates with Smartsheet API to extract sheet data, columns, rows, and metadata.
Supports hierarchical row structures and custom column types.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import smartsheet
    from smartsheet.exceptions import ApiError
except ImportError:
    raise ImportError(
        "smartsheet-python-sdk is required for Smartsheet ingestion. "
        "Install with: pip install smartsheet-python-sdk"
    )

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError, SmartsheetAPIError, SmartsheetIngestionError
from src.core.models import (
    IngestionStatus,
    SmartsheetCell,
    SmartsheetColumn,
    SmartsheetIngestionResult,
    SmartsheetRow,
)
from src.ingestion.base import BaseIngestionModule


class SmartsheetIngestionModule(BaseIngestionModule[SmartsheetIngestionResult]):
    """
    Ingestion module for Smartsheet data via API.

    Extracts:
    - Sheet structure (columns and types)
    - Row data with hierarchical relationships
    - Cell values and formatting
    - Sheet metadata (owner, permissions, etc.)
    - Attachments and comments (optional)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Smartsheet ingestion module."""
        super().__init__(config)
        self._client: Optional[smartsheet.Smartsheet] = None

    def _validate_configuration(self) -> None:
        """Validate Smartsheet-specific configuration."""
        if not self.settings.smartsheet_api_key:
            raise ConfigurationError(
                "Smartsheet API key is required. Set SMARTSHEET_API_KEY environment variable."
            )

    def _get_client(self) -> smartsheet.Smartsheet:
        """
        Get or create Smartsheet API client.

        Returns:
            Smartsheet client instance
        """
        if self._client is None:
            try:
                self._client = smartsheet.Smartsheet(self.settings.smartsheet_api_key)
                # Disable auto-retry to handle errors ourselves
                self._client.errors_as_exceptions(True)
            except Exception as e:
                raise SmartsheetAPIError(f"Failed to initialize Smartsheet client: {str(e)}")

        return self._client

    def _map_column_type(self, column_type: str) -> str:
        """
        Map Smartsheet column type to standard format.

        Args:
            column_type: Smartsheet column type

        Returns:
            Standardized column type string
        """
        # Smartsheet column types: TEXT_NUMBER, DATE, DATETIME, CONTACT_LIST,
        # CHECKBOX, PICKLIST, DURATION, PREDECESSOR, ABSTRACT_DATETIME
        type_mapping = {
            'TEXT_NUMBER': 'TEXT_NUMBER',
            'DATE': 'DATE',
            'DATETIME': 'DATETIME',
            'CONTACT_LIST': 'CONTACT',
            'CHECKBOX': 'CHECKBOX',
            'PICKLIST': 'DROPDOWN',
            'DURATION': 'DURATION',
            'PREDECESSOR': 'PREDECESSOR',
            'ABSTRACT_DATETIME': 'DATETIME',
        }

        return type_mapping.get(column_type, column_type)

    def _process_column(self, column: Any) -> SmartsheetColumn:
        """
        Process a Smartsheet column.

        Args:
            column: Smartsheet column object

        Returns:
            SmartsheetColumn model
        """
        column_id = str(column.id)
        title = str(column.title)
        column_type = self._map_column_type(column.type)
        primary = bool(column.primary) if hasattr(column, 'primary') else False

        # Extract dropdown options if available
        options = []
        if hasattr(column, 'options') and column.options:
            options = [str(opt) for opt in column.options]

        return SmartsheetColumn(
            column_id=column_id,
            title=title,
            column_type=column_type,
            primary=primary,
            options=options
        )

    def _process_cell(self, cell: Any) -> SmartsheetCell:
        """
        Process a Smartsheet cell.

        Args:
            cell: Smartsheet cell object

        Returns:
            SmartsheetCell model
        """
        column_id = str(cell.column_id)
        value = cell.value if hasattr(cell, 'value') else None
        display_value = str(cell.display_value) if hasattr(cell, 'display_value') and cell.display_value else None

        return SmartsheetCell(
            column_id=column_id,
            value=value,
            display_value=display_value
        )

    def _convert_smartsheet_date(self, date_str: str) -> Optional[datetime]:
        """
        Convert Smartsheet date string to datetime.

        Args:
            date_str: Date string from Smartsheet

        Returns:
            Python datetime or None
        """
        if not date_str:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            try:
                # Try other common formats
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            except Exception:
                return None

    def _process_row(self, row: Any) -> SmartsheetRow:
        """
        Process a Smartsheet row.

        Args:
            row: Smartsheet row object

        Returns:
            SmartsheetRow model
        """
        row_id = str(row.id)
        row_number = int(row.row_number) if hasattr(row, 'row_number') else 0

        # Process cells
        cells = []
        if hasattr(row, 'cells') and row.cells:
            for cell in row.cells:
                try:
                    cells.append(self._process_cell(cell))
                except Exception:
                    # Skip problematic cells
                    continue

        # Get parent row ID for hierarchical data
        parent_id = str(row.parent_id) if hasattr(row, 'parent_id') and row.parent_id else None

        # Extract timestamps
        created_at = None
        modified_at = None
        if hasattr(row, 'created_at') and row.created_at:
            created_at = self._convert_smartsheet_date(row.created_at)
        if hasattr(row, 'modified_at') and row.modified_at:
            modified_at = self._convert_smartsheet_date(row.modified_at)

        return SmartsheetRow(
            row_id=row_id,
            row_number=row_number,
            cells=cells,
            parent_id=parent_id,
            created_at=created_at,
            modified_at=modified_at
        )

    def extract_metadata(self, source: str) -> Dict[str, Any]:
        """
        Extract metadata from a Smartsheet.

        Args:
            source: Sheet ID or URL

        Returns:
            Dictionary of metadata
        """
        try:
            client = self._get_client()

            # Extract sheet ID from URL if needed
            sheet_id = self._extract_sheet_id(source)

            # Get sheet information
            sheet = client.Sheets.get_sheet(sheet_id)

            metadata = {
                'sheet_name': sheet.name,
                'sheet_id': str(sheet.id),
                'owner': str(sheet.owner) if hasattr(sheet, 'owner') else None,
                'created_at': str(sheet.created_at) if hasattr(sheet, 'created_at') else None,
                'modified_at': str(sheet.modified_at) if hasattr(sheet, 'modified_at') else None,
                'total_rows': len(sheet.rows) if hasattr(sheet, 'rows') else 0,
                'total_columns': len(sheet.columns) if hasattr(sheet, 'columns') else 0,
            }

            if hasattr(sheet, 'workspace') and sheet.workspace:
                metadata['workspace_id'] = str(sheet.workspace.id)
                metadata['workspace_name'] = str(sheet.workspace.name)

            return metadata

        except ApiError as e:
            raise SmartsheetAPIError(f"Smartsheet API error: {str(e)}")
        except Exception as e:
            raise SmartsheetIngestionError(f"Failed to extract metadata: {str(e)}")

    def _extract_sheet_id(self, source: str) -> int:
        """
        Extract sheet ID from string (could be ID or URL).

        Args:
            source: Sheet ID or Smartsheet URL

        Returns:
            Sheet ID as integer
        """
        # If it's already a numeric ID, return it
        if source.isdigit():
            return int(source)

        # Try to extract from URL
        # Smartsheet URLs typically: https://app.smartsheet.com/sheets/xxxxx
        if 'smartsheet.com/sheets/' in source:
            parts = source.split('/sheets/')
            if len(parts) > 1:
                sheet_id_str = parts[1].split('?')[0].split('#')[0]
                if sheet_id_str.isdigit():
                    return int(sheet_id_str)

        # Try to parse as int
        try:
            return int(source)
        except ValueError:
            raise SmartsheetIngestionError(
                f"Invalid sheet identifier: {source}. "
                "Provide either a sheet ID or Smartsheet URL."
            )

    def ingest(self, source: str, **kwargs: Any) -> SmartsheetIngestionResult:
        """
        Ingest data from Smartsheet.

        Args:
            source: Sheet ID or Smartsheet URL
            **kwargs: Additional arguments:
                - include_attachments: bool (default False)
                - include_discussions: bool (default False)

        Returns:
            SmartsheetIngestionResult with extracted data
        """
        errors = []
        columns = []
        rows = []

        try:
            client = self._get_client()

            # Extract sheet ID
            sheet_id = self._extract_sheet_id(source)

            # Get sheet data
            try:
                # Include various sheet elements based on kwargs
                include = []
                if kwargs.get('include_attachments', False):
                    include.append('attachments')
                if kwargs.get('include_discussions', False):
                    include.append('discussions')

                if include:
                    sheet = client.Sheets.get_sheet(sheet_id, include=','.join(include))
                else:
                    sheet = client.Sheets.get_sheet(sheet_id)

            except ApiError as e:
                raise SmartsheetAPIError(f"Failed to retrieve sheet: {str(e)}")

            # Extract basic metadata
            sheet_name = str(sheet.name)
            workspace_id = None
            if hasattr(sheet, 'workspace') and sheet.workspace:
                workspace_id = str(sheet.workspace.id)

            # Build detailed metadata
            metadata = {
                'owner': str(sheet.owner) if hasattr(sheet, 'owner') else None,
                'created_at': str(sheet.created_at) if hasattr(sheet, 'created_at') else None,
                'modified_at': str(sheet.modified_at) if hasattr(sheet, 'modified_at') else None,
                'permalink': str(sheet.permalink) if hasattr(sheet, 'permalink') else None,
            }

            # Process columns
            if hasattr(sheet, 'columns') and sheet.columns:
                for column in sheet.columns:
                    try:
                        columns.append(self._process_column(column))
                    except Exception as e:
                        errors.append(f"Failed to process column {column.id}: {str(e)}")

            # Process rows
            if hasattr(sheet, 'rows') and sheet.rows:
                for row in sheet.rows:
                    try:
                        rows.append(self._process_row(row))
                    except Exception as e:
                        errors.append(f"Failed to process row {row.id}: {str(e)}")

            # Determine status
            if errors and not rows:
                status = IngestionStatus.FAILED
            elif errors:
                status = IngestionStatus.PARTIAL
            else:
                status = IngestionStatus.SUCCESS

            return SmartsheetIngestionResult(
                sheet_name=sheet_name,
                sheet_id=str(sheet_id),
                workspace_id=workspace_id,
                columns=columns,
                rows=rows,
                metadata=metadata,
                ingestion_timestamp=datetime.now(),
                status=status,
                errors=errors,
                total_rows=len(rows),
                total_columns=len(columns)
            )

        except ApiError as e:
            raise SmartsheetAPIError(f"Smartsheet API error: {str(e)}")
        except SmartsheetAPIError:
            raise
        except Exception as e:
            raise SmartsheetIngestionError(f"Failed to ingest Smartsheet: {str(e)}")

    def list_workspaces(self) -> List[Dict[str, str]]:
        """
        List all accessible workspaces.

        Returns:
            List of workspace dictionaries with id and name
        """
        try:
            client = self._get_client()
            workspaces = client.Workspaces.list_workspaces(include_all=True)

            return [
                {
                    'id': str(ws.id),
                    'name': str(ws.name),
                }
                for ws in workspaces.data
            ]

        except ApiError as e:
            raise SmartsheetAPIError(f"Failed to list workspaces: {str(e)}")

    def list_sheets_in_workspace(self, workspace_id: str) -> List[Dict[str, str]]:
        """
        List all sheets in a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of sheet dictionaries with id and name
        """
        try:
            client = self._get_client()
            workspace = client.Workspaces.get_workspace(int(workspace_id))

            sheets = []
            if hasattr(workspace, 'sheets') and workspace.sheets:
                sheets = [
                    {
                        'id': str(sheet.id),
                        'name': str(sheet.name),
                    }
                    for sheet in workspace.sheets
                ]

            return sheets

        except ApiError as e:
            raise SmartsheetAPIError(f"Failed to list sheets in workspace: {str(e)}")

    def validate_file(self, file_path: Any) -> bool:
        """
        Not applicable for API-based ingestion.

        Args:
            file_path: Ignored

        Returns:
            True
        """
        return True
