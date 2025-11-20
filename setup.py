"""Setup script for PV Test Report Automation."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pv-test-report-automation",
    version="0.1.0",
    author="PV Test Lab",
    description="World-class PV test lab report automation system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pv-test-report-automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "ocr": [
            "pytesseract>=0.3.10",
            "opencv-python>=4.8.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.0",
        ],
    },
)
