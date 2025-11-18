"""Admin Panel.

Session 54: Admin Panel
"""
import streamlit as st

def main():
    st.title("Admin Panel")
    
    tab1, tab2, tab3 = st.tabs(["Users", "Equipment", "System Settings"])
    
    with tab1:
        st.subheader("User Management")
        st.button("Add New User")
    
    with tab2:
        st.subheader("Equipment Configuration")
        st.button("Add Equipment")
    
    with tab3:
        st.subheader("System Settings")
        st.checkbox("Enable Audit Logging", value=True)

if __name__ == "__main__":
    main()
