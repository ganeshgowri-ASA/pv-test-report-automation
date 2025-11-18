# Google Gemini LLM Integration Guide

## Overview

This document provides comprehensive guidance on using Google Gemini for PV (Photovoltaic) test report automation. The integration enables advanced AI capabilities including vision-based defect detection, compliance checking, and predictive failure analysis.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Quick Start](#quick-start)
5. [Core Capabilities](#core-capabilities)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)
8. [Error Handling](#error-handling)
9. [Performance Optimization](#performance-optimization)
10. [Examples](#examples)

---

## Features

### ✅ Core Capabilities

- **Text Generation**: Natural language analysis and report generation
- **Vision Analysis**: Multi-modal image analysis for defect detection
- **EL Image Analysis**: Electroluminescence image defect detection
- **Thermal Imaging**: Hotspot and thermal anomaly detection
- **Compliance Checking**: Automated verification against PV standards
- **Predictive Analysis**: Failure prediction and lifespan estimation
- **Batch Processing**: Concurrent analysis of multiple images
- **Safety Filters**: Content safety and quality controls

### 🎯 Use Cases

1. **Visual Defect Analysis**: Analyze EL/thermal images for cracks, hotspots, delamination
2. **Multi-modal Reports**: Combine text analysis with image understanding
3. **Predictive Maintenance**: Identify failure patterns before they occur
4. **Test Optimization**: Suggest improvements to testing procedures
5. **Compliance Verification**: Validate against IEC standards

---

## Installation

### Prerequisites

- Python 3.9 or higher
- Google API key for Gemini

### Install Dependencies

```bash
# Using pip
pip install -r requirements/base.txt

# Or install development dependencies
pip install -r requirements/dev.txt

# Or install the package in editable mode
pip install -e .
```

### Required Packages

```text
google-generativeai>=0.8.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
httpx>=0.24.0
pillow>=10.0.0
aiofiles>=23.0.0
```

---

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Copy the example configuration
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_VISION_MODEL=gemini-2.0-flash-exp

# LLM Configuration
LLM_PROVIDER=gemini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
LLM_TOP_P=0.95
LLM_TOP_K=40

# Application Settings
APP_NAME=PV Test Report Automation
LOG_LEVEL=INFO
ENABLE_SAFETY_FILTERS=true

# File Upload Settings
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=png,jpg,jpeg,tiff,bmp
UPLOAD_DIR=./uploads
```

### Getting an API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

---

## Quick Start

### Basic Usage

```python
import asyncio
from pv_automation.services.llm import GeminiProvider
from pv_automation.models.llm_models import GeminiRequest

async def main():
    # Initialize provider
    provider = GeminiProvider(api_key="your_api_key")

    # Create request
    request = GeminiRequest(
        prompt="Explain EL imaging in PV testing",
        temperature=0.7
    )

    # Generate response
    response = await provider.generate_text(request)
    print(response.content)

asyncio.run(main())
```

---

## Core Capabilities

### 1. Text Generation

Generate technical analysis and reports:

```python
from pv_automation.models.llm_models import GeminiRequest

request = GeminiRequest(
    prompt="Analyze this PV module test data...",
    model="gemini-2.0-flash-exp",
    temperature=0.7,
    max_tokens=2048
)

response = await provider.generate_text(request)
```

**Parameters:**
- `prompt`: Your text prompt
- `model`: Model name (default: gemini-2.0-flash-exp)
- `temperature`: 0.0-2.0 (creativity vs consistency)
- `max_tokens`: Maximum response length
- `top_p`: Nucleus sampling (0.0-1.0)
- `top_k`: Top-k sampling (1-100)

### 2. Image Analysis

Analyze PV module images for defects:

```python
from pv_automation.models.llm_models import VisionAnalysisRequest

request = VisionAnalysisRequest(
    image_path="/path/to/el_image.png",
    image_type="EL",
    standard="IEC 61215",
    additional_context="Module is 5 years old"
)

response = await provider.analyze_image(request)

print(f"Compliance: {response.compliance_status}")
print(f"Defects found: {len(response.defects)}")
```

**Supported Image Types:**
- `EL`: Electroluminescence imaging
- `Thermal`: Thermal/infrared imaging
- `Visual`: Visual inspection photos

**Detected Defects:**
- Cracks (micro-cracks, cell breakage)
- Hotspots
- Delamination
- Discoloration
- Grid line defects
- Bypass diode failures

### 3. Compliance Checking

Verify test reports against standards:

```python
from pv_automation.models.llm_models import ComplianceCheckRequest

request = ComplianceCheckRequest(
    report_data={
        "module_id": "PV-001",
        "power_output": 400,
        "efficiency": 20.5,
        # ... more test data
    },
    standard="IEC 61215",
    check_missing_data=True
)

response = await provider.check_compliance(request)

print(f"Status: {response.compliance_status}")
for violation in response.violations:
    print(f"Violation: {violation}")
```

**Supported Standards:**
- IEC 61215 (Crystalline silicon modules)
- IEC 61730 (Safety qualification)
- IEC 61853 (Performance testing)
- IEC 62804 (PID testing)
- IEC 61701 (Salt mist corrosion)
- And more...

### 4. Predictive Analysis

Predict failure probability and lifespan:

```python
from pv_automation.models.llm_models import PredictiveAnalysisRequest

request = PredictiveAnalysisRequest(
    test_data={
        "initial_power": 400,
        "current_power": 388,
        "degradation_rate": 0.61
    },
    module_age_years=5.5,
    warranty_period_years=25,
    environmental_factors={
        "avg_temperature": 35,
        "humidity": 15,
        "uv_exposure": "high"
    }
)

response = await provider.predict_failures(request)

print(f"Failure Probability: {response.failure_probability:.1%}")
print(f"Estimated Lifespan: {response.estimated_lifespan_years} years")
```

### 5. Batch Processing

Analyze multiple images concurrently:

```python
requests = [
    VisionAnalysisRequest(image_path=img, image_type="EL")
    for img in image_paths
]

responses = await provider.batch_analyze_images(requests)
```

---

## API Reference

### GeminiProvider

Main class for Gemini integration.

#### Initialization

```python
provider = GeminiProvider(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    vision_model: Optional[str] = None,
    settings: Optional[Settings] = None
)
```

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `generate_text(request)` | Generate text from prompt | `GeminiResponse` |
| `analyze_image(request)` | Analyze image for defects | `VisionAnalysisResponse` |
| `check_compliance(request)` | Check standard compliance | `ComplianceCheckResponse` |
| `predict_failures(request)` | Predict failure probability | `PredictiveAnalysisResponse` |
| `batch_analyze_images(requests)` | Batch process images | `List[VisionAnalysisResponse]` |
| `health_check()` | Check API health | `Dict[str, Any]` |
| `get_model_info()` | Get model configuration | `Dict[str, Any]` |

### Data Models

#### GeminiRequest

```python
class GeminiRequest(BaseModel):
    prompt: str
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40
    images: Optional[List[str]] = None
    system_instruction: Optional[str] = None
```

#### GeminiResponse

```python
class GeminiResponse(BaseModel):
    content: str
    safety_ratings: List[SafetyRating]
    finish_reason: str
    prompt_token_count: Optional[int]
    candidates_token_count: Optional[int]
    total_token_count: Optional[int]
    model: str
    timestamp: datetime
```

#### VisionAnalysisResponse

```python
class VisionAnalysisResponse(BaseModel):
    defects: List[DefectAnalysis]
    overall_assessment: str
    compliance_status: str
    confidence_score: float
    raw_analysis: str
    image_metadata: Optional[Dict[str, Any]]
    timestamp: datetime
```

---

## Best Practices

### 1. API Key Security

```python
# ❌ Bad: Hardcoded API key
provider = GeminiProvider(api_key="AIza...")

# ✅ Good: Use environment variables
provider = GeminiProvider()  # Reads from GEMINI_API_KEY
```

### 2. Temperature Settings

```python
# Creative tasks (summaries, recommendations)
temperature = 0.7-1.0

# Precise tasks (compliance checking, data extraction)
temperature = 0.0-0.3

# Balanced (general analysis)
temperature = 0.4-0.6
```

### 3. Error Handling

```python
from pv_automation.services.llm.base import (
    LLMProviderError,
    RateLimitError,
    SafetyFilterError
)

try:
    response = await provider.analyze_image(request)
except RateLimitError as e:
    # Implement exponential backoff
    await asyncio.sleep(60)
except SafetyFilterError as e:
    # Content was blocked
    logger.warning(f"Content blocked: {e}")
except LLMProviderError as e:
    # Generic error
    logger.error(f"Analysis failed: {e}")
```

### 4. Image Optimization

```python
# Resize large images before analysis
from PIL import Image

def optimize_image(image_path, max_size=2048):
    img = Image.open(image_path)
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size))
        img.save(image_path)
```

### 5. Batch Processing

```python
# Process in chunks to avoid rate limits
async def process_in_batches(requests, batch_size=5):
    results = []
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i+batch_size]
        batch_results = await provider.batch_analyze_images(batch)
        results.extend(batch_results)
        await asyncio.sleep(1)  # Rate limiting
    return results
```

---

## Error Handling

### Exception Hierarchy

```
LLMProviderError (base)
├── APIKeyError
├── RateLimitError
├── SafetyFilterError
├── ModelNotFoundError
├── ImageProcessingError
└── NetworkError
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `APIKeyError` | Invalid/missing API key | Check GEMINI_API_KEY |
| `RateLimitError` | Too many requests | Implement backoff |
| `SafetyFilterError` | Content blocked | Review content |
| `ImageProcessingError` | Invalid image file | Check file format/size |
| `NetworkError` | Connection failed | Check network |

---

## Performance Optimization

### 1. Model Selection

- **gemini-2.0-flash-exp**: Fast, cost-effective (recommended)
- **gemini-pro**: Higher quality, slower
- **gemini-pro-vision**: Vision tasks (deprecated, use gemini-2.0-flash-exp)

### 2. Concurrent Processing

```python
# Process multiple requests concurrently
import asyncio

tasks = [
    provider.analyze_image(req1),
    provider.check_compliance(req2),
    provider.predict_failures(req3)
]

results = await asyncio.gather(*tasks)
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_analysis(image_hash):
    # Cache frequently analyzed images
    pass
```

---

## Examples

See `examples/gemini_basic_usage.py` for complete working examples:

1. Basic text generation
2. EL image defect analysis
3. Compliance checking
4. Predictive failure analysis
5. Batch image processing
6. API health checks
7. Model information

Run examples:

```bash
# Set your API key
export GEMINI_API_KEY="your_api_key"

# Run examples
python examples/gemini_basic_usage.py
```

---

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=pv_automation --cov-report=html

# Specific test file
pytest tests/unit/services/llm/test_gemini_provider.py

# Skip tests requiring API key
pytest -m "not requires_api_key"
```

---

## Troubleshooting

### Issue: "Invalid API key"

**Solution**: Verify your API key is correct and has Gemini API enabled.

### Issue: "Rate limit exceeded"

**Solution**: Implement exponential backoff or reduce request frequency.

### Issue: "Image too large"

**Solution**: Resize images or increase `MAX_IMAGE_SIZE_MB` in settings.

### Issue: "Safety filter triggered"

**Solution**: Review content or disable safety filters for technical content.

---

## Support

- **Documentation**: This file and code docstrings
- **Examples**: `examples/` directory
- **Tests**: `tests/` directory for usage patterns
- **Issues**: GitHub issue tracker

---

## License

MIT License - See LICENSE file for details.

---

## Version History

- **v0.1.0** (2024-01): Initial Gemini integration
  - Text generation
  - Vision analysis
  - Compliance checking
  - Predictive analysis
  - Batch processing
