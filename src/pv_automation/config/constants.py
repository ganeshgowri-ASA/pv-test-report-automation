"""Constants and enumerations for PV automation system"""

from enum import Enum
from typing import Dict, Any


class PVStandard(str, Enum):
    """Supported PV testing standards"""

    IEC_61215 = "IEC 61215"  # Crystalline silicon terrestrial photovoltaic modules
    IEC_61730 = "IEC 61730"  # Photovoltaic module safety qualification
    IEC_61853 = "IEC 61853"  # Performance testing and energy rating
    IEC_62716 = "IEC 62716"  # Ammonia corrosion testing
    IEC_61701 = "IEC 61701"  # Salt mist corrosion testing
    IEC_62804 = "IEC 62804"  # Test methods for detection of PID
    IEC_60904 = "IEC 60904"  # Photovoltaic devices
    IEC_62759 = "IEC 62759"  # Transportation testing
    ISO_17025 = "ISO 17025"  # General requirements for testing laboratories
    ISO_9001 = "ISO 9001"  # Quality management systems
    NABL = "NABL"  # National Accreditation Board for Testing
    ILAC = "ILAC"  # International Laboratory Accreditation Cooperation
    BIS = "BIS"  # Bureau of Indian Standards


class ImageFormat(str, Enum):
    """Supported image formats for analysis"""

    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    TIF = "tif"
    BMP = "bmp"


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"


class DefectType(str, Enum):
    """Common PV module defect types"""

    CRACK = "crack"
    HOTSPOT = "hotspot"
    DELAMINATION = "delamination"
    DISCOLORATION = "discoloration"
    CELL_BREAKAGE = "cell_breakage"
    BYPASS_DIODE_FAILURE = "bypass_diode_failure"
    JUNCTION_BOX_DEFECT = "junction_box_defect"
    ENCAPSULANT_DEGRADATION = "encapsulant_degradation"
    BACKSHEET_DAMAGE = "backsheet_damage"
    GRID_LINE_CORROSION = "grid_line_corrosion"
    PID = "potential_induced_degradation"
    SNAIL_TRAILS = "snail_trails"


class TestCategory(str, Enum):
    """PV test categories"""

    VISUAL_INSPECTION = "visual_inspection"
    ELECTRICAL_PERFORMANCE = "electrical_performance"
    MECHANICAL_STRESS = "mechanical_stress"
    ENVIRONMENTAL_TESTING = "environmental_testing"
    SAFETY_TESTING = "safety_testing"
    DURABILITY_TESTING = "durability_testing"
    EL_IMAGING = "electroluminescence_imaging"
    THERMAL_IMAGING = "thermal_imaging"


# Supported PV standards with descriptions
SUPPORTED_STANDARDS: Dict[str, str] = {
    PVStandard.IEC_61215: "Design qualification and type approval for crystalline silicon PV modules",
    PVStandard.IEC_61730: "Photovoltaic module safety qualification",
    PVStandard.IEC_61853: "Photovoltaic module performance testing and energy rating",
    PVStandard.IEC_62716: "Photovoltaic modules - Ammonia corrosion testing",
    PVStandard.IEC_61701: "Photovoltaic modules - Salt mist corrosion testing",
    PVStandard.IEC_62804: "Test methods for the detection of potential-induced degradation",
    PVStandard.IEC_60904: "Photovoltaic devices - Measurement of current-voltage characteristics",
    PVStandard.IEC_62759: "Transportation testing of photovoltaic modules",
    PVStandard.ISO_17025: "General requirements for the competence of testing laboratories",
    PVStandard.ISO_9001: "Quality management systems - Requirements",
    PVStandard.NABL: "National Accreditation Board for Testing and Calibration Laboratories",
    PVStandard.ILAC: "International Laboratory Accreditation Cooperation",
    PVStandard.BIS: "Bureau of Indian Standards - Solar PV requirements",
}

# Default safety settings for Gemini API
DEFAULT_SAFETY_SETTINGS: Dict[str, Any] = {
    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
}

# Default generation config
DEFAULT_GENERATION_CONFIG: Dict[str, Any] = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# Image analysis prompts
DEFECT_ANALYSIS_PROMPT_TEMPLATE = """
Analyze this {image_type} image of a photovoltaic (PV) module and identify any defects or anomalies.

Focus on detecting:
- Cracks in cells
- Hotspots or thermal anomalies
- Delamination
- Discoloration
- Cell breakage
- Grid line defects
- Bypass diode failures
- Encapsulant degradation

Provide a structured analysis including:
1. Defect identification (type, location, severity)
2. Potential impact on module performance
3. Compliance with relevant standards ({standard})
4. Recommended actions

Be specific and technical in your analysis.
"""

COMPLIANCE_CHECK_PROMPT_TEMPLATE = """
Review the following PV test report data against {standard} standard requirements:

{report_data}

Provide:
1. Compliance status (Pass/Fail/Conditional)
2. Specific requirement violations (if any)
3. Missing test data or documentation
4. Recommendations for achieving full compliance
"""

PREDICTIVE_ANALYSIS_PROMPT_TEMPLATE = """
Based on the following PV module test data and historical patterns,
provide a predictive failure analysis:

{test_data}

Include:
1. Probability of failure within warranty period
2. Key risk factors identified
3. Degradation trends
4. Recommended preventive measures
5. Expected lifespan estimation
"""

# Error messages
ERROR_MESSAGES = {
    "invalid_api_key": "Invalid Gemini API key. Please check your configuration.",
    "image_too_large": "Image file size exceeds maximum allowed size of {max_size}MB.",
    "unsupported_format": "Unsupported image format. Allowed formats: {formats}",
    "model_not_available": "The requested model '{model}' is not available.",
    "rate_limit_exceeded": "API rate limit exceeded. Please try again later.",
    "safety_filter_triggered": "Content was blocked by safety filters.",
    "network_error": "Network error occurred. Please check your connection.",
}
