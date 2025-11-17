"""
Configuration management for PV test report automation system.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
import json
import os


@dataclass
class LaboratoryConfig:
    """Laboratory information configuration."""
    name: str = "PV Testing Laboratory"
    accreditation: str = "ISO/IEC 17025:2017"
    accreditation_body: str = "NABL"
    accreditation_number: str = ""
    address: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    website: str = ""


@dataclass
class EquipmentConfig:
    """Equipment configuration."""
    solar_simulator: Dict[str, Any] = field(default_factory=dict)
    iv_tracer: Dict[str, Any] = field(default_factory=dict)
    temperature_chamber: Dict[str, Any] = field(default_factory=dict)
    insulation_tester: Dict[str, Any] = field(default_factory=dict)
    thermal_camera: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestConfig:
    """Test execution configuration."""
    # Standard Test Conditions
    stc_irradiance: float = 1000.0  # W/m²
    stc_temperature: float = 25.0    # °C
    stc_spectrum: str = "AM1.5G"

    # NOCT Conditions
    noct_irradiance: float = 800.0   # W/m²
    noct_ambient_temp: float = 20.0  # °C
    noct_wind_speed: float = 1.0     # m/s

    # Degradation Limits
    max_degradation_general: float = 5.0  # %
    max_degradation_initial: float = 2.0  # %

    # Test durations (for simulations/estimates)
    thermal_cycles: int = 200
    humidity_freeze_cycles: int = 10
    damp_heat_hours: int = 1000
    dynamic_load_cycles: int = 1000

    # Environmental tolerances
    temperature_tolerance: float = 2.0  # °C
    humidity_tolerance: float = 5.0     # % RH
    irradiance_tolerance: float = 50.0  # W/m²


@dataclass
class ReportConfig:
    """Report generation configuration."""
    output_directory: Path = Path("./reports")
    template_directory: Path = Path("./templates")
    default_format: str = "pdf"
    include_photos: bool = True
    include_raw_data: bool = False
    logo_path: Optional[Path] = None


@dataclass
class DatabaseConfig:
    """Database configuration for storing test results."""
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "pv_test_reports"
    username: str = ""
    password: str = ""
    sqlite_path: Path = Path("./data/test_reports.db")


@dataclass
class SystemConfig:
    """Main system configuration."""
    laboratory: LaboratoryConfig = field(default_factory=LaboratoryConfig)
    equipment: EquipmentConfig = field(default_factory=EquipmentConfig)
    test: TestConfig = field(default_factory=TestConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # System settings
    debug_mode: bool = False
    log_level: str = "INFO"
    log_directory: Path = Path("./logs")
    data_directory: Path = Path("./data")

    @classmethod
    def from_file(cls, config_file: Path) -> 'SystemConfig':
        """
        Load configuration from JSON file.

        Args:
            config_file: Path to configuration file

        Returns:
            SystemConfig instance
        """
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_file, 'r') as f:
            config_data = json.load(f)

        return cls.from_dict(config_data)

    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'SystemConfig':
        """
        Create configuration from dictionary.

        Args:
            config_data: Configuration dictionary

        Returns:
            SystemConfig instance
        """
        config = cls()

        # Laboratory config
        if "laboratory" in config_data:
            lab_data = config_data["laboratory"]
            config.laboratory = LaboratoryConfig(**lab_data)

        # Equipment config
        if "equipment" in config_data:
            config.equipment = EquipmentConfig(**config_data["equipment"])

        # Test config
        if "test" in config_data:
            config.test = TestConfig(**config_data["test"])

        # Report config
        if "report" in config_data:
            report_data = config_data["report"]
            if "output_directory" in report_data:
                report_data["output_directory"] = Path(report_data["output_directory"])
            if "template_directory" in report_data:
                report_data["template_directory"] = Path(report_data["template_directory"])
            if "logo_path" in report_data and report_data["logo_path"]:
                report_data["logo_path"] = Path(report_data["logo_path"])
            config.report = ReportConfig(**report_data)

        # Database config
        if "database" in config_data:
            db_data = config_data["database"]
            if "sqlite_path" in db_data:
                db_data["sqlite_path"] = Path(db_data["sqlite_path"])
            config.database = DatabaseConfig(**db_data)

        # System settings
        if "debug_mode" in config_data:
            config.debug_mode = config_data["debug_mode"]
        if "log_level" in config_data:
            config.log_level = config_data["log_level"]
        if "log_directory" in config_data:
            config.log_directory = Path(config_data["log_directory"])
        if "data_directory" in config_data:
            config.data_directory = Path(config_data["data_directory"])

        return config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "laboratory": {
                "name": self.laboratory.name,
                "accreditation": self.laboratory.accreditation,
                "accreditation_body": self.laboratory.accreditation_body,
                "accreditation_number": self.laboratory.accreditation_number,
                "address": self.laboratory.address,
                "contact_email": self.laboratory.contact_email,
                "contact_phone": self.laboratory.contact_phone,
                "website": self.laboratory.website,
            },
            "equipment": {
                "solar_simulator": self.equipment.solar_simulator,
                "iv_tracer": self.equipment.iv_tracer,
                "temperature_chamber": self.equipment.temperature_chamber,
                "insulation_tester": self.equipment.insulation_tester,
                "thermal_camera": self.equipment.thermal_camera,
            },
            "test": {
                "stc_irradiance": self.test.stc_irradiance,
                "stc_temperature": self.test.stc_temperature,
                "stc_spectrum": self.test.stc_spectrum,
                "noct_irradiance": self.test.noct_irradiance,
                "noct_ambient_temp": self.test.noct_ambient_temp,
                "noct_wind_speed": self.test.noct_wind_speed,
                "max_degradation_general": self.test.max_degradation_general,
                "max_degradation_initial": self.test.max_degradation_initial,
            },
            "report": {
                "output_directory": str(self.report.output_directory),
                "template_directory": str(self.report.template_directory),
                "default_format": self.report.default_format,
                "include_photos": self.report.include_photos,
                "include_raw_data": self.report.include_raw_data,
                "logo_path": str(self.report.logo_path) if self.report.logo_path else None,
            },
            "database": {
                "type": self.database.type,
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "sqlite_path": str(self.database.sqlite_path),
            },
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "log_directory": str(self.log_directory),
            "data_directory": str(self.data_directory),
        }

    def save(self, config_file: Path) -> None:
        """
        Save configuration to file.

        Args:
            config_file: Path to save configuration
        """
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.report.output_directory,
            self.report.template_directory,
            self.log_directory,
            self.data_directory,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Default configuration instance
_default_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """
    Get the global configuration instance.

    Returns:
        SystemConfig instance
    """
    global _default_config

    if _default_config is None:
        # Try to load from environment variable
        config_file = os.environ.get("PV_TEST_CONFIG")

        if config_file and Path(config_file).exists():
            _default_config = SystemConfig.from_file(Path(config_file))
        else:
            # Use default configuration
            _default_config = SystemConfig()

    return _default_config


def set_config(config: SystemConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: SystemConfig instance
    """
    global _default_config
    _default_config = config


def load_config(config_file: Path) -> SystemConfig:
    """
    Load configuration from file and set as global config.

    Args:
        config_file: Path to configuration file

    Returns:
        SystemConfig instance
    """
    config = SystemConfig.from_file(config_file)
    set_config(config)
    return config
