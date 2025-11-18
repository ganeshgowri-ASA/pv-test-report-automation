"""Protocol Selection UI.

Session 50: Protocol Selection UI
"""
import streamlit as st

def main():
    st.title("PV Test Protocol Selector")
    st.header("IEC/ISO Standard Selection")
    
    standard = st.selectbox(
        "Select Test Standard",
        ["IEC 61215", "IEC 61730", "IEC 61853", "IEC 62716", "ISO 17025"]
    )
    
    st.subheader("Test Parameters")
    temp = st.number_input("Temperature (°C)", min_value=-40, max_value=85, value=25)
    irradiance = st.number_input("Irradiance (W/m²)", min_value=0, max_value=1200, value=1000)
    
    if st.button("Start Test"):
        st.success(f"Test configured for {standard}")

if __name__ == "__main__":
    main()
