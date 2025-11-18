"""
Setup configuration for PV Test Report Automation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pv-test-report-automation",
    version="1.0.0",
    author="ASA Lab Team",
    author_email="contact@asa-lab.com",
    description="Automated PV module testing and reporting system with IEC 61215 compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ganeshgowri-ASA/pv-test-report-automation",
    project_urls={
        "Bug Reports": "https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues",
        "Source": "https://github.com/ganeshgowri-ASA/pv-test-report-automation",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-dateutil>=2.8.2",
        "typing-extensions>=4.5.0",
        "pydantic>=2.0.0",
        "reportlab>=4.0.4",
        "openpyxl>=3.1.2",
        "pandas>=2.0.3",
        "matplotlib>=3.7.2",
        "jsonschema>=4.19.0",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "pylint>=2.17.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "numpy>=1.24.3",
            "scipy>=1.11.2",
        ],
        "web": [
            "fastapi>=0.103.0",
            "uvicorn>=0.23.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "pv-test=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "photovoltaic",
        "pv",
        "solar",
        "testing",
        "IEC 61215",
        "ISO 17025",
        "hail impact",
        "quality assurance",
        "laboratory automation",
        "test reporting",
    ],
)
