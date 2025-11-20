"""Report Review UI.

Session 53: Report Review UI
"""
import streamlit as st

def main():
    st.title("Report Review & Approval")
    
    report_id = st.selectbox("Select Report", ["RPT-2024-001", "RPT-2024-002"])
    
    st.subheader("Review Actions")
    comment = st.text_area("Review Comments")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve"):
            st.success("Report approved")
    with col2:
        if st.button("❌ Reject"):
            st.error("Report rejected")

if __name__ == "__main__":
    main()
