"""
Core Configuration Management System
Centralized configuration for PV Test Automation System
ISO 17025 Compliant Configuration Management
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("DB_NAME", "pv_automation"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))
    max_overflow: int = field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20")))

    @property
    def url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"))
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    password_min_length: int = 8
    require_mfa: bool = field(default_factory=lambda: os.getenv("REQUIRE_MFA", "false").lower() == "true")
    allowed_origins: list = field(default_factory=lambda: json.loads(os.getenv("ALLOWED_ORIGINS", '["*"]')))


@dataclass
class AccreditationConfig:
    """Accreditation and compliance configuration"""
    nabl_number: str = field(default_factory=lambda: os.getenv("NABL_NUMBER", "NABL-XXXXX"))
    iso_17025_certified: bool = True
    ilac_signatory: bool = True
    bis_certified: bool = True
    lab_name: str = field(default_factory=lambda: os.getenv("LAB_NAME", "PV Testing Laboratory"))
    lab_address: str = field(default_factory=lambda: os.getenv("LAB_ADDRESS", ""))
    scope_version: str = "2024-v1"


@dataclass
class LLMConfig:
    """LLM API configuration"""
    claude_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    claude_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4-turbo-preview"
    gemini_model: str = "gemini-1.5-pro"

    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 120


@dataclass
class StorageConfig:
    """File storage configuration"""
    base_path: Path = field(default_factory=lambda: Path(os.getenv("STORAGE_PATH", "./data")))
    upload_dir: Path = field(default_factory=lambda: Path(os.getenv("UPLOAD_DIR", "./data/uploads")))
    reports_dir: Path = field(default_factory=lambda: Path(os.getenv("REPORTS_DIR", "./data/reports")))
    temp_dir: Path = field(default_factory=lambda: Path(os.getenv("TEMP_DIR", "./data/temp")))
    archive_dir: Path = field(default_factory=lambda: Path(os.getenv("ARCHIVE_DIR", "./data/archive")))

    max_upload_size_mb: int = 100
    allowed_extensions: set = field(default_factory=lambda: {
        'xlsx', 'xls', 'csv', 'json', 'pdf', 'docx', 'doc',
        'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'vsd', 'vsdx'
    })

    def __post_init__(self):
        """Create directories if they don't exist"""
        for dir_path in [self.base_path, self.upload_dir, self.reports_dir, self.temp_dir, self.archive_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class TestConfig:
    """Test execution configuration"""
    default_timeout_seconds: int = 3600
    max_parallel_tests: int = 4
    enable_real_time_monitoring: bool = True
    auto_generate_report: bool = True
    require_review_approval: bool = True


@dataclass
class ExportConfig:
    """Report export configuration"""
    default_format: str = "pdf"
    supported_formats: set = field(default_factory=lambda: {'pdf', 'docx', 'latex', 'html', 'excel', 'json', 'xml'})
    include_raw_data: bool = True
    include_charts: bool = True
    include_calibration_certs: bool = True
    watermark_enabled: bool = True


class Config:
    """Main configuration class"""

    def __init__(self, environment: Environment = None):
        self.environment = environment or Environment(os.getenv("ENVIRONMENT", "development"))

        # Initialize all config sections
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.accreditation = AccreditationConfig()
        self.llm = LLMConfig()
        self.storage = StorageConfig()
        self.test = TestConfig()
        self.export = ExportConfig()

        # Application metadata
        self.app_name = "PV Test Report Automation System"
        self.app_version = "1.0.0"
        self.app_description = "ISO 17025 Compliant PV Module Testing & Report Generation"

        # Supported IEC protocols
        self.iec_protocols = {
            'IEC 61215': 'PV Module Design Qualification and Type Approval',
            'IEC 61730': 'PV Module Safety Qualification',
            'IEC 61853': 'PV Module Performance Testing and Energy Rating',
            'IEC 62716': 'Ammonia Corrosion Testing',
            'IEC 61701': 'Salt Mist Corrosion Testing',
            'IEC 62804': 'Potential Induced Degradation (PID) Testing',
            'IEC 60904': 'Photovoltaic Devices - Measurement of Current-voltage Characteristics',
            'IEC 62759': 'Transportation Testing for PV Modules',
        }

        # Test blocks
        self.test_blocks = [
            'IV Curve Analysis',
            'Electroluminescence (EL) Detection',
            'Visual Inspection',
            'Infrared Thermography',
            'Insulation Resistance Test',
            'Wet Leakage Current Test',
            'Ground Continuity Test',
            'Hot-Spot Endurance Test',
            'Bypass Diode Test',
            'Mechanical Load Test',
            'Hail Impact Test',
        ]

        # Workflow roles
        self.workflow_roles = {
            'technician': 'Test Execution',
            'engineer': 'Technical Review',
            'reviewer': 'Report Review',
            'approver': 'Final Approval',
            'admin': 'System Administration'
        }

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check database connection
        if not self.database.password and self.environment == Environment.PRODUCTION:
            errors.append("Database password must be set in production")

        # Check security
        if self.security.secret_key == "dev-secret-key-change-in-production" and self.environment == Environment.PRODUCTION:
            errors.append("Secret key must be changed in production")

        # Check LLM keys
        if not (self.llm.claude_api_key or self.llm.openai_api_key or self.llm.gemini_api_key):
            errors.append("At least one LLM API key must be configured")

        # Check accreditation
        if not self.accreditation.nabl_number.startswith("NABL-"):
            errors.append("Invalid NABL accreditation number format")

        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (without sensitive data)"""
        return {
            'environment': self.environment.value,
            'app_name': self.app_name,
            'app_version': self.app_version,
            'iec_protocols': list(self.iec_protocols.keys()),
            'test_blocks': self.test_blocks,
            'workflow_roles': list(self.workflow_roles.keys()),
            'accreditation': {
                'nabl_number': self.accreditation.nabl_number,
                'lab_name': self.accreditation.lab_name,
                'iso_17025_certified': self.accreditation.iso_17025_certified,
            }
        }

    def __repr__(self) -> str:
        return f"<Config(environment={self.environment.value}, version={self.app_version})>"


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reload_config():
    """Reload configuration from environment"""
    global _config_instance
    _config_instance = Config()
    return _config_instance


# Export for easy import
config = get_config()
