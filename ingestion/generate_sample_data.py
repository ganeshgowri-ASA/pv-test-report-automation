"""
Generate Sample Excel Files for Testing

Creates sample Excel files for different IEC test standards
and data patterns used in PV testing.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows


def create_sample_data_directory():
    """Create sample_data directory if it doesn't exist."""
    sample_dir = Path(__file__).parent / 'sample_data'
    sample_dir.mkdir(exist_ok=True)
    return sample_dir


def generate_iec61215_mst_data(output_path: Path):
    """
    Generate sample IEC 61215 MST (Damp Heat) test data.

    Creates a workbook with:
    - Metadata in header rows
    - Time-series data of temperature and humidity
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "DampHeat"

    # Add metadata
    ws['A1'] = 'IEC 61215 Module Stability Test - Damp Heat'
    ws['A1'].font = Font(bold=True, size=14)

    ws['A3'] = 'Module Serial:'
    ws['B3'] = 'PV-MODULE-12345'

    ws['A4'] = 'Test Start Date:'
    ws['B4'] = '2024-01-15'

    ws['A5'] = 'Test Duration:'
    ws['B5'] = '1000 hours'

    ws['A6'] = 'Operator:'
    ws['B6'] = 'John Doe'

    # Add column headers
    headers = ['Time (h)', 'Temperature (°C)', 'Humidity (%RH)', 'Chamber ID']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

    # Generate test data (1000 hours, 1-hour intervals)
    np.random.seed(42)
    time_points = np.arange(0, 1001, 1)

    # IEC 61215: 85°C ± 2°C, 85% RH ± 3%
    temperatures = 85 + np.random.normal(0, 0.5, len(time_points))
    humidity = 85 + np.random.normal(0, 1.0, len(time_points))

    # Add data rows
    for i, t in enumerate(time_points):
        ws.cell(row=9+i, column=1, value=float(t))
        ws.cell(row=9+i, column=2, value=float(temperatures[i]))
        ws.cell(row=9+i, column=3, value=float(humidity[i]))
        ws.cell(row=9+i, column=4, value='CHAMBER-01')

    wb.save(output_path)
    print(f"Created: {output_path}")


def generate_iec61730_impact_data(output_path: Path):
    """
    Generate sample IEC 61730 mechanical impact test data.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "ImpactTest"

    # Add metadata
    ws['A1'] = 'IEC 61730 Mechanical Impact Test (Ball Drop)'
    ws['A1'].font = Font(bold=True, size=14)

    ws['A3'] = 'Module Serial:'
    ws['B3'] = 'PV-MODULE-67890'

    ws['A4'] = 'Test Date:'
    ws['B4'] = '2024-02-20'

    # Add column headers
    headers = ['Test No.', 'Drop Height (mm)', 'Ball Mass (g)', 'Impact Location', 'Result', 'Notes']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=6, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

    # Generate test data (10 impact tests)
    np.random.seed(42)
    locations = ['Center', 'Corner 1', 'Corner 2', 'Corner 3', 'Corner 4', 'Edge 1', 'Edge 2', 'Edge 3', 'Edge 4', 'Junction Box']

    for i in range(10):
        ws.cell(row=7+i, column=1, value=i+1)
        ws.cell(row=7+i, column=2, value=1270 + np.random.randint(-5, 5))  # IEC 61730: 1270mm
        ws.cell(row=7+i, column=3, value=227 + np.random.uniform(-1, 1))  # IEC 61730: 227g
        ws.cell(row=7+i, column=4, value=locations[i])
        ws.cell(row=7+i, column=5, value='Pass')  # All pass in this sample
        ws.cell(row=7+i, column=6, value='No visible damage')

    wb.save(output_path)
    print(f"Created: {output_path}")


def generate_iec62716_ammonia_data(output_path: Path):
    """
    Generate sample IEC 62716 ammonia corrosion test data.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "AmmoniaExposure"

    # Add metadata
    ws['A1'] = 'IEC 62716 Ammonia Corrosion Test'
    ws['A1'].font = Font(bold=True, size=14)

    ws['A3'] = 'Test Date:'
    ws['B3'] = '2024-03-10'

    ws['A4'] = 'Chamber ID:'
    ws['B4'] = 'AMMONIA-CHAMBER-01'

    # Add column headers
    headers = ['Time (h)', 'NH3 Concentration (ppm)', 'Temperature (°C)', 'Humidity (%RH)']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=6, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

    # Generate test data (168 hours = 7 days, hourly)
    np.random.seed(42)
    time_points = np.arange(0, 169, 1)

    # IEC 62716: 20-40 ppm NH3
    nh3_concentration = 30 + np.random.normal(0, 2, len(time_points))
    temperatures = 50 + np.random.normal(0, 1, len(time_points))
    humidity = 75 + np.random.normal(0, 2, len(time_points))

    for i, t in enumerate(time_points):
        ws.cell(row=7+i, column=1, value=float(t))
        ws.cell(row=7+i, column=2, value=float(nh3_concentration[i]))
        ws.cell(row=7+i, column=3, value=float(temperatures[i]))
        ws.cell(row=7+i, column=4, value=float(humidity[i]))

    wb.save(output_path)
    print(f"Created: {output_path}")


def generate_iec61701_salt_mist_data(output_path: Path):
    """
    Generate sample IEC 61701 salt mist corrosion test data.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "SaltMist"

    # Add metadata
    ws['A1'] = 'IEC 61701 Salt Mist Corrosion Test'
    ws['A1'].font = Font(bold=True, size=14)

    ws['A3'] = 'Test Date:'
    ws['B3'] = '2024-04-05'

    ws['A4'] = 'Severity Level:'
    ws['B4'] = '6'

    # Add column headers
    headers = ['Sample ID', 'Initial Mass (g)', 'Final Mass (g)', 'Mass Loss (g)', 'Visual Inspection', 'Result']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=6, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

    # Generate test data (5 samples)
    np.random.seed(42)
    sample_ids = ['MODULE-A', 'MODULE-B', 'MODULE-C', 'MODULE-D', 'MODULE-E']

    for i, sample_id in enumerate(sample_ids):
        initial_mass = 15000 + np.random.uniform(-100, 100)
        mass_loss = np.random.uniform(0.1, 0.8)
        final_mass = initial_mass - mass_loss

        ws.cell(row=7+i, column=1, value=sample_id)
        ws.cell(row=7+i, column=2, value=round(initial_mass, 2))
        ws.cell(row=7+i, column=3, value=round(final_mass, 2))
        ws.cell(row=7+i, column=4, value=round(mass_loss, 2))
        ws.cell(row=7+i, column=5, value='Minor corrosion on frame')
        ws.cell(row=7+i, column=6, value='Pass')

    wb.save(output_path)
    print(f"Created: {output_path}")


def generate_iv_curve_data(output_path: Path):
    """
    Generate sample I-V curve measurement data.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "IV_Curve"

    # Add metadata
    ws['A1'] = 'Module Serial:'
    ws['B1'] = 'PV-MODULE-99999'

    ws['A2'] = 'Test Date:'
    ws['B2'] = '2024-05-12'

    ws['A3'] = 'Irradiance:'
    ws['B3'] = '1000 W/m²'

    ws['A4'] = 'Module Temperature:'
    ws['B4'] = '25 °C'

    ws['A5'] = 'Test Standard:'
    ws['B5'] = 'IEC 61215'

    # Add column headers
    headers = ['Voltage (V)', 'Current (A)', 'Power (W)']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=7, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

    # Generate I-V curve data
    # Typical PV module: Voc ≈ 45V, Isc ≈ 9A, Pmax ≈ 300W
    np.random.seed(42)

    Voc = 45.0
    Isc = 9.0
    Vmp = 37.5
    Imp = 8.0

    # Generate voltage points from 0 to Voc
    voltages = np.linspace(0, Voc, 100)

    # I-V curve model (simplified)
    currents = []
    for V in voltages:
        if V < Vmp:
            # Before MPP: nearly constant current
            I = Isc * (1 - (V / Voc) ** 0.3)
        else:
            # After MPP: current drops rapidly
            I = Isc * (1 - (V / Voc)) ** 4

        # Add small noise
        I += np.random.normal(0, 0.05)
        currents.append(max(0, I))

    currents = np.array(currents)
    powers = voltages * currents

    # Add data rows
    for i in range(len(voltages)):
        ws.cell(row=8+i, column=1, value=round(voltages[i], 3))
        ws.cell(row=8+i, column=2, value=round(currents[i], 3))
        ws.cell(row=8+i, column=3, value=round(powers[i], 3))

    wb.save(output_path)
    print(f"Created: {output_path}")


def generate_multi_header_data(output_path: Path):
    """
    Generate sample data with multi-level headers.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "MultiHeader"

    # Create multi-level headers
    # Row 1: Main categories
    ws.merge_cells('A1:B1')
    ws['A1'] = 'Environmental Conditions'
    ws['A1'].font = Font(bold=True)
    ws['A1'].fill = PatternFill(start_color='DDDDDD', end_color='DDDDDD', fill_type='solid')

    ws.merge_cells('C1:E1')
    ws['C1'] = 'Electrical Measurements'
    ws['C1'].font = Font(bold=True)
    ws['C1'].fill = PatternFill(start_color='DDDDDD', end_color='DDDDDD', fill_type='solid')

    # Row 2: Sub-headers
    sub_headers = ['Temperature (°C)', 'Humidity (%RH)', 'Voltage (V)', 'Current (A)', 'Power (W)']
    for col, header in enumerate(sub_headers, start=1):
        cell = ws.cell(row=2, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='EEEEEE', end_color='EEEEEE', fill_type='solid')

    # Add sample data
    np.random.seed(42)
    for i in range(50):
        ws.cell(row=3+i, column=1, value=round(25 + np.random.normal(0, 2), 1))
        ws.cell(row=3+i, column=2, value=round(50 + np.random.normal(0, 5), 1))
        ws.cell(row=3+i, column=3, value=round(37 + np.random.normal(0, 0.5), 2))
        ws.cell(row=3+i, column=4, value=round(8 + np.random.normal(0, 0.2), 2))
        ws.cell(row=3+i, column=5, value=round(300 + np.random.normal(0, 10), 1))

    wb.save(output_path)
    print(f"Created: {output_path}")


def main():
    """Generate all sample Excel files."""
    print("Generating sample Excel files for testing...")

    sample_dir = create_sample_data_directory()

    # Generate different test data files
    generate_iec61215_mst_data(sample_dir / 'iec61215_mst.xlsx')
    generate_iec61730_impact_data(sample_dir / 'iec61730_impact.xlsx')
    generate_iec62716_ammonia_data(sample_dir / 'iec62716_ammonia.xlsx')
    generate_iec61701_salt_mist_data(sample_dir / 'iec61701_salt_mist.xlsx')
    generate_iv_curve_data(sample_dir / 'iv_curve_data.xlsx')
    generate_multi_header_data(sample_dir / 'multi_header_data.xlsx')

    print(f"\nAll sample files created in: {sample_dir}")
    print("\nGenerated files:")
    for file in sample_dir.glob('*.xlsx'):
        print(f"  - {file.name}")


if __name__ == '__main__':
    main()
