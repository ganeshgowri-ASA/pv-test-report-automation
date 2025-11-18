"""
Setup script for PV Test Report Automation ingestion module.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pv-test-report-automation",
    version="1.0.0",
    author="PV Testing Lab",
    description="Comprehensive PV test lab report automation with data ingestion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ganeshgowri-ASA/pv-test-report-automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "python-dateutil>=2.8.2",
        "lxml>=4.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
        ],
        "mpp": [
            "mpxj>=1.0.0",
            "JPype1>=1.4.0",
        ],
        "imaging": [
            "cairosvg>=2.7.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pv-ingest=ingestion.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ingestion": ["sample_data/*"],
    },
)
