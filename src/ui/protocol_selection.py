"""
Protocol Selection UI - Streamlit Component.

Interactive protocol selection interface for PV test planning:
- IEC 61215, 61730, 61853, 61701 protocols
- Test configuration wizard
- Parameter customization
- Sample information input
"""

import streamlit as st
from typing import Dict, Any


def render_protocol_selection() -> Dict[str, Any]:
    """
    Render protocol selection UI.

    Returns:
        Selected protocol configuration
    """
    st.title("🔬 PV Test Protocol Selection")

    st.markdown("""
    Select the test protocol and configure parameters for your PV module testing.
    """)

    # Protocol selection
    protocol = st.selectbox(
        "Select Test Protocol",
        options=[
            "IEC 61215 - Module Stress Testing",
            "IEC 61730 - Safety Qualification",
            "IEC 61853 - Performance Testing",
            "IEC 61701 - Salt Mist Corrosion",
        ],
    )

    st.divider()

    config: Dict[str, Any] = {"protocol": protocol}

    # Protocol-specific configuration
    if "61215" in protocol:
        st.subheader("IEC 61215 Configuration")

        col1, col2 = st.columns(2)
        with col1:
            config["damp_heat_cycles"] = st.number_input(
                "Damp Heat Cycles", min_value=1, max_value=1000, value=200
            )
            config["thermal_cycling_cycles"] = st.number_input(
                "Thermal Cycling Cycles", min_value=1, max_value=1000, value=200
            )

        with col2:
            config["humidity_freeze_cycles"] = st.number_input(
                "Humidity Freeze Cycles", min_value=1, max_value=50, value=10
            )
            config["uv_irradiance"] = st.number_input(
                "UV Irradiance (kWh/m²)", min_value=1.0, max_value=50.0, value=15.0
            )

    elif "61730" in protocol:
        st.subheader("IEC 61730 Configuration")

        col1, col2 = st.columns(2)
        with col1:
            config["safety_class"] = st.selectbox("Safety Class", ["I", "II"])
        with col2:
            config["application_class"] = st.selectbox(
                "Application Class", ["A", "B", "C", "T"]
            )

    elif "61853" in protocol:
        st.subheader("IEC 61853 Configuration")

        config["irradiance_levels"] = st.multiselect(
            "Irradiance Levels (W/m²)",
            options=[100, 200, 400, 600, 800, 1000, 1100],
            default=[100, 400, 800, 1000],
        )

        config["temperature_levels"] = st.multiselect(
            "Temperature Levels (°C)",
            options=[15, 25, 50, 75],
            default=[15, 25, 50],
        )

    elif "61701" in protocol:
        st.subheader("IEC 61701 Configuration")

        config["severity_level"] = st.select_slider(
            "Severity Level", options=["1", "2", "3", "4", "5", "6"], value="3"
        )

        st.info(f"Severity Level {config['severity_level']}: Suitable for coastal environments")

    # Sample information
    st.divider()
    st.subheader("Sample Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        config["sample_id"] = st.text_input("Sample ID", value="PV-2024-001")
        config["manufacturer"] = st.text_input("Manufacturer", value="Example Solar Co.")

    with col2:
        config["module_type"] = st.text_input("Module Type", value="ESC-400-72M")
        config["serial_number"] = st.text_input("Serial Number", value="SN123456789")

    with col3:
        config["rated_power"] = st.number_input(
            "Rated Power (W)", min_value=1, max_value=1000, value=400
        )
        config["cell_technology"] = st.selectbox(
            "Cell Technology", ["Monocrystalline", "Polycrystalline", "Thin-film"]
        )

    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("▶️ Start Test", type="primary", use_container_width=True):
            st.success("Test started!")
            return config

    with col2:
        if st.button("💾 Save Config", use_container_width=True):
            st.info("Configuration saved!")

    return config


if __name__ == "__main__":
    render_protocol_selection()
