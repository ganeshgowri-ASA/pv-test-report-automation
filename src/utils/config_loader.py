"""
Configuration Loader for PV Test Report Automation

This module provides utilities to load and validate configuration files including:
- Testing standards (IEC/ISO/NABL/BIS)
- LLM API configurations
- Report templates
- Environment variables

Author: PV Test Report Automation Team
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


@dataclass
class StandardConfig:
    """Data class for testing standard configuration"""
    code: str
    full_name: str
    version: str
    applicable_to: List[str]
    scope: str
    data: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None
    loaded_at: Optional[datetime] = None


@dataclass
class LLMProviderConfig:
    """Data class for LLM provider configuration"""
    name: str
    enabled: bool
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    models: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """Main configuration loader class"""

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration loader

        Args:
            config_dir: Path to configuration directory. If None, uses default location.
        """
        if config_dir is None:
            # Default to config directory relative to this file
            self.base_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.base_dir = Path(config_dir)

        self.standards_dir = self.base_dir / "standards"
        self.templates_dir = self.base_dir / "templates"
        self.llm_config_file = self.base_dir / "llm_config.yaml"

        # Cache for loaded configurations
        self._standards_cache: Dict[str, StandardConfig] = {}
        self._llm_config_cache: Optional[Dict[str, Any]] = None
        self._templates_cache: Dict[str, Any] = {}

        logger.info(f"ConfigLoader initialized with base directory: {self.base_dir}")

    def _validate_path(self, path: Path, path_type: str = "file") -> bool:
        """
        Validate that a path exists and is of the correct type

        Args:
            path: Path to validate
            path_type: Type of path ("file" or "directory")

        Returns:
            True if valid

        Raises:
            ConfigurationError: If path is invalid
        """
        if not path.exists():
            raise ConfigurationError(f"{path_type.capitalize()} not found: {path}")

        if path_type == "file" and not path.is_file():
            raise ConfigurationError(f"Path is not a file: {path}")
        elif path_type == "directory" and not path.is_dir():
            raise ConfigurationError(f"Path is not a directory: {path}")

        return True

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a YAML file

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            self._validate_path(file_path, "file")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ConfigurationError(f"Empty YAML file: {file_path}")

            logger.debug(f"Successfully loaded YAML file: {file_path}")
            return data

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML file {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading file {file_path}: {e}")

    def load_standard(self, standard_code: str, use_cache: bool = True) -> StandardConfig:
        """
        Load a testing standard configuration

        Args:
            standard_code: Standard code (e.g., "iec_61215", "iso_17025")
            use_cache: Whether to use cached data if available

        Returns:
            StandardConfig object

        Raises:
            ConfigurationError: If standard cannot be loaded
        """
        # Check cache first
        if use_cache and standard_code in self._standards_cache:
            logger.debug(f"Using cached standard: {standard_code}")
            return self._standards_cache[standard_code]

        # Construct file path
        file_path = self.standards_dir / f"{standard_code}.yaml"

        # Load YAML data
        data = self._load_yaml_file(file_path)

        # Extract standard metadata
        standard_info = data.get('standard', {})

        if not standard_info:
            raise ConfigurationError(f"Missing 'standard' section in {file_path}")

        # Create StandardConfig object
        config = StandardConfig(
            code=standard_info.get('code', standard_code.upper()),
            full_name=standard_info.get('full_name', ''),
            version=standard_info.get('version', ''),
            applicable_to=standard_info.get('applicable_to', []),
            scope=standard_info.get('scope', ''),
            data=data,
            file_path=file_path,
            loaded_at=datetime.now()
        )

        # Validate required fields
        self._validate_standard_config(config)

        # Cache the config
        self._standards_cache[standard_code] = config

        logger.info(f"Loaded standard: {config.code} ({config.full_name})")
        return config

    def _validate_standard_config(self, config: StandardConfig) -> bool:
        """
        Validate a standard configuration

        Args:
            config: StandardConfig to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not config.code:
            raise ValidationError("Standard code is required")

        if not config.full_name:
            raise ValidationError(f"Standard {config.code}: full_name is required")

        if not config.version:
            logger.warning(f"Standard {config.code}: version is empty")

        if not config.scope:
            logger.warning(f"Standard {config.code}: scope is empty")

        return True

    def load_all_standards(self) -> Dict[str, StandardConfig]:
        """
        Load all available testing standards

        Returns:
            Dictionary mapping standard codes to StandardConfig objects
        """
        standards = {}

        if not self.standards_dir.exists():
            logger.warning(f"Standards directory not found: {self.standards_dir}")
            return standards

        # Find all YAML files in standards directory
        yaml_files = list(self.standards_dir.glob("*.yaml")) + \
                     list(self.standards_dir.glob("*.yml"))

        for yaml_file in yaml_files:
            standard_code = yaml_file.stem  # filename without extension

            try:
                config = self.load_standard(standard_code)
                standards[standard_code] = config
            except Exception as e:
                logger.error(f"Failed to load standard {standard_code}: {e}")
                continue

        logger.info(f"Loaded {len(standards)} standards")
        return standards

    def get_standard_by_code(self, code: str) -> Optional[StandardConfig]:
        """
        Get a standard by its code (e.g., "IEC 61215")

        Args:
            code: Standard code to search for

        Returns:
            StandardConfig if found, None otherwise
        """
        # Normalize the code
        normalized_code = code.replace(" ", "_").replace("/", "_").lower()

        # Try direct lookup first
        try:
            return self.load_standard(normalized_code)
        except ConfigurationError:
            pass

        # Search through all standards
        all_standards = self.load_all_standards()

        for std_code, config in all_standards.items():
            if config.code.lower() == code.lower():
                return config

        return None

    def load_llm_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load LLM configuration

        Args:
            use_cache: Whether to use cached data

        Returns:
            LLM configuration dictionary
        """
        # Check cache
        if use_cache and self._llm_config_cache is not None:
            logger.debug("Using cached LLM config")
            return self._llm_config_cache

        # Load YAML
        config = self._load_yaml_file(self.llm_config_file)

        # Process environment variables
        config = self._process_llm_env_vars(config)

        # Validate LLM config
        self._validate_llm_config(config)

        # Cache the config
        self._llm_config_cache = config

        logger.info("Loaded LLM configuration")
        return config

    def _process_llm_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process environment variables in LLM configuration

        Args:
            config: LLM configuration dictionary

        Returns:
            Processed configuration with environment variables resolved
        """
        llm_providers = config.get('llm_providers', {})

        for provider_name, provider_config in llm_providers.items():
            # Process API key
            if 'api_key_env' in provider_config:
                env_var = provider_config['api_key_env']
                api_key = os.getenv(env_var)

                if api_key:
                    provider_config['api_key'] = api_key
                    logger.debug(f"Loaded API key for {provider_name} from {env_var}")
                else:
                    logger.warning(
                        f"Environment variable {env_var} not set for {provider_name}"
                    )

            # Process API base URL
            if 'api_base_env' in provider_config:
                env_var = provider_config['api_base_env']
                api_base = os.getenv(env_var)

                if api_base:
                    provider_config['api_base'] = api_base
                    logger.debug(f"Loaded API base for {provider_name} from {env_var}")

            # Process organization ID
            if 'organization_id_env' in provider_config:
                env_var = provider_config['organization_id_env']
                org_id = os.getenv(env_var)

                if org_id:
                    provider_config['organization_id'] = org_id

            # Process deployment name (Azure)
            if 'deployment_name_env' in provider_config:
                env_var = provider_config['deployment_name_env']
                deployment = os.getenv(env_var)

                if deployment:
                    provider_config['deployment_name'] = deployment

        return config

    def _validate_llm_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate LLM configuration

        Args:
            config: LLM configuration to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        if 'llm_providers' not in config:
            raise ValidationError("LLM config missing 'llm_providers' section")

        llm_providers = config['llm_providers']

        if not llm_providers:
            raise ValidationError("No LLM providers configured")

        # Check for at least one enabled provider with API key
        enabled_with_key = False

        for provider_name, provider_config in llm_providers.items():
            if provider_config.get('enabled', False):
                if 'api_key' in provider_config and provider_config['api_key']:
                    enabled_with_key = True
                    break

        if not enabled_with_key:
            logger.warning("No enabled LLM providers with valid API keys found")

        return True

    def get_llm_provider_config(self, provider_name: str) -> LLMProviderConfig:
        """
        Get configuration for a specific LLM provider

        Args:
            provider_name: Name of the provider (e.g., "openai", "anthropic")

        Returns:
            LLMProviderConfig object

        Raises:
            ConfigurationError: If provider not found
        """
        config = self.load_llm_config()
        providers = config.get('llm_providers', {})

        if provider_name not in providers:
            raise ConfigurationError(f"LLM provider '{provider_name}' not found")

        provider_data = providers[provider_name]

        return LLMProviderConfig(
            name=provider_name,
            enabled=provider_data.get('enabled', False),
            api_key=provider_data.get('api_key'),
            api_base=provider_data.get('api_base'),
            models=provider_data.get('models', {}),
            parameters=provider_data.get('parameters', {})
        )

    def get_primary_llm_provider(self) -> LLMProviderConfig:
        """
        Get the primary LLM provider configuration

        Returns:
            LLMProviderConfig for the primary provider
        """
        config = self.load_llm_config()
        primary_provider = config.get('application', {}).get('primary_provider', 'openai')

        return self.get_llm_provider_config(primary_provider)

    def load_template(self, template_name: str) -> Any:
        """
        Load a report template

        Args:
            template_name: Name of the template file (without extension)

        Returns:
            Template data

        Raises:
            ConfigurationError: If template cannot be loaded
        """
        # Check cache
        if template_name in self._templates_cache:
            logger.debug(f"Using cached template: {template_name}")
            return self._templates_cache[template_name]

        # Try different file extensions
        for ext in ['.yaml', '.yml', '.json', '.txt']:
            template_path = self.templates_dir / f"{template_name}{ext}"

            if template_path.exists():
                if ext in ['.yaml', '.yml']:
                    data = self._load_yaml_file(template_path)
                elif ext == '.json':
                    with open(template_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        data = f.read()

                # Cache the template
                self._templates_cache[template_name] = data

                logger.info(f"Loaded template: {template_name}")
                return data

        raise ConfigurationError(f"Template not found: {template_name}")

    def list_available_standards(self) -> List[str]:
        """
        List all available standard codes

        Returns:
            List of standard codes
        """
        if not self.standards_dir.exists():
            return []

        yaml_files = list(self.standards_dir.glob("*.yaml")) + \
                     list(self.standards_dir.glob("*.yml"))

        return [f.stem for f in yaml_files]

    def list_available_templates(self) -> List[str]:
        """
        List all available template names

        Returns:
            List of template names
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for ext in ['.yaml', '.yml', '.json', '.txt']:
            templates.extend([f.stem for f in self.templates_dir.glob(f"*{ext}")])

        return list(set(templates))  # Remove duplicates

    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate that API keys are set for enabled providers

        Returns:
            Dictionary mapping provider names to validation status
        """
        config = self.load_llm_config()
        providers = config.get('llm_providers', {})

        validation_results = {}

        for provider_name, provider_config in providers.items():
            if provider_config.get('enabled', False):
                has_key = bool(provider_config.get('api_key'))
                validation_results[provider_name] = has_key

                if not has_key:
                    logger.warning(f"Provider {provider_name} is enabled but has no API key")

        return validation_results

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of loaded configurations

        Returns:
            Dictionary with configuration summary
        """
        summary = {
            'base_directory': str(self.base_dir),
            'standards_directory': str(self.standards_dir),
            'templates_directory': str(self.templates_dir),
            'available_standards': self.list_available_standards(),
            'available_templates': self.list_available_templates(),
            'loaded_standards': list(self._standards_cache.keys()),
            'llm_config_loaded': self._llm_config_cache is not None,
        }

        if self._llm_config_cache:
            config = self._llm_config_cache
            providers = config.get('llm_providers', {})
            enabled_providers = [
                name for name, cfg in providers.items()
                if cfg.get('enabled', False)
            ]
            summary['enabled_llm_providers'] = enabled_providers

        return summary

    def clear_cache(self):
        """Clear all cached configurations"""
        self._standards_cache.clear()
        self._llm_config_cache = None
        self._templates_cache.clear()
        logger.info("Configuration cache cleared")


# Utility functions

def get_config_loader(config_dir: Optional[Union[str, Path]] = None) -> ConfigLoader:
    """
    Get a ConfigLoader instance

    Args:
        config_dir: Optional path to config directory

    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(config_dir)


def load_env_file(env_file: Union[str, Path] = ".env") -> bool:
    """
    Load environment variables from a .env file

    Args:
        env_file: Path to .env file

    Returns:
        True if successful, False otherwise
    """
    env_path = Path(env_file)

    if not env_path.exists():
        logger.warning(f"Environment file not found: {env_file}")
        return False

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                match = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$', line, re.IGNORECASE)

                if match:
                    key, value = match.groups()

                    # Remove quotes if present
                    value = value.strip('"').strip("'")

                    # Set environment variable if not already set
                    if key not in os.environ:
                        os.environ[key] = value
                        logger.debug(f"Loaded environment variable: {key}")

        logger.info(f"Loaded environment variables from {env_file}")
        return True

    except Exception as e:
        logger.error(f"Error loading environment file {env_file}: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Load environment variables
    load_env_file()

    # Create config loader
    loader = ConfigLoader()

    # Get configuration summary
    summary = loader.get_config_summary()
    print("\nConfiguration Summary:")
    print(f"Base Directory: {summary['base_directory']}")
    print(f"\nAvailable Standards ({len(summary['available_standards'])}):")
    for std in summary['available_standards']:
        print(f"  - {std}")

    print(f"\nAvailable Templates ({len(summary['available_templates'])}):")
    for tpl in summary['available_templates']:
        print(f"  - {tpl}")

    # Load a specific standard
    try:
        iec_61215 = loader.load_standard('iec_61215')
        print(f"\nLoaded Standard: {iec_61215.code}")
        print(f"Full Name: {iec_61215.full_name}")
        print(f"Version: {iec_61215.version}")
    except Exception as e:
        print(f"Error loading standard: {e}")

    # Validate API keys
    api_validation = loader.validate_api_keys()
    print(f"\nAPI Key Validation:")
    for provider, is_valid in api_validation.items():
        status = "✓" if is_valid else "✗"
        print(f"  {status} {provider}")
