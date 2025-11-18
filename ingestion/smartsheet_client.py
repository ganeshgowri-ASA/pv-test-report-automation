"""
Smartsheet API client for extracting collaborative sheet data.

Supports:
- Smartsheet API authentication
- Sheet data extraction
- Comments and attachments
- Test matrix parsing
- Real-time data refresh
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ingestion.models import (
    SmartsheetAPIError,
    SmartsheetAttachment,
    SmartsheetColumn,
    SmartsheetComment,
    SmartsheetData,
    SmartsheetRow,
)

logger = logging.getLogger(__name__)


class SmartsheetClient:
    """
    Client for Smartsheet API integration.

    Provides methods to:
    - Authenticate with Smartsheet API
    - Extract sheet data
    - Parse test matrices
    - Download attachments
    - Sync collaborative data
    """

    BASE_URL = "https://api.smartsheet.com/2.0"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Smartsheet client.

        Args:
            api_token: Smartsheet API token. If not provided, will look for
                      SMARTSHEET_API_TOKEN environment variable.

        Raises:
            SmartsheetAPIError: If no API token is provided or found
        """
        self.api_token = api_token or os.environ.get('SMARTSHEET_API_TOKEN')

        if not self.api_token:
            raise SmartsheetAPIError(
                "Smartsheet API token required. Provide via api_token parameter "
                "or SMARTSHEET_API_TOKEN environment variable."
            )

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to Smartsheet API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests

        Returns:
            JSON response as dictionary

        Raises:
            SmartsheetAPIError: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Smartsheet API error: {error_msg}")
            raise SmartsheetAPIError(error_msg)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise SmartsheetAPIError(f"Request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise SmartsheetAPIError(f"Invalid JSON response: {str(e)}")

    def get_sheet(self, sheet_id: int, include_all: bool = True) -> SmartsheetData:
        """
        Get complete sheet data including rows, columns, comments, and attachments.

        Args:
            sheet_id: Smartsheet sheet ID
            include_all: Include discussions, attachments, and all metadata

        Returns:
            SmartsheetData object with complete sheet data

        Raises:
            SmartsheetAPIError: If retrieval fails
        """
        # Build query parameters
        params = []
        if include_all:
            params.extend([
                'discussions',
                'attachments',
                'format',
                'filters',
                'rowPermalink',
            ])

        query_string = f"?include={','.join(params)}" if params else ""
        endpoint = f"sheets/{sheet_id}{query_string}"

        try:
            data = self._make_request('GET', endpoint)

            # Parse columns
            columns = []
            for col_data in data.get('columns', []):
                column = SmartsheetColumn(
                    column_id=col_data['id'],
                    title=col_data['title'],
                    column_type=col_data['type'],
                    options=col_data.get('options'),
                    is_primary=col_data.get('primary', False),
                )
                columns.append(column)

            # Build column ID to title map
            col_id_to_title = {col.column_id: col.title for col in columns}

            # Parse rows
            rows = []
            for row_data in data.get('rows', []):
                # Build cells dictionary
                cells = {}
                for cell in row_data.get('cells', []):
                    col_id = cell['columnId']
                    col_title = col_id_to_title.get(col_id, f'Column_{col_id}')

                    # Extract cell value
                    value = cell.get('value') or cell.get('displayValue')
                    cells[col_title] = value

                row = SmartsheetRow(
                    row_id=row_data['id'],
                    row_number=row_data['rowNumber'],
                    cells=cells,
                    created_at=self._parse_datetime(row_data.get('createdAt')),
                    modified_at=self._parse_datetime(row_data.get('modifiedAt')),
                    created_by=row_data.get('createdBy', {}).get('email'),
                    modified_by=row_data.get('modifiedBy', {}).get('email'),
                )
                rows.append(row)

            # Parse comments (discussions)
            comments = []
            for row_data in data.get('rows', []):
                row_id = row_data['id']
                for discussion in row_data.get('discussions', []):
                    for comment_data in discussion.get('comments', []):
                        comment = SmartsheetComment(
                            comment_id=comment_data['id'],
                            text=comment_data['text'],
                            created_by=comment_data.get('createdBy', {}).get('email', 'Unknown'),
                            created_at=self._parse_datetime(comment_data['createdAt']),
                            row_id=row_id,
                        )
                        comments.append(comment)

            # Parse attachments
            attachments = []
            for row_data in data.get('rows', []):
                for attach_data in row_data.get('attachments', []):
                    attachment = SmartsheetAttachment(
                        attachment_id=attach_data['id'],
                        name=attach_data['name'],
                        url=attach_data.get('url'),
                        mime_type=attach_data['mimeType'],
                        size_bytes=attach_data.get('sizeInKb', 0) * 1024,
                        created_at=self._parse_datetime(attach_data['createdAt']),
                        created_by=attach_data.get('createdBy', {}).get('email', 'Unknown'),
                    )
                    attachments.append(attachment)

            # Parse sheet metadata
            modified_date = self._parse_datetime(data.get('modifiedAt'))
            created_date = self._parse_datetime(data.get('createdAt'))

            return SmartsheetData(
                sheet_id=data['id'],
                sheet_name=data['name'],
                columns=columns,
                rows=rows,
                comments=comments,
                attachments=attachments,
                modified_date=modified_date or datetime.utcnow(),
                created_date=created_date,
                owner=data.get('owner', {}).get('email'),
                permalink=data.get('permalink'),
            )

        except KeyError as e:
            raise SmartsheetAPIError(f"Missing expected field in API response: {str(e)}")

    def list_sheets(self) -> List[Dict[str, Any]]:
        """
        List all sheets accessible with current API token.

        Returns:
            List of sheet metadata dictionaries

        Raises:
            SmartsheetAPIError: If listing fails
        """
        data = self._make_request('GET', 'sheets')
        return data.get('data', [])

    def extract_test_matrix(self, sheet_id: int) -> SmartsheetData:
        """
        Extract test matrix data from Smartsheet.

        This is a convenience method that retrieves and structures
        test requirement matrices commonly used in PV testing.

        Args:
            sheet_id: Smartsheet sheet ID

        Returns:
            SmartsheetData with test matrix

        Raises:
            SmartsheetAPIError: If extraction fails
        """
        return self.get_sheet(sheet_id, include_all=True)

    def search_sheets(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for sheets by name.

        Args:
            query: Search query

        Returns:
            List of matching sheets

        Raises:
            SmartsheetAPIError: If search fails
        """
        endpoint = f"search?query={query}"
        data = self._make_request('GET', endpoint)

        # Filter to only sheet results
        results = data.get('results', [])
        sheets = [r for r in results if r.get('objectType') == 'sheet']

        return sheets

    def download_attachment(self, attachment: SmartsheetAttachment, output_dir: str) -> str:
        """
        Download attachment file.

        Args:
            attachment: SmartsheetAttachment object
            output_dir: Directory to save attachment

        Returns:
            Path to downloaded file

        Raises:
            SmartsheetAPIError: If download fails
        """
        if not attachment.url:
            raise SmartsheetAPIError(f"No download URL for attachment: {attachment.name}")

        output_path = Path(output_dir) / attachment.name

        try:
            # Download file
            response = self.session.get(attachment.url)
            response.raise_for_status()

            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded attachment: {output_path}")
            return str(output_path)

        except requests.exceptions.RequestException as e:
            raise SmartsheetAPIError(f"Failed to download attachment: {str(e)}")

    def export_to_csv(self, sheet_id: int, output_path: str) -> str:
        """
        Export sheet data to CSV file.

        Args:
            sheet_id: Smartsheet sheet ID
            output_path: Output CSV file path

        Returns:
            Path to exported CSV file

        Raises:
            SmartsheetAPIError: If export fails
        """
        sheet_data = self.get_sheet(sheet_id, include_all=False)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not sheet_data.rows:
                return output_path

            # Get all column titles
            fieldnames = [col.title for col in sheet_data.columns]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in sheet_data.rows:
                writer.writerow(row.cells)

        logger.info(f"Exported sheet to CSV: {output_path}")
        return output_path

    def export_to_json(self, sheet_id: int, output_path: str) -> str:
        """
        Export sheet data to JSON file.

        Args:
            sheet_id: Smartsheet sheet ID
            output_path: Output JSON file path

        Returns:
            Path to exported JSON file

        Raises:
            SmartsheetAPIError: If export fails
        """
        sheet_data = self.get_sheet(sheet_id, include_all=True)

        # Convert to dict
        data_dict = sheet_data.model_dump(mode='json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, default=str)

        logger.info(f"Exported sheet to JSON: {output_path}")
        return output_path

    def refresh_sheet_data(self, sheet_id: int) -> SmartsheetData:
        """
        Refresh and get latest sheet data.

        This is equivalent to get_sheet() but makes the intent clear.

        Args:
            sheet_id: Smartsheet sheet ID

        Returns:
            Fresh SmartsheetData

        Raises:
            SmartsheetAPIError: If refresh fails
        """
        logger.info(f"Refreshing sheet data for sheet {sheet_id}")
        return self.get_sheet(sheet_id, include_all=True)

    def get_column_values(self, sheet_id: int, column_title: str) -> List[Any]:
        """
        Extract all values from a specific column.

        Args:
            sheet_id: Smartsheet sheet ID
            column_title: Column title to extract

        Returns:
            List of column values

        Raises:
            SmartsheetAPIError: If extraction fails
        """
        sheet_data = self.get_sheet(sheet_id, include_all=False)
        return sheet_data.get_column_values(column_title)

    def filter_rows(
        self,
        sheet_id: int,
        filter_column: str,
        filter_value: Any
    ) -> List[SmartsheetRow]:
        """
        Filter rows by column value.

        Args:
            sheet_id: Smartsheet sheet ID
            filter_column: Column to filter on
            filter_value: Value to match

        Returns:
            List of matching rows

        Raises:
            SmartsheetAPIError: If filtering fails
        """
        sheet_data = self.get_sheet(sheet_id, include_all=False)

        filtered_rows = []
        for row in sheet_data.rows:
            if row.cells.get(filter_column) == filter_value:
                filtered_rows.append(row)

        return filtered_rows

    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string"""
        if not dt_string:
            return None

        try:
            # Handle timezone offset
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Invalid datetime format: {dt_string}")
            return None

    def validate_connection(self) -> bool:
        """
        Validate API token and connection to Smartsheet.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            self._make_request('GET', 'users/me')
            logger.info("Smartsheet connection validated successfully")
            return True
        except SmartsheetAPIError:
            logger.error("Smartsheet connection validation failed")
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information.

        Returns:
            User information dictionary

        Raises:
            SmartsheetAPIError: If request fails
        """
        return self._make_request('GET', 'users/me')
