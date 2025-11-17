#!/usr/bin/env python3
"""
Verification script for PV Test Report Automation setup
Checks if all required files and dependencies are in place
"""

import sys
from pathlib import Path
import subprocess


def check_files():
    """Check if all required files exist"""
    print("Checking file structure...")

    required_files = [
        "src/ui/app.py",
        "src/ui/pages/dashboard.py",
        "src/ui/pages/upload.py",
        "src/ui/pages/create_report.py",
        "src/ui/pages/review.py",
        "src/ui/pages/export.py",
        "src/core/data_ingestion/file_parser.py",
        "requirements.txt",
        ".streamlit/config.toml",
        "README.md"
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
            print(f"  ✗ Missing: {file_path}")
        else:
            print(f"  ✓ Found: {file_path}")

    if missing:
        print(f"\n❌ {len(missing)} file(s) missing!")
        return False
    else:
        print("\n✅ All required files present!")
        return True


def check_dependencies():
    """Check if required Python packages are installed"""
    print("\nChecking Python dependencies...")

    required_packages = [
        'streamlit',
        'pandas',
        'pillow',
        'python-docx',
        'openpyxl',
        'plotly',
        'PyPDF2'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').lower())
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} not installed")
            missing.append(package)

    if missing:
        print(f"\n⚠️  {len(missing)} package(s) not installed!")
        print("\nTo install missing packages, run:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"  Python {version_str}")

    if version.major >= 3 and version.minor >= 8:
        print("  ✅ Python version OK (3.8+ required)")
        return True
    else:
        print("  ❌ Python 3.8+ required!")
        return False


def main():
    """Main verification function"""
    print("=" * 60)
    print("PV Test Report Automation - Setup Verification")
    print("=" * 60)
    print()

    checks = [
        check_python_version(),
        check_files(),
        check_dependencies()
    ]

    print("\n" + "=" * 60)

    if all(checks):
        print("✅ Setup verification PASSED!")
        print("\nYou can now run the app with:")
        print("  streamlit run src/ui/app.py")
    else:
        print("⚠️  Setup verification FAILED!")
        print("\nPlease fix the issues above before running the app.")

    print("=" * 60)


if __name__ == "__main__":
    main()
