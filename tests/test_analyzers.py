"""Tests for analyzers."""

import unittest
from unittest.mock import Mock, patch

from src.gpt_integration.analyzers import (
    TestResultAnalyzer,
    ComplianceChecker,
    AnomalyDetector
)
from src.models.gpt_models import ComplianceStandard


class TestTestResultAnalyzer(unittest.TestCase):
    """Test cases for test result analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_gpt_client = Mock()

    def test_analyze_iv_curve(self):
        """Test I-V curve analysis."""
        analyzer = TestResultAnalyzer(self.mock_gpt_client)

        # Mock GPT response
        self.mock_gpt_client.query.return_value = """
{
    "summary": "Good I-V curve",
    "key_findings": ["Voc: 45V", "Isc: 9A"],
    "patterns_detected": ["Normal curve shape"],
    "anomalies": [],
    "data_quality_score": 0.95,
    "recommendations": ["Continue monitoring"]
}
"""

        iv_data = {
            "voltage": [0, 10, 20, 30, 40, 45],
            "current": [9, 8.5, 7, 5, 2, 0]
        }

        result = analyzer.analyze_iv_curve(iv_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.summary, "Good I-V curve")
        self.assertGreater(result.data_quality_score, 0.9)

    def test_analyze_test_results(self):
        """Test general test result analysis."""
        analyzer = TestResultAnalyzer(self.mock_gpt_client)

        self.mock_gpt_client.query.return_value = """
{
    "summary": "All tests passed",
    "key_findings": ["Performance within spec"],
    "patterns_detected": [],
    "anomalies": [],
    "data_quality_score": 1.0,
    "recommendations": []
}
"""

        test_data = {"test": "data"}
        result = analyzer.analyze_test_results(test_data)

        self.assertIsNotNone(result)
        self.mock_gpt_client.query.assert_called_once()


class TestComplianceChecker(unittest.TestCase):
    """Test cases for compliance checker."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_gpt_client = Mock()

    def test_check_compliance(self):
        """Test compliance checking."""
        checker = ComplianceChecker(self.mock_gpt_client)

        self.mock_gpt_client.query.return_value = """
{
    "status": "compliant",
    "requirements_met": ["Thermal cycling", "Humidity freeze"],
    "requirements_failed": [],
    "recommendations": [],
    "confidence_score": 0.9,
    "details": "All requirements met"
}
"""

        result = checker.check_compliance(
            report="Test report",
            test_data={"test": "data"},
            standard=ComplianceStandard.IEC_61215
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.standard, ComplianceStandard.IEC_61215)
        self.assertGreater(result.confidence_score, 0.8)


class TestAnomalyDetector(unittest.TestCase):
    """Test cases for anomaly detector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_gpt_client = Mock()

    def test_detect_anomalies(self):
        """Test anomaly detection."""
        detector = AnomalyDetector(self.mock_gpt_client)

        self.mock_gpt_client.query.return_value = """
[
    {
        "type": "outlier",
        "severity": "high",
        "location": "voltage[5]",
        "description": "Voltage spike detected",
        "confidence": 0.85,
        "suggested_action": "Review measurement equipment"
    }
]
"""

        test_data = {"voltage": [10, 11, 10, 12, 100, 11]}
        anomalies = detector.detect_anomalies(test_data)

        self.assertIsInstance(anomalies, list)
        self.assertGreater(len(anomalies), 0)

    def test_check_data_quality(self):
        """Test data quality checking."""
        detector = AnomalyDetector(self.mock_gpt_client)

        self.mock_gpt_client.query.return_value = """
{
    "completeness_score": 1.0,
    "accuracy_score": 0.95,
    "consistency_score": 0.9,
    "validity_score": 1.0,
    "overall_score": 0.96,
    "issues": [],
    "recommendations": []
}
"""

        test_data = {"complete": "data"}
        result = detector.check_data_quality(test_data)

        self.assertIn("overall_score", result)
        self.assertGreater(result["overall_score"], 0.9)


if __name__ == '__main__':
    unittest.main()
