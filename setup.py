"""Setup configuration for PV Test Report Automation"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="pv-test-report-automation",
    version="0.1.0",
    author="PV Testing Lab",
    description="World-class PV test lab report automation system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ganeshgowri-ASA/pv-test-report-automation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "pydantic>=2.0.0",
        "Pillow>=9.0.0",
        "pytesseract>=0.3.8",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "advanced": [
            "scikit-image>=0.19.0",
            "matplotlib>=3.5.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="photovoltaic pv testing automation image-processing quality-control",
    project_urls={
        "Documentation": "https://github.com/ganeshgowri-ASA/pv-test-report-automation",
        "Source": "https://github.com/ganeshgowri-ASA/pv-test-report-automation",
        "Tracker": "https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues",
    },
)
