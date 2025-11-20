# Test Blocks 19-27: Implementation Roadmap

## Overview

This document provides a detailed implementation roadmap for developing the 9 test block modules from skeleton to production-ready state.

---

## Phase 1: Foundation & Setup (Week 1)

### Task 1.1: Repository Analysis & Planning
**Duration**: 1 day
**Owner**: Senior Developer

**Actions**:
1. Review reference implementations (commits a3c2d98, 65456ae)
2. Document patterns and best practices
3. Create implementation templates
4. Define coding standards
5. Setup code review process

**Deliverables**:
- Implementation guidelines document
- Code templates for each test type
- Coding standards checklist
- Code review template

### Task 1.2: Development Environment Setup
**Duration**: 1 day
**Owner**: Senior Developer

**Actions**:
1. Update pyproject.toml with Python 3.11+ requirement
2. Configure mypy for type checking
3. Setup CI/CD pipeline (GitHub Actions)
4. Create pre-commit hooks
5. Configure test framework

**Python Configuration**:
```toml
[tool.poetry]
python = "^3.11"

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=html"
```

### Task 1.3: Create Shared Infrastructure
**Duration**: 2 days
**Owner**: Mid-Level Developer

**Modules to Create**:

1. **Base Classes** (`src/tests/base.py`)
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MeasurementResult:
    """Container for test measurement results."""
    value: float
    unit: str
    uncertainty: float
    timestamp: datetime
    conditions: Dict[str, Any]
    equipment_id: str
    calibration_date: Optional[datetime] = None
    notes: Optional[str] = None


class TestBlockBase(ABC):
    """Base class for all test block implementations."""
    
    STANDARD: str = ""
    UNCERTAINTY_BUDGET: Dict[str, float] = {}
    
    def __init__(self, name: str):
        """Initialize test block."""
        self.name = name
        self.logger = logging.getLogger(f"test.{name}")
        self.results: list[MeasurementResult] = []
    
    @abstractmethod
    def setup(self) -> bool:
        """Setup test equipment and environment."""
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the test procedure."""
        pass
    
    @abstractmethod
    def teardown(self) -> bool:
        """Cleanup after test."""
        pass
    
    def calculate_uncertainty(self, measurement: MeasurementResult) -> float:
        """
        Calculate combined measurement uncertainty per ISO Guide 35.
        
        Args:
            measurement: Raw measurement
            
        Returns:
            Expanded uncertainty (k=2)
        """
        # Type A: From measurement repetition
        type_a = self._calculate_type_a_uncertainty()
        
        # Type B: From equipment specifications
        type_b = self._calculate_type_b_uncertainty(measurement)
        
        # Combined uncertainty
        uc = (type_a**2 + type_b**2) ** 0.5
        
        # Expanded uncertainty (k=2 for 95% confidence)
        return 2 * uc
    
    @abstractmethod
    def _calculate_type_a_uncertainty(self) -> float:
        """Calculate Type A uncertainty (statistical)."""
        pass
    
    @abstractmethod
    def _calculate_type_b_uncertainty(self, measurement: MeasurementResult) -> float:
        """Calculate Type B uncertainty (equipment specs)."""
        pass


class EquipmentDriver(ABC):
    """Base class for equipment drivers."""
    
    def __init__(self, address: str):
        """Initialize equipment driver."""
        self.address = address
        self.connected = False
        self.calibration_date: Optional[datetime] = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to equipment."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from equipment."""
        pass
    
    @abstractmethod
    def calibrate(self) -> bool:
        """Perform equipment calibration."""
        pass
    
    @abstractmethod
    def measure(self) -> float:
        """Perform measurement."""
        pass
    
    def is_calibrated(self, days_threshold: int = 365) -> bool:
        """Check if equipment is within calibration validity."""
        if not self.calibration_date:
            return False
        from datetime import timedelta
        return (datetime.now() - self.calibration_date) < timedelta(days=days_threshold)
```

2. **Data Storage** (`src/tests/storage.py`)
```python
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime


class TestDataStorage:
    """Handle test data storage with traceability."""
    
    def __init__(self, base_path: Path):
        """Initialize storage handler."""
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_measurement(self, test_id: str, data: Dict[str, Any]) -> bool:
        """
        Save measurement data with metadata.
        
        Args:
            test_id: Unique test identifier
            data: Measurement data dictionary
            
        Returns:
            True if successful
        """
        try:
            # Add timestamp and metadata
            record = {
                'timestamp': datetime.now().isoformat(),
                'test_id': test_id,
                'data': data,
                'version': '1.0'
            }
            
            # Save to JSON file
            file_path = self.base_path / f"{test_id}_{datetime.now().isoformat()}.json"
            with open(file_path, 'w') as f:
                json.dump(record, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save measurement: {e}")
            return False
    
    def load_measurement(self, file_path: Path) -> Dict[str, Any]:
        """Load measurement data from file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_test_history(self, test_id: str) -> List[Dict[str, Any]]:
        """Get all measurements for a test."""
        results = []
        for file_path in self.base_path.glob(f"{test_id}_*.json"):
            results.append(self.load_measurement(file_path))
        return sorted(results, key=lambda x: x['timestamp'])
```

**Deliverables**:
- `src/tests/base.py` - Base classes
- `src/tests/storage.py` - Data storage
- `src/tests/equipment.py` - Equipment interfaces
- `tests/test_base.py` - Unit tests for base classes

---

## Phase 2: Core Implementation (Weeks 2-4)

### Implementation Pattern for Each Test Block

**File Structure**:
```
src/tests/{module}/
├── __init__.py (public API, version)
├── core.py (main test class)
├── equipment.py (device drivers)
├── data_acquisition.py (measurement loop)
├── calibration.py (ISO 17025 support)
└── validation.py (data quality checks)

tests/{module}/
├── test_core.py (unit tests)
├── test_equipment.py (mock equipment tests)
├── test_integration.py (end-to-end tests)
└── fixtures/ (test data)
```

### Priority 1: Branch 19 - I-V Curve (2 weeks)

**Reference**: Commit a3c2d98 (use as template)

**Implementation Steps**:

1. **Create Core Module** (2-3 days)
```python
# src/tests/iv_curve/core.py
from src.tests.base import TestBlockBase, MeasurementResult
from typing import Dict, Tuple, Optional
import numpy as np
from scipy import optimize
from datetime import datetime


class IVCurveAnalyzer(TestBlockBase):
    """I-V Curve analyzer per IEC 60904-1:2020."""
    
    STANDARD = "IEC 60904-1:2020"
    STC_TEMP = 25.0  # °C
    STC_IRRADIANCE = 1000.0  # W/m²
    
    def __init__(self):
        """Initialize I-V analyzer."""
        super().__init__("iv_curve")
        self.raw_data: Dict = {}
    
    def setup(self) -> bool:
        """Setup SMU and measurement equipment."""
        # Check equipment connection
        # Verify calibration status
        # Initialize measurement parameters
        return True
    
    def execute(self) -> bool:
        """Execute I-V measurement sweep."""
        try:
            self.logger.info("Starting I-V measurement")
            
            # Get measurement conditions
            temperature = self._get_cell_temperature()
            irradiance = self._get_irradiance()
            
            # Perform V-I sweep
            voltage_data, current_data = self._perform_sweep()
            
            # Store raw data
            self.raw_data = {
                'voltage': voltage_data,
                'current': current_data,
                'temperature': temperature,
                'irradiance': irradiance
            }
            
            # Calculate parameters
            params = self._calculate_parameters()
            
            # Create measurement result
            result = MeasurementResult(
                value=params['Pmax'],
                unit='W',
                uncertainty=self.calculate_uncertainty(MeasurementResult(...)),
                timestamp=datetime.now(),
                conditions={'T': temperature, 'G': irradiance},
                equipment_id='SMU_001'
            )
            
            self.results.append(result)
            self.logger.info(f"I-V measurement complete: Pmax={result.value}W")
            return True
            
        except Exception as e:
            self.logger.error(f"I-V measurement failed: {e}")
            return False
    
    def teardown(self) -> bool:
        """Shutdown equipment."""
        # Turn off voltage/current
        # Save data
        # Log completion
        return True
    
    def _perform_sweep(self) -> Tuple[np.ndarray, np.ndarray]:
        """Perform voltage sweep and collect I-V data."""
        voltages = np.linspace(0, self.voc_estimate * 1.1, 100)
        currents = []
        
        for v in voltages:
            i = self._measure_current_at_voltage(v)
            currents.append(i)
        
        return voltages, np.array(currents)
    
    def _calculate_parameters(self) -> Dict[str, float]:
        """Calculate I-V parameters per IEC 60904-1."""
        V = np.array(self.raw_data['voltage'])
        I = np.array(self.raw_data['current'])
        P = V * I
        
        # Find parameters
        isc = self._find_isc(V, I)
        voc = self._find_voc(V, I)
        pmax_idx = np.argmax(P)
        pmax = P[pmax_idx]
        vmp = V[pmax_idx]
        imp = I[pmax_idx]
        ff = pmax / (voc * isc) if (voc * isc) > 0 else 0.0
        
        return {
            'Voc': voc,
            'Isc': isc,
            'Vmp': vmp,
            'Imp': imp,
            'Pmax': pmax,
            'FF': ff
        }
    
    def _calculate_type_a_uncertainty(self) -> float:
        """Type A: From measurement repetition."""
        # Based on multiple measurements
        return 0.005  # 0.5% placeholder
    
    def _calculate_type_b_uncertainty(self, measurement: MeasurementResult) -> float:
        """Type B: From equipment specifications."""
        # Based on SMU accuracy specs
        return 0.003  # 0.3% placeholder
    
    # ... additional helper methods
```

2. **Create Equipment Driver** (1-2 days)
```python
# src/tests/iv_curve/equipment.py
from src.tests.base import EquipmentDriver
from typing import Optional


class SMUDriver(EquipmentDriver):
    """Source Measurement Unit (SMU) driver."""
    
    def __init__(self, address: str, model: str = "Keysight_B2901A"):
        """Initialize SMU driver."""
        super().__init__(address)
        self.model = model
        self.interface = None  # Placeholder for VISA/GPIB interface
    
    def connect(self) -> bool:
        """Connect to SMU via GPIB/LAN."""
        try:
            # Pseudocode for VISA connection
            # import pyvisa
            # rm = pyvisa.ResourceManager()
            # self.interface = rm.open_resource(self.address)
            self.connected = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to SMU: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from SMU."""
        if self.interface:
            self.interface.close()
        self.connected = False
        return True
    
    def calibrate(self) -> bool:
        """Calibrate SMU."""
        if not self.connected:
            return False
        # Send calibration command to SMU
        return True
    
    def measure(self) -> float:
        """Measure current at present voltage."""
        if not self.connected:
            raise RuntimeError("Not connected to SMU")
        # Return measured current
        return 0.0  # Placeholder
    
    def set_voltage(self, voltage: float) -> bool:
        """Set output voltage."""
        if not self.connected:
            return False
        # Send voltage command to SMU
        return True
    
    def get_voltage(self) -> float:
        """Read back output voltage."""
        if not self.connected:
            return 0.0
        # Query voltage from SMU
        return 0.0  # Placeholder
```

3. **Create Unit Tests** (1-2 days)
```python
# tests/iv_curve/test_core.py
import pytest
from src.tests.iv_curve.core import IVCurveAnalyzer
from src.tests.iv_curve.equipment import SMUDriver
import numpy as np


@pytest.fixture
def analyzer():
    """Create analyzer instance."""
    return IVCurveAnalyzer()


@pytest.fixture
def smu_driver():
    """Create mock SMU driver."""
    return SMUDriver(address="GPIB0::3::INSTR")


class TestIVCurveAnalyzer:
    """Test I-V curve analyzer."""
    
    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.standard == "IEC 60904-1:2020"
        assert len(analyzer.results) == 0
    
    def test_parameter_calculation(self, analyzer):
        """Test parameter extraction."""
        # Create synthetic I-V curve
        V = np.linspace(0, 40, 100)
        I = np.linspace(10, 0, 100)
        
        analyzer.raw_data = {
            'voltage': V,
            'current': I,
            'temperature': 25.0,
            'irradiance': 1000
        }
        
        params = analyzer._calculate_parameters()
        
        assert 'Voc' in params
        assert 'Isc' in params
        assert 'Pmax' in params
        assert params['Pmax'] > 0
    
    def test_uncertainty_calculation(self, analyzer):
        """Test uncertainty calculation."""
        from src.tests.base import MeasurementResult
        from datetime import datetime
        
        measurement = MeasurementResult(
            value=100.0,
            unit='W',
            uncertainty=0.0,
            timestamp=datetime.now(),
            conditions={'T': 25.0, 'G': 1000},
            equipment_id='SMU_001'
        )
        
        uncertainty = analyzer.calculate_uncertainty(measurement)
        assert uncertainty > 0
        assert uncertainty < measurement.value * 0.1  # < 10% uncertainty
```

4. **Create Calibration Module** (1 day)
```python
# src/tests/iv_curve/calibration.py
from src.tests.base import EquipmentDriver
from datetime import datetime, timedelta
from typing import Optional, List


class CalibrationManager:
    """Manage equipment calibration per ISO 17025."""
    
    def __init__(self):
        """Initialize calibration manager."""
        self.certificates: List[Dict] = []
    
    def add_certificate(
        self,
        equipment_id: str,
        calibration_date: datetime,
        next_calibration: datetime,
        uncertainty: float,
        certificate_file: Optional[str] = None
    ) -> bool:
        """
        Register calibration certificate.
        
        Args:
            equipment_id: Equipment identifier
            calibration_date: When calibration was performed
            next_calibration: Next calibration due date
            uncertainty: Measurement uncertainty from certificate
            certificate_file: Path to certificate file
            
        Returns:
            True if registered successfully
        """
        certificate = {
            'equipment_id': equipment_id,
            'calibration_date': calibration_date,
            'next_calibration': next_calibration,
            'uncertainty': uncertainty,
            'certificate_file': certificate_file
        }
        self.certificates.append(certificate)
        return True
    
    def is_calibrated(self, equipment_id: str) -> bool:
        """Check if equipment is within calibration validity."""
        for cert in self.certificates:
            if cert['equipment_id'] == equipment_id:
                return datetime.now() < cert['next_calibration']
        return False
    
    def get_uncertainty(self, equipment_id: str) -> float:
        """Get calibration uncertainty for equipment."""
        for cert in self.certificates:
            if cert['equipment_id'] == equipment_id:
                return cert['uncertainty']
        return None
```

**Deliverables for Branch 19**:
- ✓ Core analyzer with 500+ lines of code
- ✓ SMU driver with VISA support
- ✓ Data acquisition module
- ✓ Calibration support
- ✓ Unit tests (>80% coverage)
- ✓ Integration tests with mock equipment
- ✓ Documentation and examples

### Priority 2: Branch 20 - Electroluminescence (2 weeks)

**Reference**: Commit 65456ae

**Key Components**:
1. Image processor (multi-format loading, preprocessing)
2. Defect detector (ML-based crack detection)
3. Report generator (HTML with IEC compliance)

**Implementation Path**:
- Copy reference implementation structure
- Adapt to module conventions
- Add equipment camera driver
- Create test fixtures with sample images
- Implement compliance checking

### Similar Pattern for Branches 21-27

Each branch follows the same structure:
1. Copy/adapt reference implementation
2. Create equipment driver
3. Implement data acquisition
4. Add calibration support
5. Create comprehensive tests

---

## Phase 3: Integration & Compliance (Weeks 5-6)

### Task 3.1: ISO 17025 Integration
**Duration**: 1 week

**Implementations**:
1. Measurement uncertainty per ISO Guide 35
2. Equipment calibration tracking
3. Data traceability logging
4. Quality control procedures
5. Documentation management

### Task 3.2: Equipment Interface Standardization
**Duration**: 3-4 days

**Create Standard Drivers**:
1. VISA-based instruments (Fluke, Hioki, Keysight)
2. Serial interface devices
3. Network-connected equipment
4. USB devices

### Task 3.3: Compliance Validation
**Duration**: 3-4 days

**Checklist**:
- [ ] IEC standards compliance per test
- [ ] ISO 17025 requirements met
- [ ] Measurement uncertainty calculated
- [ ] Traceability documented
- [ ] Equipment qualified
- [ ] Procedures documented
- [ ] Staff trained

---

## Phase 4: Testing & Deployment (Weeks 7-8)

### Task 4.1: Comprehensive Testing
**Duration**: 1 week

**Test Types**:
1. Unit tests (algorithm validation)
2. Integration tests (equipment simulation)
3. Compliance tests (standards adherence)
4. Performance tests (speed/memory)
5. Stress tests (error handling)

### Task 4.2: Documentation
**Duration**: 3-4 days

**Documentation**:
1. API documentation (Sphinx)
2. User guides per test type
3. Equipment setup guides
4. Troubleshooting guides
5. Example scripts

### Task 4.3: Deployment & Training
**Duration**: 3-4 days

**Actions**:
1. Code review and approval
2. Merge to main branch
3. Release notes
4. User training
5. Support setup

---

## Tools & Dependencies

### Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
numpy = "^1.24.0"
scipy = "^1.10.0"
pyvisa = "^1.14.0"  # Equipment communication
pillow = "^10.0.0"  # Image processing
opencv-python = "^4.8.0"  # Advanced image processing
matplotlib = "^3.7.0"  # Plotting
pydantic = "^2.0.0"  # Data validation
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
mypy = "^1.5.0"
black = "^23.9.0"
ruff = "^0.10.0"
```

### Development Tools

```bash
# Code quality
mypy src/ tests/  # Type checking
black src/ tests/  # Code formatting
ruff check src/ tests/  # Linting
pytest --cov=src/  # Testing with coverage

# Documentation
sphinx-build -b html docs/ build/html

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

---

## Success Metrics

### Code Quality
- Type hint coverage: > 90%
- Test coverage: > 80%
- Code complexity: < 10
- Documentation: 100%

### Compliance
- ISO 17025: All requirements met
- IEC standards: Compliance verified
- Measurement uncertainty: Calculated & documented
- Traceability: Complete audit trail

### Performance
- Measurement time: < 60 seconds/test
- Data logging: < 100ms
- Report generation: < 5 seconds
- Memory usage: < 500MB

### Reliability
- Error recovery: Automatic
- Data integrity: Checksums verified
- Equipment reconnection: Automatic
- Test repeatability: > 95%

---

## Risk Management

### Technical Risks

1. **Equipment Driver Complexity**
   - Mitigation: Use standard VISA library
   - Fallback: Mock equipment for testing
   - Timeline: +1 week

2. **Measurement Accuracy**
   - Mitigation: Reference standards available
   - Validation: Compare with known samples
   - Timeline: +3 days

3. **Data Management**
   - Mitigation: Use structured storage (SQLite/PostgreSQL)
   - Backup: Daily backups required
   - Timeline: Built-in

### Resource Risks

1. **Staff Availability**
   - Contingency: Cross-training required
   - Buffer: +20% schedule padding

2. **Equipment Availability**
   - Contingency: Simulation/mock drivers
   - Testing: Early access to equipment needed

3. **Standards Documentation**
   - Contingency: Use internal reference implementations
   - Verification: Expert review required

---

## Next Steps

1. **Week 1**: Approve roadmap and allocate resources
2. **Weeks 2-4**: Execute Phase 1-2 implementation
3. **Weeks 5-6**: Compliance integration and validation
4. **Weeks 7-8**: Testing, documentation, and deployment

**Go-live Target**: 8 weeks from start

