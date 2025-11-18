"""
IEC 61853 Example Usage
========================

Demonstrates complete workflow for IEC 61853 testing.

This example shows:
1. Basic test execution
2. Custom configuration
3. Data analysis
4. Energy rating
5. Report generation
"""

import logging
from datetime import datetime

from protocols.iec_61853 import (
    IEC61853TestController,
    MatrixTestConfig,
    TestSequenceMode,
    StabilizationCriteria
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """Example 1: Basic usage with default settings"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage")
    print("="*70 + "\n")

    # Initialize test controller
    test = IEC61853TestController(
        module_serial="PV-2025-001234",
        test_lab="NABL Test Laboratory XYZ",
        module_manufacturer="SolarTech Industries",
        module_model="ST-300M-60",
        module_technology="mono-Si",
        rated_power=300.0,
        test_engineer="John Doe",
        use_simulated_hardware=True  # Use simulation for demo
    )

    # Run complete test series
    print("Running complete IEC 61853 test series...")
    results = test.run_complete_test_series(
        include_spectral=True,
        include_energy_rating=True
    )

    # Print summary
    summary = test.get_summary()
    print("\nTest Summary:")
    print(f"  Test ID: {summary['test_id']}")
    print(f"  Status: {summary['status']}")
    print(f"  Matrix points: {summary['matrix']['successful']}/{summary['matrix']['total_points']}")
    print(f"  γ (Pmax): {summary['temperature_coefficients']['gamma_pmax']:.3f} %/°C")

    # Export results
    test.export_results(output_dir="./example_results")

    # Generate report
    test.generate_report("example_1_report.pdf")

    print("\n✓ Example 1 completed successfully!")


def example_2_custom_configuration():
    """Example 2: Custom test configuration"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Custom Configuration")
    print("="*70 + "\n")

    test = IEC61853TestController(
        module_serial="PV-2025-002345",
        test_lab="Advanced PV Testing Center",
        rated_power=350.0,
        use_simulated_hardware=True
    )

    # Custom matrix configuration
    # Using fewer points for faster testing
    config = MatrixTestConfig(
        temperatures=[-10, 15, 25, 40, 60],  # 5 custom temperature points
        irradiances=[200, 500, 800, 1000, 1200],  # 5 custom irradiance levels
        sequence_mode=TestSequenceMode.OPTIMIZED,  # Minimize thermal cycles
        max_retries=2,
        validation_enabled=True
    )

    # Custom stabilization criteria for faster testing
    config.stabilization_criteria = StabilizationCriteria(
        tolerance=1.5,  # ±1.5°C
        duration=300,   # 5 minutes
        max_wait_time=1800,  # 30 minutes max
        sample_interval=5.0
    )

    print(f"Running custom matrix: {len(config.temperatures)} temps × {len(config.irradiances)} irrad")

    # Run with custom config
    matrix_results = test.run_performance_matrix(config=config)

    print(f"\nCompleted: {matrix_results.successful_points}/{matrix_results.total_points} points")
    print(f"Duration: {matrix_results.total_duration/3600:.2f} hours")

    # Analyze
    analysis = test.analyze_performance()

    print("\nTemperature Coefficients:")
    print(f"  α (Isc): {analysis['temperature_coefficients']['alpha_isc']:+.3f} %/°C")
    print(f"  β (Voc): {analysis['temperature_coefficients']['beta_voc']:+.3f} %/°C")
    print(f"  γ (Pmax): {analysis['temperature_coefficients']['gamma_pmax']:+.3f} %/°C")

    print("\nPerformance Surface:")
    print(f"  R²: {analysis['performance_surface']['r_squared']:.4f}")
    print(f"  RMSE: {analysis['performance_surface']['rmse']:.2f} W")

    print("\n✓ Example 2 completed successfully!")


def example_3_detailed_analysis():
    """Example 3: Detailed data analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Detailed Analysis")
    print("="*70 + "\n")

    test = IEC61853TestController(
        module_serial="PV-2025-003456",
        test_lab="Research Laboratory",
        rated_power=300.0,
        use_simulated_hardware=True
    )

    # Quick matrix test
    config = MatrixTestConfig(
        temperatures=[0, 25, 50],
        irradiances=[200, 600, 1000]
    )
    config.stabilization_criteria.duration = 5.0  # Fast stabilization for demo

    test.run_performance_matrix(config=config)
    test.analyze_performance()

    # Access analyzer directly
    analyzer = test.analyzer

    # Get performance surface
    surface = analyzer.get_performance_surface()

    print("Performance Predictions:")
    test_conditions = [
        (1000, 25, "STC"),
        (800, 35, "Hot sunny day"),
        (400, 15, "Cool cloudy day"),
        (1100, 50, "High irradiance, hot")
    ]

    for irrad, temp, condition in test_conditions:
        pmax = surface.predict(irradiance=irrad, temperature=temp)
        print(f"  {condition:20s}: {pmax:6.2f} W @ {irrad:4.0f} W/m², {temp:3.0f}°C")

    # Get temperature coefficients
    temp_coeff = analyzer.get_temperature_coefficients()

    print("\nTemperature Coefficient Details:")
    print(f"  α (Isc): {temp_coeff.alpha_isc:+.4f} %/°C ({temp_coeff.alpha_isc_abs:+.4f} A/°C)")
    print(f"  β (Voc): {temp_coeff.beta_voc:+.4f} %/°C ({temp_coeff.beta_voc_abs:+.4f} V/°C)")
    print(f"  γ (Pmax): {temp_coeff.gamma_pmax:+.4f} %/°C ({temp_coeff.gamma_pmax_abs:+.4f} W/°C)")
    print(f"  R² (Pmax): {temp_coeff.r_squared_pmax:.4f}")

    # Quality metrics
    quality = analyzer.calculate_quality_metrics()

    print("\nData Quality Metrics:")
    print(f"  Fill Factor: {quality['fill_factor']['mean']:.4f} ± {quality['fill_factor']['std']:.4f}")
    print(f"  Temp Stability: {quality['temperature_stability']['mean']:.2f}°C (max: {quality['temperature_stability']['max']:.2f}°C)")
    print(f"  Irrad Uniformity: {quality['irradiance_uniformity']['mean']:.1f}% (min: {quality['irradiance_uniformity']['min']:.1f}%)")
    print(f"  Data Completeness: {quality['data_completeness']['success_rate']*100:.1f}%")

    print("\n✓ Example 3 completed successfully!")


def example_4_energy_rating():
    """Example 4: Energy rating calculations"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Energy Rating Calculations")
    print("="*70 + "\n")

    test = IEC61853TestController(
        module_serial="PV-2025-004567",
        test_lab="Energy Rating Center",
        rated_power=300.0,
        use_simulated_hardware=True
    )

    # Quick test
    config = MatrixTestConfig(
        temperatures=[0, 25, 50],
        irradiances=[400, 800, 1000]
    )
    config.stabilization_criteria.duration = 5.0

    test.run_performance_matrix(config=config)
    test.analyze_performance()

    # Calculate energy ratings for all standard locations
    print("Calculating energy ratings for standard locations...")
    energy_results = test.calculate_energy_ratings()

    print("\nEnergy Rating Results:")
    print(f"{'Location':<20s} {'Climate':<20s} {'Energy (kWh)':<15s} {'Yield (kWh/kWp)':<15s} {'Class':<8s}")
    print("-" * 85)

    for loc_name, loc_data in energy_results['location_results'].items():
        print(f"{loc_name:<20s} "
              f"{loc_data['climate']:<20s} "
              f"{loc_data['annual_energy_kwh']:>12.1f}   "
              f"{loc_data['specific_yield_kwh_kwp']:>12.1f}   "
              f"{loc_data['energy_class']:<8s}")

    print("\nEnergy Rating Summary:")
    summary = energy_results['summary']
    print(f"  Locations tested: {summary['locations_tested']}")
    print(f"  Average annual energy: {summary['average_annual_energy']:.1f} kWh")
    print(f"  Average specific yield: {summary['average_specific_yield']:.1f} kWh/kWp")
    print(f"  Range: {summary['min_energy']:.1f} - {summary['max_energy']:.1f} kWh")

    print("\n✓ Example 4 completed successfully!")


def example_5_spectral_angular():
    """Example 5: Spectral and angular response testing"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Spectral & Angular Response")
    print("="*70 + "\n")

    test = IEC61853TestController(
        module_serial="PV-2025-005678",
        test_lab="Optical Characterization Lab",
        rated_power=300.0,
        use_simulated_hardware=True
    )

    print("Running spectral and angular response tests...")
    results = test.run_spectral_angular_tests()

    # Spectral response
    spectral = results['spectral_response']
    print("\nSpectral Response:")
    print(f"  Peak wavelength: {spectral['peak_wavelength']:.1f} nm")
    print(f"  Mismatch factor: {spectral['mismatch_factor']:.4f}")
    print(f"  Curve points: {spectral['curve_points']}")

    # Angular response
    angular = results['angular_response']
    print("\nAngular Response:")
    print(f"  IAM factor: {angular['iam_factor']:.4f}")
    print(f"  Curve points: {angular['curve_points']}")

    print("\nOptical Characterization Complete!")
    print(f"  Standard: {results['standard']}")
    print(f"  Timestamp: {results['timestamp']}")

    print("\n✓ Example 5 completed successfully!")


def run_all_examples():
    """Run all examples"""
    print("\n" + "#"*70)
    print("# IEC 61853 PROTOCOL - EXAMPLE DEMONSTRATIONS")
    print("#"*70)

    try:
        # Run examples
        example_1_basic_usage()
        # example_2_custom_configuration()  # Commented out for quick demo
        # example_3_detailed_analysis()
        # example_4_energy_rating()
        # example_5_spectral_angular()

        print("\n" + "#"*70)
        print("# ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("#"*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
