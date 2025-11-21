"""
IEC 61215: Terrestrial Photovoltaic (PV) Modules - Design Qualification and Type Approval
Complete implementation of design qualification testing
"""

from typing import Dict, Any, List
from .base import ProtocolBase, TestSequence, SampleSpecification, TestParameter


class IEC61215Protocol(ProtocolBase):
    """IEC 61215 - PV Module Design Qualification"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 61215"
        self.protocol_version = "2021"
        self.full_title = "Terrestrial photovoltaic (PV) modules - Design qualification and type approval"
        self.description = "Qualification testing for PV module design and performance"

        self._initialize_test_sequences()
        self._initialize_equipment()
        self._initialize_environmental_conditions()

    def _initialize_test_sequences(self):
        """Initialize test sequences as per IEC 61215"""
        self.test_sequences = [
            TestSequence(
                sequence_number=1,
                name="Visual Inspection and Performance",
                description="Initial visual inspection and power measurement",
                required_tests=[
                    "10.1 Visual Inspection",
                    "10.2 Maximum Power Determination",
                    "10.3 Insulation Test",
                ],
                estimated_duration_hours=4.0
            ),
            TestSequence(
                sequence_number=2,
                name="Environmental Testing",
                description="UV preconditioning and thermal cycling",
                required_tests=[
                    "10.10 UV Preconditioning Test",
                    "10.11 Thermal Cycling Test",
                    "10.12 Humidity-Freeze Test",
                ],
                estimated_duration_hours=240.0  # 10 days
            ),
            TestSequence(
                sequence_number=3,
                name="Mechanical Stress Testing",
                description="Mechanical load and hail impact tests",
                required_tests=[
                    "10.16 Mechanical Load Test",
                    "10.17 Hail Impact Test",
                ],
                estimated_duration_hours=16.0
            ),
            TestSequence(
                sequence_number=4,
                name="Electrical Safety",
                description="Wet leakage current and bypass diode tests",
                required_tests=[
                    "10.15 Wet Leakage Current Test",
                    "10.18 Bypass Diode Test",
                ],
                estimated_duration_hours=8.0
            ),
            TestSequence(
                sequence_number=5,
                name="Hot-Spot Endurance",
                description="Hot-spot endurance testing",
                required_tests=[
                    "10.9 Hot-Spot Endurance Test",
                ],
                estimated_duration_hours=24.0
            ),
        ]

    def _initialize_equipment(self):
        """Required equipment for IEC 61215 testing"""
        self.required_equipment = [
            "Solar Simulator (Class AAA)",
            "Environmental Chamber (-40°C to +85°C)",
            "UV Chamber (280-400 nm)",
            "Mechanical Load Tester (up to 5400 Pa)",
            "Hail Impact Tester (ice balls 25mm)",
            "Insulation Resistance Tester (500V/1000V)",
            "IV Curve Tracer",
            "Bypass Diode Tester",
            "Infrared Camera (Thermal Imaging)",
            "Electroluminescence (EL) Imaging System",
        ]

    def _initialize_environmental_conditions(self):
        """Standard environmental conditions"""
        self.environmental_conditions = {
            'STC': {
                'irradiance': 1000,  # W/m²
                'temperature': 25,  # °C
                'spectrum': 'AM 1.5',
            },
            'NOCT': {
                'irradiance': 800,  # W/m²
                'ambient_temp': 20,  # °C
                'wind_speed': 1,  # m/s
            },
            'thermal_cycling': {
                'min_temp': -40,  # °C
                'max_temp': 85,  # °C
                'cycles': 200,
                'dwell_time': '2-4 hours',
            },
        }

    def get_test_matrix(self) -> Dict[str, Any]:
        """Complete test matrix for IEC 61215"""
        return {
            'MST 01': {
                'name': 'Visual Inspection',
                'section': '10.1',
                'type': 'visual',
                'criteria': 'No defects, cracks, or delamination',
            },
            'MST 02': {
                'name': 'Maximum Power Determination',
                'section': '10.2',
                'type': 'electrical',
                'criteria': 'Within ±3% of rated power',
                'conditions': 'STC',
            },
            'MST 03': {
                'name': 'Insulation Test',
                'section': '10.3',
                'type': 'electrical',
                'min_resistance': '40 MΩ',
                'test_voltage': '1000V DC',
            },
            'MST 09': {
                'name': 'Hot-Spot Endurance Test',
                'section': '10.9',
                'type': 'thermal',
                'duration': '1 hour at Isc',
                'max_temp_rise': '40°C above ambient',
            },
            'MST 10': {
                'name': 'UV Preconditioning Test',
                'section': '10.10',
                'type': 'environmental',
                'dose': '15 kWh/m²',
                'spectrum': '280-400 nm',
            },
            'MST 11': {
                'name': 'Thermal Cycling Test',
                'section': '10.11',
                'type': 'environmental',
                'cycles': 200,
                'temp_range': '-40°C to +85°C',
                'max_power_degradation': '5%',
            },
            'MST 12': {
                'name': 'Humidity-Freeze Test',
                'section': '10.12',
                'type': 'environmental',
                'cycles': 10,
                'conditions': '85°C/85%RH to -40°C',
                'max_power_degradation': '5%',
            },
            'MST 15': {
                'name': 'Wet Leakage Current Test',
                'section': '10.15',
                'type': 'safety',
                'max_leakage': '1 mA',
                'test_voltage': '1.2 × Voc',
            },
            'MST 16': {
                'name': 'Mechanical Load Test',
                'section': '10.16',
                'type': 'mechanical',
                'loads': [2400, 5400],  # Pa
                'cycles': [3, 1],
                'max_power_degradation': '5%',
            },
            'MST 17': {
                'name': 'Hail Impact Test',
                'section': '10.17',
                'type': 'mechanical',
                'ice_ball_diameter': '25 mm',
                'impact_velocity': '23 m/s',
                'impact_points': 11,
            },
            'MST 18': {
                'name': 'Bypass Diode Test',
                'section': '10.18',
                'type': 'electrical',
                'criteria': 'Diode functional, no overheating',
            },
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        """Validate sample suitability for IEC 61215 testing"""
        # Check if module type is supported
        supported_types = ['Mono-Si', 'Poly-Si', 'Thin-Film', 'PERC', 'HJT', 'TOPCon']

        if sample.module_type not in supported_types:
            return False, f"Module type {sample.module_type} not in supported types: {supported_types}"

        # Check power rating
        if sample.rated_power < 10 or sample.rated_power > 700:
            return False, f"Rated power {sample.rated_power}W outside typical range (10-700W)"

        # Check voltage
        if sample.voltage_max > 1500:
            return False, f"Maximum voltage {sample.voltage_max}V exceeds typical system limit (1500V)"

        return True, "Sample meets IEC 61215 testing requirements"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        """Get specific acceptance criteria for a test"""
        criteria_map = {
            'Visual Inspection': {
                'no_cracks': True,
                'no_delamination': True,
                'no_corrosion': True,
                'solder_bonds_intact': True,
            },
            'Maximum Power Determination': {
                'tolerance': '±3%',
                'min_fill_factor': 0.70,
            },
            'Thermal Cycling Test': {
                'max_power_degradation': 5.0,  # %
                'max_insulation_drop': 50.0,  # %
                'no_major_visual_defects': True,
            },
            'Hail Impact Test': {
                'no_cracks': True,
                'no_permanent_deformation': True,
                'max_power_degradation': 5.0,  # %
            },
        }

        return criteria_map.get(test_name, {'criteria': 'As per IEC 61215 standard'})
