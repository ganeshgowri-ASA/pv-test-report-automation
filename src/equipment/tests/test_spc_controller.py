"""
Tests for SPC Controller
"""

import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from decimal import Decimal

from ..spc_controller import SPCController
from ..models import SPCDataPoint, SPCControlChart


class TestSPCController(unittest.TestCase):
    """Test SPCController functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.controller = SPCController(storage_path=self.test_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_add_data_point(self):
        """Test adding SPC data point"""
        point = SPCDataPoint(
            equipment_id="eq-123",
            measurement_type="voltage_accuracy",
            measured_value=Decimal('10.05'),
            reference_value=Decimal('10.00'),
            error=Decimal('0.05'),
            operator="Test User"
        )

        data_point_id = self.controller.add_data_point(point)

        self.assertIsNotNone(data_point_id)
        self.assertEqual(len(self.controller._data_points), 1)

    def test_get_data_points_with_filters(self):
        """Test retrieving data points with filters"""
        # Add multiple data points
        for i in range(5):
            point = SPCDataPoint(
                equipment_id="eq-123",
                measurement_type="voltage_accuracy",
                measured_value=Decimal(str(10 + i * 0.1)),
                reference_value=Decimal('10.0'),
                error=Decimal(str(i * 0.1)),
                measured_at=datetime.now() - timedelta(days=i)
            )
            self.controller.add_data_point(point)

        # Get all points for equipment
        points = self.controller.get_data_points("eq-123", "voltage_accuracy")
        self.assertEqual(len(points), 5)

        # Get with limit
        limited = self.controller.get_data_points("eq-123", "voltage_accuracy", limit=3)
        self.assertEqual(len(limited), 3)

    def test_create_control_chart(self):
        """Test creating control chart"""
        chart_id = self.controller.create_control_chart(
            equipment_id="eq-456",
            measurement_type="current_accuracy",
            chart_type="xbar_r"
        )

        self.assertIsNotNone(chart_id)
        self.assertEqual(len(self.controller._control_charts), 1)

        chart = self.controller.get_control_chart(chart_id)
        self.assertEqual(chart.equipment_id, "eq-456")
        self.assertEqual(chart.chart_type, "xbar_r")

    def test_update_control_limits_individuals(self):
        """Test updating control limits for individuals chart"""
        equipment_id = "eq-limits"
        measurement_type = "voltage_error"

        # Create chart
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            chart_type="individuals"
        )

        # Add sufficient data points with known values
        test_values = [0.02, 0.03, -0.01, 0.04, 0.01, -0.02, 0.03, 0.00,
                       0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.00]

        for val in test_values:
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0') + Decimal(str(val)),
                reference_value=Decimal('10.0'),
                error=Decimal(str(val))
            )
            self.controller.add_data_point(point)

        # Update limits
        updated_chart = self.controller.update_control_limits(chart_id)

        self.assertIsNotNone(updated_chart.center_line)
        self.assertIsNotNone(updated_chart.upper_control_limit)
        self.assertIsNotNone(updated_chart.lower_control_limit)

    def test_get_equipment_charts(self):
        """Test getting all charts for equipment"""
        equipment_id = "eq-multi-chart"

        # Create multiple charts
        self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type="voltage_accuracy"
        )
        self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type="current_accuracy"
        )

        charts = self.controller.get_equipment_charts(equipment_id)

        self.assertEqual(len(charts), 2)

    def test_check_rule1_violation(self):
        """Test Rule 1: Point beyond 3 sigma"""
        equipment_id = "eq-rule1"
        measurement_type = "test_metric"

        # Create chart and set known limits
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            chart_type="individuals"
        )

        chart = self.controller.get_control_chart(chart_id)
        chart.center_line = Decimal('0.0')
        chart.upper_control_limit = Decimal('0.3')
        chart.lower_control_limit = Decimal('-0.3')
        self.controller._save_data()  # Save chart updates

        # Add normal points
        for val in [0.02, 0.01, -0.01, 0.03]:
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(val))
            )
            self.controller.add_data_point(point)

        # Add point beyond 3 sigma
        violation_point = SPCDataPoint(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            measured_value=Decimal('10.35'),
            reference_value=Decimal('10.0'),
            error=Decimal('0.35')
        )
        self.controller.add_data_point(violation_point)

        # Check violations
        violations = self.controller.check_control_violations(chart_id)

        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].violation_type, 'rule1')

    def test_check_rule4_violation(self):
        """Test Rule 4: Eight consecutive points on same side"""
        equipment_id = "eq-rule4"
        measurement_type = "test_metric"

        # Create chart
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            chart_type="individuals"
        )

        chart = self.controller.get_control_chart(chart_id)
        chart.center_line = Decimal('0.0')
        chart.upper_control_limit = Decimal('0.3')
        chart.lower_control_limit = Decimal('-0.3')
        self.controller._save_data()  # Save chart updates

        # Add 8 consecutive points above center line
        for _ in range(8):
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal('0.05')  # Positive value
            )
            self.controller.add_data_point(point)

        # Check violations
        violations = self.controller.check_control_violations(chart_id, check_recent=10)

        rule4_violations = [v for v in violations if v.violation_type == 'rule4']
        self.assertGreater(len(rule4_violations), 0)

    def test_check_rule5_violation(self):
        """Test Rule 5: Six consecutive increasing/decreasing points"""
        equipment_id = "eq-rule5"
        measurement_type = "test_metric"

        # Create chart
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            chart_type="individuals"
        )

        chart = self.controller.get_control_chart(chart_id)
        chart.center_line = Decimal('0.0')
        chart.upper_control_limit = Decimal('0.3')
        chart.lower_control_limit = Decimal('-0.3')
        self.controller._save_data()  # Save chart updates

        # Add 6 consecutive increasing points
        for i in range(6):
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(i * 0.01))
            )
            self.controller.add_data_point(point)

        # Check violations
        violations = self.controller.check_control_violations(chart_id, check_recent=10)

        rule5_violations = [v for v in violations if v.violation_type == 'rule5']
        self.assertGreater(len(rule5_violations), 0)

    def test_calculate_process_capability(self):
        """Test process capability calculation"""
        equipment_id = "eq-capability"
        measurement_type = "voltage_error"

        # Create chart
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type
        )

        # Add data points with known distribution
        # Mean = 0.0, StDev ≈ 0.02
        test_values = [0.02, 0.03, -0.01, 0.04, 0.01, -0.02, 0.03, 0.00,
                       0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.00,
                       0.02, 0.01, -0.01, 0.03, 0.00, -0.02, 0.01,
                       0.02, 0.00, 0.01, -0.01, 0.02, 0.00, 0.01, -0.01]

        for val in test_values:
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(val))
            )
            self.controller.add_data_point(point)

        # Calculate capability with spec limits
        capability = self.controller.calculate_process_capability(
            chart_id=chart_id,
            upper_spec_limit=Decimal('0.10'),
            lower_spec_limit=Decimal('-0.10'),
            target_value=Decimal('0.0')
        )

        self.assertIn('cp', capability)
        self.assertIn('cpk', capability)
        self.assertGreater(capability['cp'], 0)
        self.assertGreater(capability['cpk'], 0)
        self.assertIn('interpretation', capability)

    def test_capability_interpretation(self):
        """Test capability interpretation"""
        # Test different Cpk values
        self.assertEqual(
            self.controller._interpret_capability(2.5),
            "Excellent (6-sigma capable)"
        )
        self.assertEqual(
            self.controller._interpret_capability(1.7),
            "Very Good (5-sigma capable)"
        )
        self.assertEqual(
            self.controller._interpret_capability(1.5),
            "Good (4-sigma capable)"
        )
        self.assertEqual(
            self.controller._interpret_capability(1.1),
            "Adequate (3-sigma capable)"
        )
        self.assertEqual(
            self.controller._interpret_capability(0.8),
            "Marginal - improvement needed"
        )
        self.assertEqual(
            self.controller._interpret_capability(0.5),
            "Poor - immediate action required"
        )

    def test_analyze_trend_increasing(self):
        """Test trend analysis for increasing trend"""
        equipment_id = "eq-trend-inc"
        measurement_type = "drift"

        # Add data points with increasing trend
        for i in range(20):
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(i * 0.01))  # Linear increase
            )
            self.controller.add_data_point(point)

        trend = self.controller.analyze_trend(equipment_id, measurement_type)

        self.assertEqual(trend.trend_type, 'increasing')
        self.assertIsNotNone(trend.slope)
        self.assertGreater(trend.slope, 0)

    def test_analyze_trend_stable(self):
        """Test trend analysis for stable data"""
        equipment_id = "eq-trend-stable"
        measurement_type = "stable_metric"

        # Add data points with random variation around zero
        import random
        random.seed(42)

        for _ in range(20):
            val = random.uniform(-0.02, 0.02)
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(val))
            )
            self.controller.add_data_point(point)

        trend = self.controller.analyze_trend(equipment_id, measurement_type)

        # Should be stable or unstable (random data)
        self.assertIn(trend.trend_type, ['stable', 'unstable'])

    def test_analyze_trend_insufficient_data(self):
        """Test trend analysis with insufficient data"""
        equipment_id = "eq-trend-few"
        measurement_type = "test"

        # Add only a few points
        for i in range(5):
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal('0.01')
            )
            self.controller.add_data_point(point)

        trend = self.controller.analyze_trend(equipment_id, measurement_type)

        self.assertEqual(trend.trend_type, 'insufficient_data')

    def test_linear_regression(self):
        """Test linear regression calculation"""
        # Test with known linear data
        x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_values = [2.0, 4.0, 6.0, 8.0, 10.0]  # y = 2x

        slope, r_squared = self.controller._linear_regression(x_values, y_values)

        self.assertAlmostEqual(slope, 2.0, places=5)
        self.assertAlmostEqual(r_squared, 1.0, places=5)

    def test_get_quality_metrics(self):
        """Test quality metrics generation"""
        equipment_id = "eq-metrics"
        measurement_type = "accuracy"

        # Add data points
        for i in range(10):
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(i * 0.01))
            )
            self.controller.add_data_point(point)

        metrics = self.controller.get_quality_metrics(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            period_days=30
        )

        self.assertEqual(metrics['equipment_id'], equipment_id)
        self.assertEqual(metrics['data_points'], 10)
        self.assertIn('mean_error', metrics)
        self.assertIn('std_error', metrics)
        self.assertIn('max_error', metrics)
        self.assertIn('min_error', metrics)

    def test_get_quality_metrics_with_violations(self):
        """Test quality metrics with control violations"""
        equipment_id = "eq-metrics-viol"
        measurement_type = "test"

        # Create chart with limits
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type
        )

        chart = self.controller.get_control_chart(chart_id)
        chart.center_line = Decimal('0.0')
        chart.upper_control_limit = Decimal('0.1')
        chart.lower_control_limit = Decimal('-0.1')
        self.controller._save_data()  # Save chart updates

        # Add points including violation
        for val in [0.01, 0.02, 0.15, 0.01]:  # 0.15 is violation
            point = SPCDataPoint(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                measured_value=Decimal('10.0'),
                reference_value=Decimal('10.0'),
                error=Decimal(str(val))
            )
            self.controller.add_data_point(point)

        metrics = self.controller.get_quality_metrics(
            equipment_id=equipment_id,
            measurement_type=measurement_type
        )

        self.assertGreater(metrics['violations_count'], 0)

    def test_persistence(self):
        """Test data persistence"""
        equipment_id = "eq-persist"
        measurement_type = "test"

        # Add data point
        point = SPCDataPoint(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            measured_value=Decimal('10.0'),
            reference_value=Decimal('10.0'),
            error=Decimal('0.01')
        )
        self.controller.add_data_point(point)

        # Create chart
        chart_id = self.controller.create_control_chart(
            equipment_id=equipment_id,
            measurement_type=measurement_type
        )

        # Create new controller with same storage
        controller2 = SPCController(storage_path=self.test_dir)

        # Verify data was loaded
        points = controller2.get_data_points(equipment_id, measurement_type)
        self.assertEqual(len(points), 1)

        chart = controller2.get_control_chart(chart_id)
        self.assertIsNotNone(chart)


if __name__ == '__main__':
    unittest.main()
