"""Setup configuration for PV Test Report Automation."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="pv-test-report-automation",
    version="0.1.0",
    author="PV Test Lab",
    author_email="lab@example.com",
    description="Automated PV module testing and reporting per IEC standards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ganeshgowri-ASA/pv-test-report-automation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0,<3.0.0",
        "python-dateutil>=2.8.2",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "reporting": [
            "matplotlib>=3.7.0",
            "openpyxl>=3.1.0",
            "reportlab>=4.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
        "instruments": [
            "pyserial>=3.5",
            "pyvisa>=1.13.0",
            "pymodbus>=3.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pv-test=src.cli:main",
        ],
    },
)
