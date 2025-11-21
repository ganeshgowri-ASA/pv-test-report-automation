# PV Test Report Automation System - Streamlit Cloud Entry Point
# This file serves as the root entry point for Streamlit Cloud deployment

import sys
from pathlib import Path

# Add streamlit_app directory to Python path
streamlit_app_path = Path(__file__).parent / "streamlit_app"
sys.path.insert(0, str(streamlit_app_path))

# Run the main application
exec(open(streamlit_app_path / "main.py").read())
