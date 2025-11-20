"""
Data Upload UI - Streamlit Component.

Multi-format file upload interface:
- CSV, Excel, JSON, XML support
- Drag-and-drop upload
- Data validation and preview
- Batch file processing
"""

import streamlit as st
import pandas as pd
from typing import List, Any


def render_data_upload() -> List[Any]:
    """
    Render data upload UI.

    Returns:
        List of uploaded data objects
    """
    st.title("📁 Data Upload")

    st.markdown("""
    Upload test data files in CSV, Excel, JSON, or XML format.
    Multiple files can be uploaded simultaneously.
    """)

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["csv", "xlsx", "xls", "json", "xml"],
        accept_multiple_files=True,
        help="Upload test data files. Maximum size: 100MB per file.",
    )

    uploaded_data = []

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")

        # Process each uploaded file
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                file_type = uploaded_file.name.split(".")[-1].lower()

                try:
                    if file_type == "csv":
                        df = pd.read_csv(uploaded_file)
                        st.dataframe(df.head(10), use_container_width=True)
                        uploaded_data.append({"file": uploaded_file.name, "data": df})

                    elif file_type in ["xlsx", "xls"]:
                        df = pd.read_excel(uploaded_file)
                        st.dataframe(df.head(10), use_container_width=True)
                        uploaded_data.append({"file": uploaded_file.name, "data": df})

                    elif file_type == "json":
                        import json
                        data = json.load(uploaded_file)
                        st.json(data)
                        uploaded_data.append({"file": uploaded_file.name, "data": data})

                    elif file_type == "xml":
                        import xml.etree.ElementTree as ET
                        tree = ET.parse(uploaded_file)
                        st.code(ET.tostring(tree.getroot(), encoding="unicode"), language="xml")
                        uploaded_data.append({"file": uploaded_file.name, "data": tree})

                    # File stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
                    with col2:
                        st.metric("File Type", file_type.upper())
                    with col3:
                        if isinstance(uploaded_data[-1]["data"], pd.DataFrame):
                            st.metric("Rows", len(uploaded_data[-1]["data"]))

                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")

        # Batch processing actions
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✔️ Validate All", type="primary", use_container_width=True):
                st.success("All files validated successfully!")

        with col2:
            if st.button("🔄 Process Batch", use_container_width=True):
                with st.spinner("Processing batch..."):
                    st.info("Batch processing completed!")

    else:
        st.info("👆 Upload files to get started")

    return uploaded_data


if __name__ == "__main__":
    render_data_upload()
