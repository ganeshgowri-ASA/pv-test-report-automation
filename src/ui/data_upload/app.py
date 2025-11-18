"""Data Upload UI.

Session 51: Data Upload UI
"""
import streamlit as st

def main():
    st.title("Test Data Upload")
    
    uploaded_file = st.file_uploader(
        "Upload test data file",
        type=["csv", "xlsx", "json"],
        help="Drag and drop or click to browse"
    )
    
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        if st.button("Process File"):
            st.info("Processing test data...")

if __name__ == "__main__":
    main()
