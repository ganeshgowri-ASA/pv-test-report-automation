"""
Upload page for PV Test Report Automation
Handles file uploads and displays uploaded files
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.data_ingestion.file_parser import parse_file, FileParser


def render_upload_page():
    """Render the file upload page"""

    st.title("📤 Upload Test Data")

    st.markdown("""
    Upload your PV test data files here. Supported formats:
    - **Excel**: .xlsx, .xls, .xlsm
    - **Images**: .jpg, .png, .gif, .bmp, .tiff
    - **PDF**: .pdf
    - **Word**: .docx, .doc
    """)

    # Initialize session state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = {}

    st.divider()

    # File uploader
    st.subheader("Upload Files")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=['xlsx', 'xls', 'xlsm', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'pdf', 'docx', 'doc'],
        accept_multiple_files=True,
        help="You can upload multiple files at once"
    )

    if uploaded_files:
        if st.button("Process Uploaded Files", type="primary"):
            process_files(uploaded_files)

    st.divider()

    # Display uploaded files
    st.subheader("📁 Uploaded Files")

    if st.session_state.uploaded_files:
        display_uploaded_files()
    else:
        st.info("No files uploaded yet. Use the file uploader above to get started.")

    st.divider()

    # Quick actions
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear All Files", use_container_width=True):
            if st.session_state.uploaded_files:
                st.session_state.uploaded_files = []
                st.session_state.parsed_data = {}
                st.success("All files cleared!")
                st.rerun()

    with col2:
        if st.button("➡️ Go to Create Report", use_container_width=True, type="primary"):
            if st.session_state.uploaded_files:
                st.session_state.current_page = "Create Report"
                st.rerun()
            else:
                st.warning("Please upload some files first!")


def process_files(uploaded_files):
    """Process and parse uploaded files"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")

        # Check if file already uploaded
        existing_files = [f['name'] for f in st.session_state.uploaded_files]
        if uploaded_file.name in existing_files:
            st.warning(f"File '{uploaded_file.name}' already uploaded. Skipping...")
            continue

        # Parse the file
        try:
            parsed_result = parse_file(uploaded_file, uploaded_file.name)

            # Store file information
            file_info = {
                'name': uploaded_file.name,
                'type': FileParser.get_file_type(uploaded_file.name),
                'size': uploaded_file.size,
                'uploaded_at': datetime.now().isoformat(),
                'parsed': parsed_result.get('success', False),
                'error': parsed_result.get('error')
            }

            st.session_state.uploaded_files.append(file_info)

            # Store parsed data separately
            if parsed_result.get('success'):
                st.session_state.parsed_data[uploaded_file.name] = parsed_result

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")

        # Update progress
        progress = (idx + 1) / len(uploaded_files)
        progress_bar.progress(progress)

    status_text.text("Processing complete!")
    st.success(f"Successfully processed {len(uploaded_files)} file(s)!")


def display_uploaded_files():
    """Display list of uploaded files with details"""

    for idx, file_info in enumerate(st.session_state.uploaded_files):
        with st.expander(f"📄 {file_info['name']}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Type:** {file_info['type'].upper()}")
                st.write(f"**Size:** {format_file_size(file_info['size'])}")
                st.write(f"**Uploaded:** {format_datetime(file_info['uploaded_at'])}")

                if file_info['parsed']:
                    st.success("✅ Successfully parsed")
                else:
                    st.error(f"❌ Parse error: {file_info.get('error', 'Unknown error')}")

            with col2:
                if st.button("🗑️ Remove", key=f"remove_{idx}"):
                    st.session_state.uploaded_files.pop(idx)
                    if file_info['name'] in st.session_state.parsed_data:
                        del st.session_state.parsed_data[file_info['name']]
                    st.rerun()

            # Display parsed data preview
            if file_info['parsed'] and file_info['name'] in st.session_state.parsed_data:
                display_parsed_data_preview(file_info['name'], file_info['type'])


def display_parsed_data_preview(filename, file_type):
    """Display preview of parsed data"""

    parsed_data = st.session_state.parsed_data[filename]

    st.markdown("**Preview:**")

    if file_type == 'excel':
        # Display Excel data
        if 'sheets' in parsed_data:
            sheet_names = list(parsed_data['sheets'].keys())
            selected_sheet = st.selectbox(
                "Select Sheet",
                sheet_names,
                key=f"sheet_{filename}"
            )

            sheet_data = parsed_data['sheets'][selected_sheet]
            st.write(f"**Rows:** {sheet_data['rows']}, **Columns:** {sheet_data['columns']}")

            # Display data preview
            df = sheet_data['data']
            st.dataframe(df.head(10), use_container_width=True)

    elif file_type == 'image':
        # Display image metadata
        metadata = parsed_data.get('metadata', {})
        st.json({
            'Format': metadata.get('format'),
            'Size': f"{metadata.get('width')} x {metadata.get('height')}",
            'Mode': metadata.get('mode')
        })

    elif file_type == 'pdf':
        # Display PDF metadata
        metadata = parsed_data.get('metadata', {})
        st.json({
            'Pages': metadata.get('num_pages'),
            'Info': metadata.get('info', {})
        })

    elif file_type == 'word':
        # Display Word metadata
        metadata = parsed_data.get('metadata', {})
        st.json({
            'Paragraphs': metadata.get('num_paragraphs'),
            'Tables': metadata.get('num_tables'),
            'Properties': metadata.get('properties', {})
        })


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_datetime(iso_string):
    """Format ISO datetime string"""
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_string


if __name__ == "__main__":
    render_upload_page()
