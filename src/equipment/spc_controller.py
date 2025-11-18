"""
SPC Controller (Session 33)

Statistical Process Control with control charts, out-of-control detection,
capability analysis, trend analysis, and quality metrics.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import statistics

from .models import (
    SPCDataPoint,
    SPCControlChart
)


logger = logging.getLogger(__name__)


@dataclass
class ControlViolation:
    """Control chart violation"""
    equipment_id: str
    measurement_type: str
    data_point_id: str
    violation_type: str
    message: str
    severity: str  # 'warning', 'critical'
    measured_at: datetime
    value: Decimal


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    equipment_id: str
    measurement_type: str
    trend_type: str  # 'increasing', 'decreasing', 'stable', 'unstable'
    slope: Optional[float]
    r_squared: Optional[float]
    description: str


class SPCController:
    """
    Statistical Process Control Controller

    Manages SPC data collection, control chart generation, out-of-control detection,
    process capability analysis, and trend analysis.
    """

    # Western Electric Rules for out-of-control detection
    WESTERN_ELECTRIC_RULES = {
        'rule1': 'One point beyond 3 sigma from center line',
        'rule2': 'Two out of three consecutive points beyond 2 sigma (same side)',
        'rule3': 'Four out of five consecutive points beyond 1 sigma (same side)',
        'rule4': 'Eight consecutive points on same side of center line',
        'rule5': 'Six consecutive points increasing or decreasing',
        'rule6': 'Fifteen consecutive points within 1 sigma',
        'rule7': 'Fourteen consecutive points alternating up and down',
        'rule8': 'Eight consecutive points beyond 1 sigma (both sides)',
    }

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize SPC controller

        Args:
            storage_path: Path to store SPC data
        """
        self.storage_path = Path(storage_path) if storage_path else Path("./data/spc")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.data_points_file = self.storage_path / "data_points.json"
        self.control_charts_file = self.storage_path / "control_charts.json"

        self._data_points: List[SPCDataPoint] = []
        self._control_charts: Dict[str, SPCControlChart] = {}

        self._load_data()

    def _load_data(self) -> None:
        """Load SPC data from storage"""
        try:
            if self.data_points_file.exists():
                with open(self.data_points_file, 'r') as f:
                    data = json.load(f)
                    self._data_points = [SPCDataPoint.from_dict(item) for item in data]
                logger.info(f"Loaded {len(self._data_points)} SPC data points")

            if self.control_charts_file.exists():
                with open(self.control_charts_file, 'r') as f:
                    data = json.load(f)
                    self._control_charts = {
                        item['chart_id']: SPCControlChart.from_dict(item)
                        for item in data
                    }
                logger.info(f"Loaded {len(self._control_charts)} control charts")

        except Exception as e:
            logger.error(f"Error loading SPC data: {e}")

    def _save_data(self) -> None:
        """Save SPC data to storage"""
        try:
            with open(self.data_points_file, 'w') as f:
                data = [dp.to_dict() for dp in self._data_points]
                json.dump(data, f, indent=2)

            with open(self.control_charts_file, 'w') as f:
                data = [chart.to_dict() for chart in self._control_charts.values()]
                json.dump(data, f, indent=2)

            logger.info("SPC data saved successfully")

        except Exception as e:
            logger.error(f"Error saving SPC data: {e}")
            raise

    # ==================== Data Collection ====================

    def add_data_point(self, data_point: SPCDataPoint) -> str:
        """
        Add SPC data point

        Args:
            data_point: SPCDataPoint object

        Returns:
            data_point_id
        """
        self._data_points.append(data_point)
        self._save_data()

        logger.info(f"Added SPC data point for equipment {data_point.equipment_id}")
        return data_point.data_point_id

    def get_data_points(
        self,
        equipment_id: str,
        measurement_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[SPCDataPoint]:
        """
        Get SPC data points with filters

        Args:
            equipment_id: Equipment ID
            measurement_type: Type of measurement
            start_date: Optional start datetime
            end_date: Optional end datetime
            limit: Optional limit on number of points

        Returns:
            List of SPCDataPoint objects
        """
        points = [
            dp for dp in self._data_points
            if dp.equipment_id == equipment_id and dp.measurement_type == measurement_type
        ]

        if start_date:
            points = [dp for dp in points if dp.measured_at >= start_date]

        if end_date:
            points = [dp for dp in points if dp.measured_at <= end_date]

        # Sort by measurement time
        points.sort(key=lambda dp: dp.measured_at)

        if limit:
            points = points[-limit:]  # Most recent points

        return points

    # ==================== Control Chart Management ====================

    def create_control_chart(
        self,
        equipment_id: str,
        measurement_type: str,
        chart_type: str = "xbar_r",
        subgroup_size: int = 5,
        data_points_for_limits: int = 25,
        sigma_multiplier: Decimal = Decimal('3.0')
    ) -> str:
        """
        Create new control chart

        Args:
            equipment_id: Equipment ID
            measurement_type: Type of measurement
            chart_type: Chart type (xbar_r, individuals, cusum, ewma)
            subgroup_size: Subgroup size for X-bar R charts
            data_points_for_limits: Number of points to use for calculating limits
            sigma_multiplier: Sigma multiplier for control limits (typically 3)

        Returns:
            chart_id
        """
        chart = SPCControlChart(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            chart_type=chart_type,
            subgroup_size=subgroup_size,
            data_points_for_limits=data_points_for_limits,
            sigma_multiplier=sigma_multiplier
        )

        self._control_charts[chart.chart_id] = chart
        self._save_data()

        logger.info(f"Created {chart_type} control chart for {equipment_id}/{measurement_type}")
        return chart.chart_id

    def update_control_limits(self, chart_id: str) -> SPCControlChart:
        """
        Calculate and update control limits based on historical data

        Args:
            chart_id: Control chart ID

        Returns:
            Updated SPCControlChart
        """
        chart = self._control_charts.get(chart_id)
        if not chart:
            raise ValueError(f"Control chart not found: {chart_id}")

        # Get recent data points
        points = self.get_data_points(
            equipment_id=chart.equipment_id,
            measurement_type=chart.measurement_type,
            limit=chart.data_points_for_limits
        )

        if len(points) < 10:
            logger.warning(f"Insufficient data points ({len(points)}) to calculate control limits")
            return chart

        # Calculate based on chart type
        if chart.chart_type == "individuals":
            self._calculate_individuals_limits(chart, points)
        elif chart.chart_type == "xbar_r":
            self._calculate_xbar_r_limits(chart, points)
        else:
            logger.warning(f"Chart type {chart.chart_type} not fully implemented")
            self._calculate_individuals_limits(chart, points)

        chart.last_updated = datetime.now()
        self._save_data()

        return chart

    def _calculate_individuals_limits(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> None:
        """Calculate control limits for individuals chart (I-MR chart)"""
        values = [float(dp.error) for dp in points]

        # Calculate center line (mean)
        mean_value = statistics.mean(values)
        chart.center_line = Decimal(str(mean_value))

        # Calculate moving range
        moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        if moving_ranges:
            mean_mr = statistics.mean(moving_ranges)

            # Control limits using moving range
            # For individuals chart: UCL = X̄ + 3(MR̄/d2), LCL = X̄ - 3(MR̄/d2)
            # d2 for n=2 is 1.128
            d2 = 1.128
            sigma_est = mean_mr / d2

            multiplier = float(chart.sigma_multiplier)
            chart.upper_control_limit = Decimal(str(mean_value + multiplier * sigma_est))
            chart.lower_control_limit = Decimal(str(mean_value - multiplier * sigma_est))

            # Warning limits at 2 sigma
            chart.upper_warning_limit = Decimal(str(mean_value + 2 * sigma_est))
            chart.lower_warning_limit = Decimal(str(mean_value - 2 * sigma_est))

    def _calculate_xbar_r_limits(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> None:
        """Calculate control limits for X-bar and R chart"""
        # Group points into subgroups
        subgroup_size = chart.subgroup_size
        values = [float(dp.error) for dp in points]

        if len(values) < subgroup_size:
            logger.warning("Insufficient data for X-bar R chart, using individuals instead")
            self._calculate_individuals_limits(chart, points)
            return

        # Calculate subgroup means and ranges
        subgroup_means = []
        subgroup_ranges = []

        for i in range(0, len(values) - subgroup_size + 1, subgroup_size):
            subgroup = values[i:i + subgroup_size]
            subgroup_means.append(statistics.mean(subgroup))
            subgroup_ranges.append(max(subgroup) - min(subgroup))

        if not subgroup_means:
            return

        # X-bar chart center line
        xbar_mean = statistics.mean(subgroup_means)
        chart.center_line = Decimal(str(xbar_mean))

        # Average range
        r_mean = statistics.mean(subgroup_ranges)

        # Control limit constants (for n=5)
        # These would vary based on subgroup_size in production
        A2 = 0.577  # for n=5
        D3 = 0.0    # for n=5
        D4 = 2.114  # for n=5

        # X-bar control limits
        chart.upper_control_limit = Decimal(str(xbar_mean + A2 * r_mean))
        chart.lower_control_limit = Decimal(str(xbar_mean - A2 * r_mean))

        # Warning limits (approximate)
        chart.upper_warning_limit = Decimal(str(xbar_mean + (2/3) * A2 * r_mean))
        chart.lower_warning_limit = Decimal(str(xbar_mean - (2/3) * A2 * r_mean))

    def get_control_chart(self, chart_id: str) -> Optional[SPCControlChart]:
        """Get control chart by ID"""
        return self._control_charts.get(chart_id)

    def get_equipment_charts(self, equipment_id: str) -> List[SPCControlChart]:
        """Get all control charts for equipment"""
        return [
            chart for chart in self._control_charts.values()
            if chart.equipment_id == equipment_id and chart.is_active
        ]

    # ==================== Out-of-Control Detection ====================

    def check_control_violations(
        self,
        chart_id: str,
        check_recent: int = 20
    ) -> List[ControlViolation]:
        """
        Check for control chart violations using Western Electric Rules

        Args:
            chart_id: Control chart ID
            check_recent: Number of recent points to check

        Returns:
            List of ControlViolation objects
        """
        chart = self.get_control_chart(chart_id)
        if not chart:
            raise ValueError(f"Control chart not found: {chart_id}")

        if chart.center_line is None or chart.upper_control_limit is None:
            logger.warning("Control limits not set, cannot check violations")
            return []

        # Get recent data points
        points = self.get_data_points(
            equipment_id=chart.equipment_id,
            measurement_type=chart.measurement_type,
            limit=check_recent
        )

        if not points:
            return []

        violations = []

        # Check Western Electric Rules
        violations.extend(self._check_rule1(chart, points))
        violations.extend(self._check_rule2(chart, points))
        violations.extend(self._check_rule3(chart, points))
        violations.extend(self._check_rule4(chart, points))
        violations.extend(self._check_rule5(chart, points))

        return violations

    def _get_sigma_zone(self, value: Decimal, chart: SPCControlChart) -> int:
        """
        Get sigma zone for value (-3 to +3)

        Returns:
            Zone number: 0 (within 1σ), ±1 (1-2σ), ±2 (2-3σ), ±3 (beyond 3σ)
        """
        if chart.center_line is None or chart.upper_control_limit is None:
            return 0

        cl = float(chart.center_line)
        ucl = float(chart.upper_control_limit)
        lcl = float(chart.lower_control_limit)

        sigma = (ucl - cl) / 3.0
        val = float(value)

        deviation = (val - cl) / sigma if sigma > 0 else 0

        if deviation > 3:
            return 3
        elif deviation > 2:
            return 2
        elif deviation > 1:
            return 1
        elif deviation < -3:
            return -3
        elif deviation < -2:
            return -2
        elif deviation < -1:
            return -1
        else:
            return 0

    def _check_rule1(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> List[ControlViolation]:
        """Rule 1: One point beyond 3 sigma"""
        violations = []

        for point in points:
            zone = self._get_sigma_zone(point.error, chart)

            if abs(zone) >= 3:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=point.data_point_id,
                    violation_type='rule1',
                    message=self.WESTERN_ELECTRIC_RULES['rule1'],
                    severity='critical',
                    measured_at=point.measured_at,
                    value=point.error
                ))

        return violations

    def _check_rule2(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> List[ControlViolation]:
        """Rule 2: Two out of three consecutive points beyond 2 sigma (same side)"""
        violations = []

        for i in range(len(points) - 2):
            window = points[i:i+3]
            zones = [self._get_sigma_zone(dp.error, chart) for dp in window]

            # Check positive side
            beyond_2sigma_pos = sum(1 for z in zones if z >= 2)
            if beyond_2sigma_pos >= 2:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=window[-1].data_point_id,
                    violation_type='rule2',
                    message=self.WESTERN_ELECTRIC_RULES['rule2'],
                    severity='warning',
                    measured_at=window[-1].measured_at,
                    value=window[-1].error
                ))

            # Check negative side
            beyond_2sigma_neg = sum(1 for z in zones if z <= -2)
            if beyond_2sigma_neg >= 2:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=window[-1].data_point_id,
                    violation_type='rule2',
                    message=self.WESTERN_ELECTRIC_RULES['rule2'],
                    severity='warning',
                    measured_at=window[-1].measured_at,
                    value=window[-1].error
                ))

        return violations

    def _check_rule3(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> List[ControlViolation]:
        """Rule 3: Four out of five consecutive points beyond 1 sigma (same side)"""
        violations = []

        for i in range(len(points) - 4):
            window = points[i:i+5]
            zones = [self._get_sigma_zone(dp.error, chart) for dp in window]

            # Check positive side
            beyond_1sigma_pos = sum(1 for z in zones if z >= 1)
            if beyond_1sigma_pos >= 4:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=window[-1].data_point_id,
                    violation_type='rule3',
                    message=self.WESTERN_ELECTRIC_RULES['rule3'],
                    severity='warning',
                    measured_at=window[-1].measured_at,
                    value=window[-1].error
                ))

            # Check negative side
            beyond_1sigma_neg = sum(1 for z in zones if z <= -1)
            if beyond_1sigma_neg >= 4:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=window[-1].data_point_id,
                    violation_type='rule3',
                    message=self.WESTERN_ELECTRIC_RULES['rule3'],
                    severity='warning',
                    measured_at=window[-1].measured_at,
                    value=window[-1].error
                ))

        return violations

    def _check_rule4(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> List[ControlViolation]:
        """Rule 4: Eight consecutive points on same side of center line"""
        violations = []

        if chart.center_line is None:
            return violations

        for i in range(len(points) - 7):
            window = points[i:i+8]
            cl = float(chart.center_line)
            values = [float(dp.error) for dp in window]

            all_above = all(v > cl for v in values)
            all_below = all(v < cl for v in values)

            if all_above or all_below:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=window[-1].data_point_id,
                    violation_type='rule4',
                    message=self.WESTERN_ELECTRIC_RULES['rule4'],
                    severity='warning',
                    measured_at=window[-1].measured_at,
                    value=window[-1].error
                ))

        return violations

    def _check_rule5(
        self,
        chart: SPCControlChart,
        points: List[SPCDataPoint]
    ) -> List[ControlViolation]:
        """Rule 5: Six consecutive points increasing or decreasing"""
        violations = []

        for i in range(len(points) - 5):
            window = points[i:i+6]
            values = [float(dp.error) for dp in window]

            increasing = all(values[j] < values[j+1] for j in range(5))
            decreasing = all(values[j] > values[j+1] for j in range(5))

            if increasing or decreasing:
                violations.append(ControlViolation(
                    equipment_id=chart.equipment_id,
                    measurement_type=chart.measurement_type,
                    data_point_id=window[-1].data_point_id,
                    violation_type='rule5',
                    message=self.WESTERN_ELECTRIC_RULES['rule5'],
                    severity='warning',
                    measured_at=window[-1].measured_at,
                    value=window[-1].error
                ))

        return violations

    # ==================== Capability Analysis ====================

    def calculate_process_capability(
        self,
        chart_id: str,
        upper_spec_limit: Optional[Decimal] = None,
        lower_spec_limit: Optional[Decimal] = None,
        target_value: Optional[Decimal] = None,
        data_points: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate process capability indices (Cp, Cpk, Pp, Ppk)

        Args:
            chart_id: Control chart ID
            upper_spec_limit: Upper specification limit
            lower_spec_limit: Lower specification limit
            target_value: Target value
            data_points: Number of recent points to use (None = all)

        Returns:
            Dictionary with capability indices
        """
        chart = self.get_control_chart(chart_id)
        if not chart:
            raise ValueError(f"Control chart not found: {chart_id}")

        # Use spec limits from chart if not provided
        usl = upper_spec_limit or chart.upper_spec_limit
        lsl = lower_spec_limit or chart.lower_spec_limit
        target = target_value or chart.target_value

        if not usl or not lsl:
            raise ValueError("Specification limits required for capability analysis")

        # Get data points
        points = self.get_data_points(
            equipment_id=chart.equipment_id,
            measurement_type=chart.measurement_type,
            limit=data_points
        )

        if len(points) < 30:
            logger.warning(f"Capability analysis recommended with at least 30 points (have {len(points)})")

        values = [float(dp.error) for dp in points]

        # Calculate statistics
        mean = statistics.mean(values)
        if len(values) > 1:
            stdev = statistics.stdev(values)
        else:
            stdev = 0.0

        # Process capability (Cp, Cpk) - uses within-subgroup variation
        # For simplicity, using overall stdev as approximation
        tolerance = float(usl - lsl)
        cp = (tolerance / (6 * stdev)) if stdev > 0 else float('inf')

        # Cpk considers process centering
        usl_f = float(usl)
        lsl_f = float(lsl)
        cpu = (usl_f - mean) / (3 * stdev) if stdev > 0 else float('inf')
        cpl = (mean - lsl_f) / (3 * stdev) if stdev > 0 else float('inf')
        cpk = min(cpu, cpl)

        # Process performance (Pp, Ppk) - uses overall variation
        pp = cp  # Same calculation for our purposes
        ppk = cpk

        # Update chart
        chart.cp = Decimal(str(cp)) if cp != float('inf') else None
        chart.cpk = Decimal(str(cpk)) if cpk != float('inf') else None
        chart.pp = Decimal(str(pp)) if pp != float('inf') else None
        chart.ppk = Decimal(str(ppk)) if ppk != float('inf') else None
        chart.upper_spec_limit = usl
        chart.lower_spec_limit = lsl
        chart.target_value = target
        self._save_data()

        return {
            'chart_id': chart_id,
            'equipment_id': chart.equipment_id,
            'measurement_type': chart.measurement_type,
            'cp': cp,
            'cpk': cpk,
            'pp': pp,
            'ppk': ppk,
            'mean': mean,
            'stdev': stdev,
            'usl': float(usl),
            'lsl': float(lsl),
            'target': float(target) if target else None,
            'data_points': len(points),
            'interpretation': self._interpret_capability(cpk)
        }

    def _interpret_capability(self, cpk: float) -> str:
        """Interpret Cpk value"""
        if cpk >= 2.0:
            return "Excellent (6-sigma capable)"
        elif cpk >= 1.67:
            return "Very Good (5-sigma capable)"
        elif cpk >= 1.33:
            return "Good (4-sigma capable)"
        elif cpk >= 1.0:
            return "Adequate (3-sigma capable)"
        elif cpk >= 0.67:
            return "Marginal - improvement needed"
        else:
            return "Poor - immediate action required"

    # ==================== Trend Analysis ====================

    def analyze_trend(
        self,
        equipment_id: str,
        measurement_type: str,
        data_points: int = 50
    ) -> TrendAnalysis:
        """
        Analyze trend in measurement data

        Args:
            equipment_id: Equipment ID
            measurement_type: Measurement type
            data_points: Number of recent points to analyze

        Returns:
            TrendAnalysis object
        """
        points = self.get_data_points(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            limit=data_points
        )

        if len(points) < 10:
            return TrendAnalysis(
                equipment_id=equipment_id,
                measurement_type=measurement_type,
                trend_type='insufficient_data',
                slope=None,
                r_squared=None,
                description=f"Insufficient data for trend analysis ({len(points)} points)"
            )

        # Simple linear regression
        x_values = list(range(len(points)))
        y_values = [float(dp.error) for dp in points]

        slope, r_squared = self._linear_regression(x_values, y_values)

        # Determine trend type
        if r_squared < 0.3:
            trend_type = 'unstable'
            description = "No clear trend - data appears random"
        elif abs(slope) < 0.01:
            trend_type = 'stable'
            description = "Stable - no significant trend"
        elif slope > 0:
            trend_type = 'increasing'
            description = f"Increasing trend (slope: {slope:.4f})"
        else:
            trend_type = 'decreasing'
            description = f"Decreasing trend (slope: {slope:.4f})"

        return TrendAnalysis(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            trend_type=trend_type,
            slope=slope,
            r_squared=r_squared,
            description=description
        )

    def _linear_regression(
        self,
        x_values: List[float],
        y_values: List[float]
    ) -> Tuple[float, float]:
        """
        Simple linear regression

        Returns:
            (slope, r_squared)
        """
        n = len(x_values)
        if n < 2:
            return 0.0, 0.0

        mean_x = statistics.mean(x_values)
        mean_y = statistics.mean(y_values)

        # Calculate slope
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
        denominator = sum((x - mean_x) ** 2 for x in x_values)

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared
        ss_res = sum((y - (slope * x + (mean_y - slope * mean_x))) ** 2
                     for x, y in zip(x_values, y_values))
        ss_tot = sum((y - mean_y) ** 2 for y in y_values)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return slope, r_squared

    # ==================== Quality Metrics ====================

    def get_quality_metrics(
        self,
        equipment_id: str,
        measurement_type: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get quality metrics for equipment over period

        Args:
            equipment_id: Equipment ID
            measurement_type: Measurement type
            period_days: Period for metrics (days)

        Returns:
            Dictionary with quality metrics
        """
        start_date = datetime.now() - timedelta(days=period_days)

        points = self.get_data_points(
            equipment_id=equipment_id,
            measurement_type=measurement_type,
            start_date=start_date
        )

        if not points:
            return {
                'equipment_id': equipment_id,
                'measurement_type': measurement_type,
                'period_days': period_days,
                'data_points': 0,
                'message': 'No data available'
            }

        values = [float(dp.error) for dp in points]

        # Get control chart for limits
        charts = [
            c for c in self._control_charts.values()
            if c.equipment_id == equipment_id and c.measurement_type == measurement_type
        ]
        chart = charts[0] if charts else None

        # Calculate metrics
        mean_error = statistics.mean(values)
        std_error = statistics.stdev(values) if len(values) > 1 else 0.0
        max_error = max(values)
        min_error = min(values)

        # Count violations if chart exists
        violations_count = 0
        if chart:
            violations = self.check_control_violations(chart.chart_id, check_recent=len(points))
            violations_count = len(violations)

        return {
            'equipment_id': equipment_id,
            'measurement_type': measurement_type,
            'period_days': period_days,
            'data_points': len(points),
            'mean_error': mean_error,
            'std_error': std_error,
            'max_error': max_error,
            'min_error': min_error,
            'violations_count': violations_count,
            'chart_id': chart.chart_id if chart else None,
        }
