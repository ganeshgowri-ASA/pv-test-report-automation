"""
Example Usage of IEC Protocol Implementations

This module demonstrates how to use each protocol handler with realistic
test data and shows the complete workflow for PV module testing.
"""

import numpy as np
from datetime import datetime

from .iec_60904 import IEC60904
from .iec_61853 import IEC61853
from .iec_62804 import IEC62804
from .iec_62759 import IEC62759


def example_iec_60904():
    """
    Example: IEC 60904 I-V Characteristics Measurement

    Demonstrates how to:
    1. Prepare I-V curve data
    2. Run the calculation
    3. Extract key parameters
    4. Check pass/fail criteria
    """
    print("=" * 70)
    print("IEC 60904 - I-V Characteristics Example")
    print("=" * 70)

    # Create protocol handler
    protocol = IEC60904()

    # Simulate realistic I-V curve data for a 300W crystalline silicon module
    # Typical parameters: Voc=45V, Isc=9.5A, Vmp=37V, Imp=8.1A
    voltage = np.linspace(0, 45, 100)

    # Use single-diode model for realistic I-V curve
    voc = 45.0
    isc = 9.5
    rs = 0.3  # Series resistance
    rsh = 500  # Shunt resistance

    # Simplified current calculation
    current = isc * (1 - voltage / voc) ** 0.8 - voltage / rsh

    # Prepare data dictionary
    iv_data = {
        'voltage': voltage.tolist(),
        'current': current.tolist(),
        'irradiance': 1000.0,  # W/m² (STC)
        'temperature': 25.0,    # °C (STC)
        'area': 1.95,          # m²
        'spectrum': 'AM1.5G'
    }

    # Calculate I-V parameters
    result = protocol.calculate(iv_data)

    # Display results
    print(f"\nTest Date: {result.test_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {result.status.value}")
    print(f"Data Quality: {result.data_quality.value}")

    print("\n--- Key Parameters ---")
    print(f"Isc (Short-circuit current):  {result.measurements['Isc']}")
    print(f"Voc (Open-circuit voltage):   {result.measurements['Voc']}")
    print(f"Pmp (Maximum power):          {result.measurements['Pmp']}")
    print(f"Vmp (Voltage at MPP):         {result.measurements['Vmp']}")
    print(f"Imp (Current at MPP):         {result.measurements['Imp']}")
    print(f"FF (Fill factor):             {result.measurements['FF'].value:.4f}")
    print(f"Efficiency:                   {result.measurements['Efficiency'].value:.2f}%")
    print(f"Rs (Series resistance):       {result.measurements['Rs'].value:.3f} Ω")
    print(f"Rsh (Shunt resistance):       {result.measurements['Rsh'].value:.1f} Ω")

    print("\n--- Pass/Fail Criteria ---")
    for criterion, passed in result.pass_fail_criteria.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{criterion}: {status}")

    return result


def example_iec_61853():
    """
    Example: IEC 61853 Performance Testing and Energy Rating

    Demonstrates how to:
    1. Create a performance matrix
    2. Calculate temperature coefficients
    3. Analyze low irradiance performance
    4. Determine STC power rating
    """
    print("\n" + "=" * 70)
    print("IEC 61853 - Performance Testing Example")
    print("=" * 70)

    # Create protocol handler
    protocol = IEC61853()

    # Define test conditions
    irradiances = [200, 400, 600, 800, 1000, 1100]  # W/m²
    temperatures = [15, 25, 50, 75]  # °C

    # Generate realistic performance matrix
    # Base parameters at STC
    p_stc = 305.0  # W
    alpha_isc = 0.05  # %/°C
    beta_voc = -0.30  # %/°C
    gamma_pmp = -0.40  # %/°C

    power_matrix = []
    voltage_matrix = []
    current_matrix = []

    v_stc = 37.5  # V at STC
    i_stc = 9.6   # A at STC

    for temp in temperatures:
        power_row = []
        voltage_row = []
        current_row = []

        for irr in irradiances:
            # Calculate power with temperature and irradiance effects
            temp_factor = 1 + (gamma_pmp / 100) * (temp - 25)
            irr_factor = irr / 1000
            power = p_stc * irr_factor * temp_factor

            # Calculate voltage and current
            v_temp_factor = 1 + (beta_voc / 100) * (temp - 25)
            i_temp_factor = 1 + (alpha_isc / 100) * (temp - 25)

            voltage = v_stc * v_temp_factor
            current = i_stc * irr_factor * i_temp_factor

            power_row.append(power)
            voltage_row.append(voltage)
            current_row.append(current)

        power_matrix.append(power_row)
        voltage_matrix.append(voltage_row)
        current_matrix.append(current_row)

    # Prepare data dictionary
    performance_data = {
        'irradiances': irradiances,
        'temperatures': temperatures,
        'power_matrix': power_matrix,
        'voltage_matrix': voltage_matrix,
        'current_matrix': current_matrix
    }

    # Calculate performance parameters
    result = protocol.calculate(performance_data)

    # Display results
    print(f"\nTest Date: {result.test_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {result.status.value}")

    print("\n--- STC Power Rating ---")
    print(f"P_STC: {result.measurements['P_STC']}")

    print("\n--- Temperature Coefficients ---")
    print(f"α (Isc):  {result.measurements['alpha_Isc'].value:+.4f} %/°C")
    print(f"β (Voc):  {result.measurements['beta_Voc'].value:+.4f} %/°C")
    print(f"γ (Pmp):  {result.measurements['gamma_Pmp'].value:+.4f} %/°C")

    print("\n--- Low Irradiance Performance ---")
    low_irr = result.measurements['low_irradiance_performance']
    print(f"Power at 200 W/m²:        {low_irr['P_200W']:.2f} W")
    print(f"Power at 400 W/m²:        {low_irr['P_400W']:.2f} W")
    print(f"Performance ratio (200):  {low_irr['performance_ratio_200W']:.3f}")
    print(f"Low light loss (200):     {low_irr['low_light_loss_200W_percent']:.2f}%")

    print("\n--- Pass/Fail Criteria ---")
    for criterion, passed in result.pass_fail_criteria.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{criterion}: {status}")

    return result


def example_iec_62804():
    """
    Example: IEC 62804 PID Testing

    Demonstrates how to:
    1. Set up PID test data
    2. Calculate degradation
    3. Classify PID performance
    4. Analyze recovery
    """
    print("\n" + "=" * 70)
    print("IEC 62804 - PID Testing Example")
    print("=" * 70)

    # Create protocol handler
    protocol = IEC62804()

    # Simulate PID test with time-series data
    hours = np.linspace(0, 96, 25)
    initial_power = 305.0

    # Simulate progressive degradation (Class A: < 5%)
    # Power decreases following exponential decay
    degradation_factor = 0.04  # 4% total degradation
    powers = initial_power * (1 - degradation_factor * (1 - np.exp(-hours / 48)))

    # Prepare data dictionary
    pid_data = {
        'initial_power': initial_power,
        'post_stress_power': powers[-1],
        'stress_voltage': -1000,  # V
        'stress_duration_hours': 96,
        'stress_temperature': 85,  # °C
        'stress_humidity': 85,     # %RH
        'time_series': {
            'hours': hours.tolist(),
            'powers': powers.tolist()
        },
        'leakage_current': {
            'hours': [0, 24, 48, 72, 96],
            'current_mA': [2.1, 2.3, 2.4, 2.3, 2.2]
        },
        'recovery_data': {
            'final_power': 303.5,  # Nearly full recovery
            'duration_hours': 96
        }
    }

    # Calculate PID results
    result = protocol.calculate(pid_data)

    # Display results
    print(f"\nTest Date: {result.test_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {result.status.value}")

    print("\n--- PID Test Conditions ---")
    meta = result.metadata
    print(f"Stress voltage:     {meta['stress_voltage_V']} V")
    print(f"Test duration:      {meta['stress_duration_hours']} hours")
    print(f"Temperature:        {meta['stress_temperature_C']}°C")
    print(f"Humidity:           {meta['stress_humidity_RH']}%RH")

    print("\n--- PID Results ---")
    print(f"Power degradation:  {result.measurements['power_degradation']}")
    print(f"PID Classification: {result.measurements['PID_classification']}")
    print(f"Degradation rate:   {result.measurements['degradation_rate_per_hour'].value:.4f} %/hour")

    print("\n--- Time Series Analysis ---")
    ts = result.measurements['time_series_analysis']
    print(f"Degradation profile: {ts['degradation_profile']}")
    print(f"R² (linear fit):     {ts['r_squared']:.4f}")

    print("\n--- Recovery Analysis ---")
    recovery = result.measurements['recovery_analysis']
    print(f"Recovered power:      {recovery['recovered_power_W']:.2f} W")
    print(f"Recovery percentage:  {recovery['recovery_percentage']:.1f}%")
    print(f"Residual degradation: {recovery['residual_degradation_pct']:.2f}%")
    print(f"Full recovery:        {recovery['full_recovery']}")

    print("\n--- Pass/Fail Criteria ---")
    for criterion, passed in result.pass_fail_criteria.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{criterion}: {status}")

    return result


def example_iec_62759():
    """
    Example: IEC 62759 Transportation Testing

    Demonstrates how to:
    1. Record mechanical load tests
    2. Document visual inspections
    3. Calculate durability score
    4. Assess transportation damage
    """
    print("\n" + "=" * 70)
    print("IEC 62759 - Transportation Testing Example")
    print("=" * 70)

    # Create protocol handler
    protocol = IEC62759()

    # Prepare transportation test data
    transport_data = {
        'initial_power': 305.0,
        'final_power': 302.0,  # 1% degradation
        'transportation_mode': 'SEA',
        'test_sequence': 'ISTA 3A',
        'module_type': 'Framed glass-backsheet',

        # Mechanical load tests
        'mechanical_tests': [
            {
                'type': 'static_front',
                'load': 2400,  # Pa
                'passed': True,
                'defects_found': [],
                'duration': '30min'
            },
            {
                'type': 'static_back',
                'load': 2400,  # Pa
                'passed': True,
                'defects_found': [],
                'duration': '30min'
            },
            {
                'type': 'edge_load',
                'load': 100,  # N/m
                'passed': True,
                'defects_found': [],
                'duration': '15min'
            },
            {
                'type': 'vibration',
                'load': 1.5,  # g's
                'passed': True,
                'defects_found': [],
                'duration': '3hours'
            }
        ],

        # Visual inspections
        'visual_inspections': [
            {
                'time': 'before_test',
                'defects': [],
                'overall_condition': 'excellent'
            },
            {
                'time': 'after_mechanical',
                'defects': [
                    {
                        'type': 'frame_scratch',
                        'severity': 'MINOR',
                        'location': 'corner'
                    }
                ],
                'overall_condition': 'good'
            },
            {
                'time': 'after_vibration',
                'defects': [
                    {
                        'type': 'frame_scratch',
                        'severity': 'MINOR',
                        'location': 'corner'
                    },
                    {
                        'type': 'label_detached',
                        'severity': 'MINOR',
                        'location': 'back'
                    }
                ],
                'overall_condition': 'good'
            }
        ],

        # Insulation resistance
        'insulation_resistance': {
            'value': 180.0  # MΩ
        },

        # Environmental tests
        'environmental_tests': [
            {
                'type': 'thermal_cycling',
                'temperature': 85,
                'humidity': 85,
                'duration_hours': 48
            }
        ],

        # Vibration profile
        'vibration_data': {
            'frequencies': np.linspace(1, 200, 100).tolist(),
            'accelerations': (0.5 + 0.2 * np.random.random(100)).tolist(),
            'axes': ['x', 'y', 'z'],
            'duration': 1.0
        }
    }

    # Calculate transportation test results
    result = protocol.calculate(transport_data)

    # Display results
    print(f"\nTest Date: {result.test_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {result.status.value}")

    print("\n--- Transportation Test Conditions ---")
    meta = result.metadata
    print(f"Transportation mode: {meta['transportation_mode']}")
    print(f"Test sequence:       {meta['test_sequence']}")
    print(f"Module type:         {meta['module_type']}")

    print("\n--- Power Performance ---")
    print(f"Power degradation: {result.measurements['power_degradation']}")

    print("\n--- Mechanical Test Results ---")
    mech = result.measurements['mechanical_test_results']
    print(f"Tests performed:  {mech['total_tests']}")
    print(f"Tests passed:     {mech['tests_passed']}")
    print(f"Tests failed:     {mech['tests_failed']}")
    print(f"Pass rate:        {mech['pass_rate_percent']:.1f}%")
    print(f"Max load applied: {mech['max_load_applied']:.0f} Pa/N")

    print("\n--- Visual Inspection Results ---")
    visual = result.measurements['visual_inspection_results']
    print(f"Total inspections: {visual['total_inspections']}")
    print(f"Total defects:     {visual['total_defects']}")
    print(f"Worst severity:    {visual['worst_severity']}")
    print(f"Assessment:        {visual['overall_assessment']}")

    print("\n--- Insulation Resistance ---")
    print(f"Resistance: {result.measurements['insulation_resistance']}")

    print("\n--- Durability Score ---")
    durability = result.measurements['durability_score']
    print(f"Score:  {durability['score']:.0f}/100")
    print(f"Rating: {durability['rating']}")

    print("\n--- Pass/Fail Criteria ---")
    for criterion, passed in result.pass_fail_criteria.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{criterion}: {status}")

    return result


def run_all_examples():
    """Run all protocol examples"""
    results = {}

    results['iec_60904'] = example_iec_60904()
    results['iec_61853'] = example_iec_61853()
    results['iec_62804'] = example_iec_62804()
    results['iec_62759'] = example_iec_62759()

    print("\n" + "=" * 70)
    print("All Examples Completed Successfully!")
    print("=" * 70)

    return results


if __name__ == '__main__':
    run_all_examples()
