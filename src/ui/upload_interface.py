"""Upload Interface for PV Test Report Automation System.

This module provides multi-file upload functionality with validation,
progress tracking, and preview capabilities.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import io

from .components.forms import create_form_field, create_file_uploader
from .components.data_tables import create_data_table


# Supported file types
SUPPORTED_EXTENSIONS = {
    "csv": "CSV Files",
    "xlsx": "Excel Files",
    "json": "JSON Files",
    "xml": "XML Files",
    "pdf": "PDF Reports",
}

MAX_FILE_SIZE_MB = 50
MAX_TOTAL_SIZE_MB = 200


def initialize_upload_state() -> None:
    """Initialize session state for upload interface."""
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "upload_queue" not in st.session_state:
        st.session_state.upload_queue = []
    if "upload_progress" not in st.session_state:
        st.session_state.upload_progress = {}
    if "validation_results" not in st.session_state:
        st.session_state.validation_results = {}
    if "preview_data" not in st.session_state:
        st.session_state.preview_data = {}
    if "batch_mode" not in st.session_state:
        st.session_state.batch_mode = False


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content.

    Args:
        file_content: File content as bytes.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(file_content).hexdigest()


def validate_file(
    filename: str,
    file_size: int,
    file_content: bytes,
) -> Tuple[bool, List[str]]:
    """Validate uploaded file.

    Args:
        filename: Name of the file.
        file_size: Size of file in bytes.
        file_content: File content as bytes.

    Returns:
        Tuple of (is_valid, error_messages).
    """
    errors = []

    # Check file extension
    file_ext = Path(filename).suffix.lower().lstrip(".")
    if file_ext not in SUPPORTED_EXTENSIONS:
        errors.append(
            f"Unsupported file type: {file_ext}. "
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    # Check file size
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        errors.append(
            f"File too large: {file_size / 1024 / 1024:.2f}MB. "
            f"Maximum size: {MAX_FILE_SIZE_MB}MB"
        )

    # Check for empty files
    if file_size == 0:
        errors.append("File is empty")

    # Additional content validation based on file type
    try:
        if file_ext == "csv":
            pd.read_csv(io.BytesIO(file_content), nrows=0)
        elif file_ext == "xlsx":
            pd.read_excel(io.BytesIO(file_content), nrows=0)
        elif file_ext == "json":
            pd.read_json(io.BytesIO(file_content))
    except Exception as e:
        errors.append(f"Invalid file format: {str(e)}")

    return len(errors) == 0, errors


def preview_file_content(file_content: bytes, filename: str) -> Optional[pd.DataFrame]:
    """Generate preview of file content.

    Args:
        file_content: File content as bytes.
        filename: Name of the file.

    Returns:
        DataFrame preview or None if preview not available.
    """
    file_ext = Path(filename).suffix.lower().lstrip(".")

    try:
        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(file_content), nrows=100)
            return df
        elif file_ext == "xlsx":
            df = pd.read_excel(io.BytesIO(file_content), nrows=100)
            return df
        elif file_ext == "json":
            df = pd.read_json(io.BytesIO(file_content))
            return df.head(100)
    except Exception:
        return None

    return None


def render_upload_area() -> None:
    """Render the main file upload area."""
    st.subheader("Upload Test Data Files")

    # Upload mode selector
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS.values())} | "
            f"Max file size: {MAX_FILE_SIZE_MB}MB | "
            f"Max total size: {MAX_TOTAL_SIZE_MB}MB"
        )
    with col2:
        batch_mode = st.toggle(
            "Batch Mode",
            value=st.session_state.batch_mode,
            help="Enable batch processing for multiple files",
        )
        st.session_state.batch_mode = batch_mode

    # File uploader with drag-and-drop support
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=list(SUPPORTED_EXTENSIONS.keys()),
        accept_multiple_files=True,
        help="Drag and drop files here or click to browse",
    )

    if uploaded_files:
        process_uploaded_files(uploaded_files)


def process_uploaded_files(uploaded_files: List) -> None:
    """Process and validate uploaded files.

    Args:
        uploaded_files: List of uploaded file objects.
    """
    st.subheader("File Processing")

    total_size = sum(f.size for f in uploaded_files)
    max_total_bytes = MAX_TOTAL_SIZE_MB * 1024 * 1024

    if total_size > max_total_bytes:
        st.error(
            f"Total file size ({total_size / 1024 / 1024:.2f}MB) exceeds "
            f"maximum allowed ({MAX_TOTAL_SIZE_MB}MB)"
        )
        return

    # Create progress container
    progress_container = st.container()

    with progress_container:
        st.write(f"Processing {len(uploaded_files)} file(s)...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        processed_files = []

        for idx, uploaded_file in enumerate(uploaded_files):
            # Update progress
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing: {uploaded_file.name}")

            # Read file content
            file_content = uploaded_file.read()
            file_hash = calculate_file_hash(file_content)

            # Validate file
            is_valid, errors = validate_file(
                uploaded_file.name,
                uploaded_file.size,
                file_content,
            )

            # Generate preview
            preview = preview_file_content(file_content, uploaded_file.name)

            # Store file info
            file_info = {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "type": uploaded_file.type,
                "hash": file_hash,
                "uploaded_at": datetime.now(),
                "is_valid": is_valid,
                "errors": errors,
                "preview": preview,
            }

            processed_files.append(file_info)

            # Store in session state
            st.session_state.validation_results[file_hash] = {
                "is_valid": is_valid,
                "errors": errors,
            }
            if preview is not None:
                st.session_state.preview_data[file_hash] = preview

        # Complete progress
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")

        # Display results
        render_upload_results(processed_files)


def render_upload_results(processed_files: List[Dict[str, Any]]) -> None:
    """Render upload results and validation status.

    Args:
        processed_files: List of processed file information.
    """
    st.divider()
    st.subheader("Upload Results")

    # Summary statistics
    total_files = len(processed_files)
    valid_files = sum(1 for f in processed_files if f["is_valid"])
    invalid_files = total_files - valid_files
    total_size = sum(f["size"] for f in processed_files)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Valid", valid_files)
    with col3:
        st.metric("Invalid", invalid_files)
    with col4:
        st.metric("Total Size", f"{total_size / 1024 / 1024:.2f} MB")

    # File list with status
    st.subheader("File Details")

    for file_info in processed_files:
        with st.expander(
            f"{'✓' if file_info['is_valid'] else '✗'} {file_info['name']}",
            expanded=not file_info["is_valid"],
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("**File Information:**")
                st.write(f"- Size: {file_info['size'] / 1024:.2f} KB")
                st.write(f"- Type: {file_info['type']}")
                st.write(f"- Hash: {file_info['hash'][:16]}...")
                st.write(
                    f"- Uploaded: {file_info['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                )

            with col2:
                if file_info["is_valid"]:
                    st.success("Validation Passed")
                else:
                    st.error("Validation Failed")

            # Show validation errors
            if file_info["errors"]:
                st.write("**Validation Errors:**")
                for error in file_info["errors"]:
                    st.error(error)

            # Show preview
            if file_info["preview"] is not None:
                st.write("**Preview (first 100 rows):**")
                st.dataframe(file_info["preview"], use_container_width=True)

                # Show column info
                st.write("**Column Information:**")
                col_info = pd.DataFrame({
                    "Column": file_info["preview"].columns,
                    "Type": file_info["preview"].dtypes.astype(str),
                    "Non-Null": file_info["preview"].count().values,
                    "Null": file_info["preview"].isnull().sum().values,
                })
                st.dataframe(col_info, hide_index=True, use_container_width=True)


def render_batch_processing() -> None:
    """Render batch processing controls."""
    if not st.session_state.batch_mode:
        return

    st.divider()
    st.subheader("Batch Processing")

    col1, col2, col3 = st.columns(3)

    with col1:
        processing_mode = st.selectbox(
            "Processing Mode",
            options=["Sequential", "Parallel"],
            help="Choose how to process multiple files",
        )

    with col2:
        priority = st.selectbox(
            "Priority",
            options=["Normal", "High", "Low"],
            help="Set processing priority",
        )

    with col3:
        notify_on_complete = st.checkbox(
            "Notify on Completion",
            value=True,
            help="Send notification when batch processing completes",
        )

    # Batch actions
    st.write("**Batch Actions:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Process All", use_container_width=True):
            st.info("Processing all valid files...")

    with col2:
        if st.button("Clear Queue", use_container_width=True):
            st.session_state.upload_queue = []
            st.success("Queue cleared")

    with col3:
        if st.button("Validate All", use_container_width=True):
            st.info("Re-validating all files...")

    with col4:
        if st.button("Download Log", use_container_width=True):
            st.info("Generating download log...")


def render_upload_history() -> None:
    """Render upload history."""
    st.divider()
    st.subheader("Upload History")

    # TODO: Replace with actual upload history from database
    history_data = pd.DataFrame({
        "timestamp": [
            datetime.now() - pd.Timedelta(hours=i) for i in range(10)
        ],
        "filename": [f"test_data_{i}.csv" for i in range(10)],
        "size": [1024 * (i + 1) for i in range(10)],
        "status": ["Success", "Success", "Failed", "Success"] * 2 + ["Success", "Success"],
        "user": ["system"] * 10,
    })

    history_data["timestamp"] = history_data["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    history_data["size"] = history_data["size"].apply(lambda x: f"{x / 1024:.2f} KB")

    # Filter controls
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_status = st.multiselect(
            "Filter by Status",
            options=["Success", "Failed"],
            default=["Success", "Failed"],
        )
    with col2:
        limit = st.number_input("Show last", min_value=5, max_value=100, value=10)

    # Display history table
    filtered_history = history_data[history_data["status"].isin(filter_status)].head(limit)

    create_data_table(
        filtered_history,
        page_size=10,
        column_config={
            "timestamp": st.column_config.TextColumn("Timestamp"),
            "filename": st.column_config.TextColumn("Filename"),
            "size": st.column_config.TextColumn("Size"),
            "status": st.column_config.TextColumn("Status"),
            "user": st.column_config.TextColumn("User"),
        },
    )


def render_upload_settings() -> None:
    """Render upload settings panel."""
    with st.sidebar:
        st.subheader("Upload Settings")

        auto_validate = st.checkbox(
            "Auto-validate on upload",
            value=True,
            help="Automatically validate files after upload",
        )

        auto_preview = st.checkbox(
            "Auto-generate preview",
            value=True,
            help="Automatically generate file preview",
        )

        preserve_originals = st.checkbox(
            "Preserve original files",
            value=True,
            help="Keep original uploaded files",
        )

        st.divider()

        st.write("**Validation Rules:**")
        check_duplicates = st.checkbox("Check for duplicates", value=True)
        validate_schema = st.checkbox("Validate schema", value=True)
        check_data_quality = st.checkbox("Check data quality", value=False)


def render_upload_interface() -> None:
    """Render the upload interface page."""
    # Initialize state
    initialize_upload_state()

    # Page header
    st.title("Upload Test Data")
    st.write("Upload and validate test data files for processing")

    # Settings panel
    render_upload_settings()

    # Main upload area
    render_upload_area()

    # Batch processing controls
    render_batch_processing()

    # Upload history
    render_upload_history()


if __name__ == "__main__":
    render_upload_interface()
