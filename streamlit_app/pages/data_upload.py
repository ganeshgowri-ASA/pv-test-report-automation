"""
Data Upload - Multi-format data ingestion module
"""

import streamlit as st

SUPPORTED_FORMATS = {
    "Excel": [".xlsx", ".xls", ".xlsm"],
    "Word": [".docx", ".doc"],
    "PDF": [".pdf"],
    "Images": [".jpg", ".jpeg", ".png", ".tiff", ".bmp"],
    "JSON": [".json"],
    "CSV": [".csv", ".tsv"],
    "XML": [".xml"],
    "Visio": [".vsdx", ".vsd"]
}

def render():
    """Render the data upload page"""
    st.title("📤 Data Upload")
    st.markdown("### Multi-Format Test Data Ingestion")

    st.info("""
    **Supported Formats:** Excel, Word, PDF, Images (JPG/PNG/TIFF), JSON, CSV, XML, Visio
    Upload raw test data, equipment outputs, or existing reports for processing.
    """)

    # Upload type selection
    upload_type = st.radio(
        "Select Upload Type:",
        ["Single File Upload", "Batch Upload", "Equipment Direct Import", "Cloud Storage Import"]
    )

    if upload_type == "Single File Upload":
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["xlsx", "xls", "docx", "pdf", "jpg", "png", "json", "csv", "xml", "vsdx"],
            help="Upload test data in any supported format"
        )

        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
            with col2:
                st.metric("File Type", uploaded_file.type)
            with col3:
                st.metric("Status", "Ready")

            # Processing options
            st.subheader("🔧 Processing Options")

            col_p1, col_p2 = st.columns(2)

            with col_p1:
                auto_extract = st.checkbox("Auto-extract data fields", value=True)
                validate_data = st.checkbox("Validate against protocol", value=True)

            with col_p2:
                use_llm = st.checkbox("LLM-assisted parsing", value=True)
                create_backup = st.checkbox("Create backup", value=True)

            if st.button("🚀 Process File", use_container_width=True):
                with st.spinner("Processing file..."):
                    st.success("✅ File processed successfully!")
                    st.info("Navigate to Test Execution to view extracted data")

    elif upload_type == "Batch Upload":
        st.subheader("📦 Batch Upload")

        uploaded_files = st.file_uploader(
            "Choose multiple files",
            accept_multiple_files=True,
            type=["xlsx", "xls", "docx", "pdf", "jpg", "png", "json", "csv", "xml"]
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files uploaded")

            # Display file list
            for idx, file in enumerate(uploaded_files, 1):
                st.markdown(f"{idx}. **{file.name}** ({file.size / 1024:.2f} KB)")

            if st.button("🚀 Process All Files", use_container_width=True):
                with st.spinner("Processing files..."):
                    progress_bar = st.progress(0)
                    for i in range(len(uploaded_files)):
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    st.success("✅ All files processed!")

    elif upload_type == "Equipment Direct Import":
        st.subheader("🔌 Equipment Direct Import")

        equipment_type = st.selectbox(
            "Select Equipment",
            ["Solar Simulator", "EL Imaging System", "I-V Curve Tracer", "Insulation Tester",
             "Data Logger", "Spectroradiometer", "Thermal Camera"]
        )

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            connection_type = st.radio("Connection Type", ["USB", "Network", "Serial"])

        with col_e2:
            if connection_type == "Network":
                ip_address = st.text_input("IP Address", value="192.168.1.100")
            elif connection_type == "Serial":
                com_port = st.text_input("COM Port", value="COM3")

        if st.button("🔗 Connect to Equipment", use_container_width=True):
            st.info(f"Attempting to connect to {equipment_type}...")

    else:  # Cloud Storage Import
        st.subheader("☁️ Cloud Storage Import")

        storage_provider = st.selectbox(
            "Select Provider",
            ["MinIO (Local)", "AWS S3", "Google Cloud Storage", "Azure Blob Storage"]
        )

        bucket_name = st.text_input("Bucket/Container Name")
        file_path = st.text_input("File Path")

        if st.button("📥 Import from Cloud", use_container_width=True):
            st.info(f"Importing from {storage_provider}...")

    # Data mapping section
    st.markdown("---")
    st.subheader("🗺️ Data Field Mapping")

    with st.expander("Configure Field Mapping", expanded=False):
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown("**Source Fields**")
            st.multiselect("Detected Fields", ["Voc", "Isc", "Pmax", "Vmpp", "Impp", "FF", "Efficiency"])

        with col_m2:
            st.markdown("**Target Protocol Fields**")
            st.multiselect("Required Fields", ["Open Circuit Voltage", "Short Circuit Current", "Maximum Power"])

    # Recent uploads
    st.markdown("---")
    st.subheader("📋 Recent Uploads")

    recent_uploads = [
        {"file": "IV_Curve_Data_2024.xlsx", "date": "2024-11-20 10:30", "status": "Processed"},
        {"file": "EL_Images_Batch_45.zip", "date": "2024-11-20 09:15", "status": "Processed"},
        {"file": "Test_Report_Draft.docx", "date": "2024-11-19 16:45", "status": "Pending"},
    ]

    for upload in recent_uploads:
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.text(upload['file'])
        with col2:
            st.text(upload['date'])
        with col3:
            status_color = "🟢" if upload['status'] == "Processed" else "🟡"
            st.text(f"{status_color} {upload['status']}")
        with col4:
            st.button("View", key=f"view_{upload['file']}")
