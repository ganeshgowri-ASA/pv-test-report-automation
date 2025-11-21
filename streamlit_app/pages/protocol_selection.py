"""
Protocol Selection - Choose IEC test standards and protocols
"""

import streamlit as st

# IEC Protocol definitions
PROTOCOLS = {
    "IEC 61215": {
        "title": "IEC 61215 - Terrestrial PV Modules - Design Qualification",
        "description": "Crystalline silicon terrestrial photovoltaic (PV) modules design qualification and type approval",
        "tests": [
            "Visual Inspection",
            "Maximum Power Determination",
            "Insulation Test",
            "Temperature Coefficient Measurement",
            "NOCT Measurement",
            "Performance at Low Irradiance",
            "Outdoor Exposure Test",
            "Hot-Spot Endurance Test",
            "UV Preconditioning Test",
            "Thermal Cycling Test",
            "Humidity-Freeze Test",
            "Damp Heat Test",
            "Robustness of Terminations",
            "Wet Leakage Current Test",
            "Mechanical Load Test",
            "Hail Test",
            "Bypass Diode Thermal Test"
        ],
        "applicable_to": "Crystalline Silicon Modules"
    },
    "IEC 61730": {
        "title": "IEC 61730 - PV Module Safety Qualification",
        "description": "Photovoltaic (PV) module safety qualification",
        "tests": [
            "Construction Requirements",
            "Accessible Parts and Connections",
            "Electrical Shock and Energy Hazards",
            "Fire Hazard Testing",
            "Mechanical Stress Testing",
            "Environmental Stress Testing",
            "Module Marking and Instructions"
        ],
        "applicable_to": "All PV Module Types"
    },
    "IEC 61853": {
        "title": "IEC 61853 - PV Module Performance Testing",
        "description": "Photovoltaic (PV) module performance testing and energy rating",
        "tests": [
            "Irradiance and Temperature Performance",
            "Spectral Response",
            "Angle of Incidence",
            "Operating Temperature",
            "Energy Rating"
        ],
        "applicable_to": "All PV Module Types"
    },
    "IEC 62716": {
        "title": "IEC 62716 - Ammonia Corrosion Testing",
        "description": "PV modules - Ammonia (NH3) corrosion testing",
        "tests": [
            "Ammonia Exposure Test",
            "Performance Measurement",
            "Visual Inspection Post-Test",
            "Wet Insulation Resistance"
        ],
        "applicable_to": "Modules for Agricultural/Industrial Environments"
    },
    "IEC 61701": {
        "title": "IEC 61701 - Salt Mist Corrosion Testing",
        "description": "PV modules - Salt mist corrosion testing",
        "tests": [
            "Salt Mist Exposure",
            "Performance Degradation Measurement",
            "Visual Inspection",
            "Insulation Test"
        ],
        "applicable_to": "Modules for Coastal/Marine Environments"
    },
    "IEC 62804": {
        "title": "IEC 62804 - PID Testing",
        "description": "Potential-Induced Degradation (PID) testing of crystalline silicon PV modules",
        "tests": [
            "PID Test at 85°C/85% RH",
            "Performance Measurement",
            "Recovery Test",
            "Long-term PID Testing"
        ],
        "applicable_to": "Crystalline Silicon Modules"
    },
    "IEC 60904": {
        "title": "IEC 60904 - PV Device Measurement",
        "description": "Photovoltaic devices - Measurement of current-voltage characteristics",
        "tests": [
            "I-V Curve Measurement",
            "Spectral Response Measurement",
            "Temperature Coefficient Measurement",
            "Linearity Testing"
        ],
        "applicable_to": "Individual PV Devices and Modules"
    },
    "IEC 62759": {
        "title": "IEC 62759 - Transportation Testing",
        "description": "Transportation testing for photovoltaic (PV) modules",
        "tests": [
            "Vibration Test",
            "Mechanical Shock Test",
            "Drop Test",
            "Package Integrity"
        ],
        "applicable_to": "Packaged PV Modules"
    }
}

def render():
    """Render the protocol selection page"""
    st.title("📋 Protocol Selection")
    st.markdown("### Select IEC Test Standards and Configure Test Parameters")

    st.info("""
    **Available Standards:** 8 IEC protocols covering design qualification, safety, performance,
    environmental stress, and specialized testing for PV modules.
    """)

    # Protocol selection
    st.subheader("🎯 Select Primary Test Protocol")

    selected_protocol = st.selectbox(
        "Choose IEC Standard",
        options=list(PROTOCOLS.keys()),
        format_func=lambda x: f"{x} - {PROTOCOLS[x]['title'].split(' - ')[1]}"
    )

    if selected_protocol:
        protocol_info = PROTOCOLS[selected_protocol]

        # Display protocol details
        st.markdown("---")
        st.subheader(f"📖 {protocol_info['title']}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Description:** {protocol_info['description']}")
            st.markdown(f"**Applicable To:** {protocol_info['applicable_to']}")

        with col2:
            st.metric("Total Tests", len(protocol_info['tests']))

        # Test checklist
        st.markdown("---")
        st.subheader("✅ Test Sequence Selection")

        st.markdown("Select the specific tests to perform:")

        selected_tests = []
        num_cols = 2
        cols = st.columns(num_cols)

        for idx, test in enumerate(protocol_info['tests']):
            with cols[idx % num_cols]:
                if st.checkbox(test, value=True, key=f"test_{idx}"):
                    selected_tests.append(test)

        st.info(f"**Selected:** {len(selected_tests)} out of {len(protocol_info['tests'])} tests")

        # Additional protocols
        st.markdown("---")
        st.subheader("➕ Additional Protocols (Optional)")

        additional_protocols = st.multiselect(
            "Select additional standards to combine:",
            options=[p for p in PROTOCOLS.keys() if p != selected_protocol],
            format_func=lambda x: f"{x} - {PROTOCOLS[x]['title'].split(' - ')[1]}"
        )

        if additional_protocols:
            st.success(f"Combined testing with: {', '.join(additional_protocols)}")

        # Sample information
        st.markdown("---")
        st.subheader("📦 Sample Information")

        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            sample_id = st.text_input("Sample ID", value="PV-2024-001")

        with col_s2:
            manufacturer = st.text_input("Manufacturer", value="SolarTech Inc.")

        with col_s3:
            module_type = st.selectbox(
                "Module Type",
                ["Mono-crystalline", "Poly-crystalline", "Thin Film", "Bifacial", "PERC", "HJT"]
            )

        col_s4, col_s5, col_s6 = st.columns(3)

        with col_s4:
            rated_power = st.number_input("Rated Power (W)", min_value=1, value=400)

        with col_s5:
            num_cells = st.number_input("Number of Cells", min_value=1, value=72)

        with col_s6:
            sample_qty = st.number_input("Sample Quantity", min_value=1, value=3)

        # Test configuration
        st.markdown("---")
        st.subheader("⚙️ Test Configuration")

        col_c1, col_c2 = st.columns(2)

        with col_c1:
            test_lab = st.text_input("Test Laboratory", value="PV Testing Center")
            test_engineer = st.text_input("Test Engineer", value=st.session_state.get('username', 'Unknown'))

        with col_c2:
            start_date = st.date_input("Planned Start Date")
            priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])

        # Environmental conditions
        with st.expander("🌡️ Environmental Conditions", expanded=False):
            col_e1, col_e2, col_e3 = st.columns(3)

            with col_e1:
                temperature = st.number_input("Temperature (°C)", value=25.0)

            with col_e2:
                humidity = st.number_input("Humidity (%)", value=50.0)

            with col_e3:
                pressure = st.number_input("Pressure (kPa)", value=101.325)

        # LLM Configuration
        st.markdown("---")
        st.subheader("🤖 LLM Integration Settings")

        enable_llm = st.checkbox("Enable LLM-Powered Analysis", value=True)

        if enable_llm:
            col_l1, col_l2 = st.columns(2)

            with col_l1:
                llm_provider = st.selectbox(
                    "LLM Provider",
                    ["Claude (Anthropic)", "GPT-4 (OpenAI)", "Gemini (Google)"]
                )

            with col_l2:
                analysis_depth = st.select_slider(
                    "Analysis Depth",
                    options=["Basic", "Standard", "Comprehensive", "Expert"]
                )

            st.info(f"""
            **LLM Configuration:** {llm_provider} with {analysis_depth} analysis
            - Automated anomaly detection
            - Intelligent test result interpretation
            - Standards compliance verification
            - Report narrative generation
            """)

        # Action buttons
        st.markdown("---")

        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

        with col_btn1:
            if st.button("💾 Save Configuration", use_container_width=True):
                st.success("✅ Test configuration saved!")
                st.session_state.test_config = {
                    'protocol': selected_protocol,
                    'tests': selected_tests,
                    'sample_id': sample_id,
                    'manufacturer': manufacturer
                }

        with col_btn2:
            if st.button("📋 Load Template", use_container_width=True):
                st.info("Template loading feature")

        with col_btn3:
            if st.button("📤 Proceed to Data Upload", use_container_width=True):
                st.info("Navigate to Data Upload page to continue")

        with col_btn4:
            if st.button("🔄 Reset", use_container_width=True):
                st.rerun()
