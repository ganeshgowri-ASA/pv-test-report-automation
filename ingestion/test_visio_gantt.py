"""
Comprehensive unit tests for ingestion module.

Tests:
- Visio parser functionality
- Gantt/MS Project parser functionality
- Smartsheet client (mocked API)
- Diagram extractor
- Timeline parser
- Model validation
- Error handling
"""

import json
import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from ingestion.diagram_extractor import DiagramExtractor
from ingestion.gantt_parser import GanttIngestion
from ingestion.models import (
    DiagramConnector,
    DiagramShape,
    GanttParsingError,
    GanttTask,
    SmartsheetAPIError,
    SmartsheetData,
    TimelineData,
    VisioIngestionResult,
    VisioParsingError,
)
from ingestion.smartsheet_client import SmartsheetClient
from ingestion.timeline_parser import TimelineParser


class TestGanttParser(unittest.TestCase):
    """Test cases for Gantt/MS Project parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_data_dir = Path(__file__).parent / 'sample_data'
        self.test_xml_path = self.sample_data_dir / 'test_schedule.xml'

    def test_gantt_init_valid_file(self):
        """Test GanttIngestion initialization with valid file"""
        if self.test_xml_path.exists():
            gantt = GanttIngestion(str(self.test_xml_path))
            self.assertEqual(gantt.project_name, 'test_schedule')
            self.assertIsNotNone(gantt.file_hash)

    def test_gantt_init_missing_file(self):
        """Test GanttIngestion raises error for missing file"""
        with self.assertRaises(GanttParsingError):
            GanttIngestion('/nonexistent/file.xml')

    def test_gantt_init_invalid_format(self):
        """Test GanttIngestion raises error for invalid format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            with self.assertRaises(GanttParsingError):
                GanttIngestion(temp_path)
        finally:
            os.unlink(temp_path)

    def test_extract_tasks_from_xml(self):
        """Test task extraction from XML file"""
        if not self.test_xml_path.exists():
            self.skipTest("Sample XML file not found")

        gantt = GanttIngestion(str(self.test_xml_path))
        tasks = gantt.extract_tasks()

        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)

        # Check first task
        task = tasks[0]
        self.assertIsInstance(task, GanttTask)
        self.assertEqual(task.task_id, 1)
        self.assertIn('Calibration', task.task_name)
        self.assertIsInstance(task.start_date, date)
        self.assertIsInstance(task.end_date, date)

    def test_extract_timeline(self):
        """Test complete timeline extraction"""
        if not self.test_xml_path.exists():
            self.skipTest("Sample XML file not found")

        gantt = GanttIngestion(str(self.test_xml_path))
        timeline = gantt.extract_timeline()

        self.assertIsInstance(timeline, TimelineData)
        self.assertEqual(timeline.project_name, 'test_schedule')
        self.assertGreater(len(timeline.tasks), 0)
        self.assertIsNotNone(timeline.start_date)
        self.assertIsNotNone(timeline.end_date)
        self.assertTrue(timeline.start_date < timeline.end_date)

    def test_critical_path_calculation(self):
        """Test critical path calculation"""
        if not self.test_xml_path.exists():
            self.skipTest("Sample XML file not found")

        gantt = GanttIngestion(str(self.test_xml_path))
        timeline = gantt.extract_timeline()

        if timeline.critical_path:
            self.assertIsNotNone(timeline.critical_path.critical_tasks)
            self.assertIsNotNone(timeline.critical_path.total_duration)
            self.assertGreater(timeline.critical_path.total_duration, 0)

    def test_export_to_json(self):
        """Test JSON export"""
        if not self.test_xml_path.exists():
            self.skipTest("Sample XML file not found")

        gantt = GanttIngestion(str(self.test_xml_path))

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            output_path = f.name

        try:
            result_path = gantt.export_to_json(output_path)
            self.assertEqual(result_path, output_path)
            self.assertTrue(os.path.exists(output_path))

            # Verify JSON is valid
            with open(output_path, 'r') as f:
                data = json.load(f)
                self.assertIn('project_name', data)
                self.assertIn('tasks', data)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_to_csv(self):
        """Test CSV export"""
        if not self.test_xml_path.exists():
            self.skipTest("Sample XML file not found")

        gantt = GanttIngestion(str(self.test_xml_path))

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
            output_path = f.name

        try:
            result_path = gantt.export_to_csv(output_path)
            self.assertEqual(result_path, output_path)
            self.assertTrue(os.path.exists(output_path))

            # Verify CSV has content
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('task_id', content)
                self.assertIn('task_name', content)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestSmartsheetClient(unittest.TestCase):
    """Test cases for Smartsheet API client"""

    def test_init_with_token(self):
        """Test initialization with API token"""
        client = SmartsheetClient(api_token='test_token_123')
        self.assertEqual(client.api_token, 'test_token_123')

    def test_init_without_token(self):
        """Test initialization without token raises error"""
        # Save current env var if exists
        old_token = os.environ.get('SMARTSHEET_API_TOKEN')
        if 'SMARTSHEET_API_TOKEN' in os.environ:
            del os.environ['SMARTSHEET_API_TOKEN']

        try:
            with self.assertRaises(SmartsheetAPIError):
                SmartsheetClient()
        finally:
            # Restore env var
            if old_token:
                os.environ['SMARTSHEET_API_TOKEN'] = old_token

    @patch('ingestion.smartsheet_client.requests.Session')
    def test_validate_connection_success(self, mock_session):
        """Test successful connection validation"""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 123, 'email': 'test@example.com'}
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = SmartsheetClient(api_token='test_token')
        result = client.validate_connection()

        self.assertTrue(result)

    @patch('ingestion.smartsheet_client.requests.Session.request')
    def test_validate_connection_failure(self, mock_request):
        """Test failed connection validation"""
        # Mock a failed request by raising an HTTPError
        from requests.exceptions import HTTPError
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.side_effect = HTTPError(response=mock_response)

        client = SmartsheetClient(api_token='test_token')
        result = client.validate_connection()

        self.assertFalse(result)

    def test_load_sample_smartsheet_data(self):
        """Test loading sample Smartsheet JSON data"""
        sample_file = Path(__file__).parent / 'sample_data' / 'test_matrix.json'

        if not sample_file.exists():
            self.skipTest("Sample Smartsheet JSON not found")

        with open(sample_file, 'r') as f:
            data = json.load(f)

        # Validate structure
        smartsheet_data = SmartsheetData(**data)
        self.assertEqual(smartsheet_data.sheet_id, 123456789)
        self.assertGreater(len(smartsheet_data.rows), 0)
        self.assertGreater(len(smartsheet_data.columns), 0)

    def test_smartsheet_data_to_dict_rows(self):
        """Test converting SmartsheetData to dict rows"""
        sample_file = Path(__file__).parent / 'sample_data' / 'test_matrix.json'

        if not sample_file.exists():
            self.skipTest("Sample Smartsheet JSON not found")

        with open(sample_file, 'r') as f:
            data = json.load(f)

        smartsheet_data = SmartsheetData(**data)
        dict_rows = smartsheet_data.to_dict_rows()

        self.assertIsInstance(dict_rows, list)
        self.assertGreater(len(dict_rows), 0)
        self.assertIsInstance(dict_rows[0], dict)

    def test_smartsheet_get_column_values(self):
        """Test extracting column values"""
        sample_file = Path(__file__).parent / 'sample_data' / 'test_matrix.json'

        if not sample_file.exists():
            self.skipTest("Sample Smartsheet JSON not found")

        with open(sample_file, 'r') as f:
            data = json.load(f)

        smartsheet_data = SmartsheetData(**data)
        statuses = smartsheet_data.get_column_values('Status')

        self.assertIsInstance(statuses, list)
        self.assertGreater(len(statuses), 0)


class TestTimelineParser(unittest.TestCase):
    """Test cases for timeline parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_xml = Path(__file__).parent / 'sample_data' / 'test_schedule.xml'

    def test_parse_timeline(self):
        """Test timeline parsing"""
        if not self.sample_xml.exists():
            self.skipTest("Sample XML not found")

        parser = TimelineParser()
        timeline = parser.parse_timeline(str(self.sample_xml))

        self.assertIsInstance(timeline, TimelineData)
        self.assertGreater(len(timeline.tasks), 0)

    def test_extract_test_schedule(self):
        """Test extracting test schedule with phases"""
        if not self.sample_xml.exists():
            self.skipTest("Sample XML not found")

        parser = TimelineParser()
        schedule = parser.extract_test_schedule(str(self.sample_xml))

        self.assertIn('project_name', schedule)
        self.assertIn('phases', schedule)
        self.assertIn('start_date', schedule)
        self.assertIn('end_date', schedule)

    def test_extract_milestones(self):
        """Test milestone extraction"""
        if not self.sample_xml.exists():
            self.skipTest("Sample XML not found")

        parser = TimelineParser()
        milestones = parser.extract_milestones(str(self.sample_xml))

        self.assertIsInstance(milestones, list)

    def test_calculate_workload(self):
        """Test workload calculation"""
        if not self.sample_xml.exists():
            self.skipTest("Sample XML not found")

        parser = TimelineParser()
        workload = parser.calculate_workload(str(self.sample_xml))

        self.assertIsInstance(workload, dict)

    def test_export_calendar_format(self):
        """Test iCalendar export"""
        if not self.sample_xml.exists():
            self.skipTest("Sample XML not found")

        parser = TimelineParser()

        with tempfile.NamedTemporaryFile(suffix='.ics', delete=False, mode='w') as f:
            output_path = f.name

        try:
            result_path = parser.export_calendar_format(str(self.sample_xml), output_path)
            self.assertTrue(os.path.exists(result_path))

            # Verify iCalendar format
            with open(result_path, 'r') as f:
                content = f.read()
                self.assertIn('BEGIN:VCALENDAR', content)
                self.assertIn('END:VCALENDAR', content)
                self.assertIn('BEGIN:VEVENT', content)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestModels(unittest.TestCase):
    """Test cases for Pydantic models"""

    def test_gantt_task_model_validation(self):
        """Test GanttTask model validation"""
        task = GanttTask(
            task_id=1,
            task_name="Test Task",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10),
            duration=9,
            completion=50.0,
        )

        self.assertEqual(task.task_id, 1)
        self.assertEqual(task.completion, 50.0)

    def test_gantt_task_completion_bounds(self):
        """Test completion percentage is bounded 0-100"""
        # Should clamp to 100
        task = GanttTask(
            task_id=1,
            task_name="Test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10),
            duration=9,
            completion=150.0,
        )
        self.assertEqual(task.completion, 100.0)

        # Should clamp to 0
        task2 = GanttTask(
            task_id=2,
            task_name="Test2",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10),
            duration=9,
            completion=-10.0,
        )
        self.assertEqual(task2.completion, 0.0)

    def test_diagram_shape_model(self):
        """Test DiagramShape model"""
        shape = DiagramShape(
            shape_id="shape1",
            shape_type="process",
            text="Test Step",
            position_x=100.0,
            position_y=200.0,
        )

        self.assertEqual(shape.shape_id, "shape1")
        self.assertEqual(shape.shape_type, "process")
        self.assertEqual(shape.text, "Test Step")

    def test_diagram_connector_model(self):
        """Test DiagramConnector model"""
        connector = DiagramConnector(
            connector_id="conn1",
            from_shape_id="shape1",
            to_shape_id="shape2",
            label="Next",
        )

        self.assertEqual(connector.from_shape_id, "shape1")
        self.assertEqual(connector.to_shape_id, "shape2")


class TestVisioParser(unittest.TestCase):
    """Test cases for Visio parser"""

    def test_visio_init_invalid_file(self):
        """Test VisioIngestion raises error for missing file"""
        with self.assertRaises(VisioParsingError):
            from ingestion.visio_parser import VisioIngestion
            VisioIngestion('/nonexistent/file.vsdx')

    def test_visio_init_invalid_format(self):
        """Test VisioIngestion raises error for invalid format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            with self.assertRaises(VisioParsingError):
                from ingestion.visio_parser import VisioIngestion
                VisioIngestion(temp_path)
        finally:
            os.unlink(temp_path)


class TestDiagramExtractor(unittest.TestCase):
    """Test cases for diagram extractor"""

    def test_extractor_init(self):
        """Test DiagramExtractor initialization"""
        extractor = DiagramExtractor()
        self.assertIn('.vsdx', extractor.supported_formats)

    def test_extract_unsupported_format(self):
        """Test extraction with unsupported format"""
        extractor = DiagramExtractor()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            from ingestion.models import DiagramExtractionError
            with self.assertRaises(DiagramExtractionError):
                extractor.extract_from_file(temp_path)
        finally:
            os.unlink(temp_path)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""

    def test_gantt_to_timeline_workflow(self):
        """Test complete Gantt -> Timeline workflow"""
        sample_xml = Path(__file__).parent / 'sample_data' / 'test_schedule.xml'

        if not sample_xml.exists():
            self.skipTest("Sample XML not found")

        # Parse with GanttIngestion
        gantt = GanttIngestion(str(sample_xml))
        tasks = gantt.extract_tasks()

        # Parse with TimelineParser
        parser = TimelineParser()
        timeline = parser.parse_timeline(str(sample_xml))

        # Both should have same number of tasks
        self.assertEqual(len(tasks), len(timeline.tasks))

    def test_smartsheet_json_load_workflow(self):
        """Test loading and processing Smartsheet JSON"""
        sample_json = Path(__file__).parent / 'sample_data' / 'test_matrix.json'

        if not sample_json.exists():
            self.skipTest("Sample JSON not found")

        with open(sample_json, 'r') as f:
            data = json.load(f)

        # Load into model
        smartsheet_data = SmartsheetData(**data)

        # Extract specific columns
        test_ids = smartsheet_data.get_column_values('Test ID')
        statuses = smartsheet_data.get_column_values('Status')

        self.assertEqual(len(test_ids), len(smartsheet_data.rows))
        self.assertEqual(len(statuses), len(smartsheet_data.rows))


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGanttParser))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartsheetClient))
    suite.addTests(loader.loadTestsFromTestCase(TestTimelineParser))
    suite.addTests(loader.loadTestsFromTestCase(TestModels))
    suite.addTests(loader.loadTestsFromTestCase(TestVisioParser))
    suite.addTests(loader.loadTestsFromTestCase(TestDiagramExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
