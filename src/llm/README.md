# LLM Integration Module

Production-ready LLM integration for AI-powered PV test report analysis, compliance checking, and summarization.

## Overview

This module provides comprehensive integration with multiple Large Language Model (LLM) providers to enable intelligent analysis and processing of PV test reports. It includes robust error handling, caching, rate limiting, and usage tracking.

## Features

### Core Capabilities
- **Multi-Provider Support**: OpenAI GPT-4, Google Gemini, with extensible architecture
- **Async Operations**: Full async/await support for high-performance concurrent processing
- **Smart Caching**: Automatic response caching to reduce costs and improve performance
- **Rate Limiting**: Token bucket rate limiting with automatic retry and backoff
- **Usage Tracking**: Comprehensive cost and usage analytics per model
- **Error Handling**: Robust error handling with configurable retry logic

### AI-Powered Features
1. **Report Analysis**: Deep analysis of PV test reports with technical insights
2. **Compliance Checking**: Automated verification against international standards (IEC 61215, IEC 61730)
3. **Report Summarization**: Multi-format, multi-language summary generation
4. **Data Extraction**: Structured data extraction from text and images
5. **Multi-Modal Analysis**: Combined text and image analysis with Gemini

## Installation

### Dependencies

```bash
pip install openai google-generativeai
```

### API Keys

Set environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"
```

Or configure programmatically:

```python
from llm import LLMConfig, LLMProvider

config = LLMConfig()
config.set_api_key(LLMProvider.OPENAI, "your-key")
config.set_api_key(LLMProvider.GEMINI, "your-key")
```

## Quick Start

### Basic GPT Integration

```python
from llm import GPTIntegration, ModelType
import asyncio

# Initialize
gpt = GPTIntegration(model_type=ModelType.GPT_4_TURBO)

# Analyze a report
report_data = {
    'module_id': 'PV-001',
    'test_results': {'power': 300, 'efficiency': 18.5}
}

# Synchronous
response = gpt.analyze_report(report_data)
print(response.content)

# Asynchronous
async def analyze():
    response = await gpt.analyze_report_async(report_data)
    return response

result = asyncio.run(analyze())
```

### Gemini Multi-Modal Analysis

```python
from llm import GeminiIntegration, ImageData
from pathlib import Path

# Initialize
gemini = GeminiIntegration()

# Analyze chart image
async def analyze_chart():
    chart_path = Path("test_results_chart.png")
    response = await gemini.analyze_chart(
        chart_path,
        context="This is a power degradation chart"
    )
    return response.content

result = asyncio.run(analyze_chart())
```

### Compliance Checking

```python
from llm import ComplianceChecker

# Initialize
checker = ComplianceChecker()

# Check compliance against IEC 61215
async def check_compliance():
    report_data = {
        'module_id': 'PV-001',
        'test_results': {
            'visual_inspection': {'status': 'pass'},
            'power_measurement': {'pmax': 305, 'deviation': 1.7}
        }
    }

    result = await checker.check_compliance(
        report_data,
        standard="IEC 61215"
    )

    print(f"Compliance Rate: {result.compliance_rate}%")
    print(f"Status: {result.overall_status.value}")

    for gap in result.gaps:
        print(f"Gap: {gap.requirement_description}")
        print(f"Severity: {gap.severity.value}")
        print(f"Recommendation: {gap.recommendation}")

    return result

result = asyncio.run(check_compliance())
```

### Report Summarization

```python
from llm import (
    ReportSummarizer,
    SummaryConfig,
    SummaryType,
    SummaryFormat,
    Language
)

# Initialize
summarizer = ReportSummarizer()

# Configure summary
config = SummaryConfig(
    summary_type=SummaryType.EXECUTIVE,
    format=SummaryFormat.MARKDOWN,
    language=Language.ENGLISH,
    max_words=500,
    include_recommendations=True
)

# Generate summary
async def generate_summary():
    report_data = {
        'module_id': 'PV-001',
        'test_results': {...}
    }

    summary = await summarizer.generate_summary(report_data, config)

    # Export to file
    summarizer.export_summary(summary, "summary.md")

    return summary

result = asyncio.run(generate_summary())
```

## Advanced Usage

### Batch Processing

```python
# Batch analyze multiple reports
async def batch_process():
    reports = [
        {'module_id': 'PV-001', ...},
        {'module_id': 'PV-002', ...},
        {'module_id': 'PV-003', ...}
    ]

    responses = await gpt.batch_analyze(reports)
    return responses
```

### Custom Caching

```python
from pathlib import Path

# Configure custom cache
config = LLMConfig(cache_dir=Path("/custom/cache"))
config.cache_ttl = timedelta(days=30)  # 30-day cache

gpt = GPTIntegration(config, enable_cache=True)
```

### Usage Tracking

```python
# Get usage statistics
summary = config.get_usage_summary()

print(f"Total Cost: ${summary['total_cost']:.2f}")
print(f"Total Requests: {summary['total_requests']}")
print(f"Total Tokens: {summary['total_tokens']}")

# Per-model stats
for model, stats in summary['by_model'].items():
    print(f"{model}: {stats['total_requests']} requests, ${stats['total_cost']:.2f}")

# Reset stats
config.reset_usage_stats()
```

### Rate Limiting Configuration

```python
from llm import RateLimitConfig

# Custom rate limits
rate_config = RateLimitConfig(
    requests_per_minute=30,
    tokens_per_minute=50000,
    max_retries=5,
    retry_delay=2.0,
    exponential_backoff=True
)

config.rate_limiters[LLMProvider.OPENAI] = RateLimiter(rate_config)
```

## Module Structure

```
src/llm/
├── __init__.py                 # Package exports
├── llm_config.py              # Configuration and management
├── gpt_integration.py         # OpenAI GPT integration
├── gemini_integration.py      # Google Gemini integration
├── compliance_checker.py      # Compliance verification
├── report_summarizer.py       # Report summarization
├── README.md                  # This file
└── tests/
    ├── __init__.py
    ├── conftest.py            # Shared test fixtures
    ├── test_llm_config.py
    ├── test_gpt_integration.py
    ├── test_compliance_checker.py
    └── test_report_summarizer.py
```

## Configuration

### Model Selection

Available models:

```python
from llm import ModelType

# OpenAI Models
ModelType.GPT_4_TURBO          # Best quality, supports vision
ModelType.GPT_4                # High quality
ModelType.GPT_35_TURBO         # Fast and economical

# Google Gemini Models
ModelType.GEMINI_15_PRO        # Best quality, large context
ModelType.GEMINI_PRO_VISION    # Supports vision
ModelType.GEMINI_PRO           # Fast and economical
```

### Cost Information

Approximate costs (per 1K tokens):

| Model | Input | Output |
|-------|-------|--------|
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-4 | $0.03 | $0.06 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| Gemini 1.5 Pro | $0.00125 | $0.00375 |
| Gemini Pro | $0.00025 | $0.0005 |

## Standards Database

Built-in support for PV testing standards:

### IEC 61215 - Terrestrial PV modules
- Visual Inspection (10.1)
- Maximum Power Determination (10.2)
- Thermal Cycling (10.8)
- Damp Heat Test (10.11)
- Humidity Freeze (10.13)
- Mechanical Load Test (10.16)

### IEC 61730 - PV module safety
- Continuity of Grounding (MST-01)
- Wet Leakage Current (MST-23)

### Custom Requirements

```python
from llm import StandardRequirement

custom_req = StandardRequirement(
    id="CUSTOM-001",
    standard="Internal Standard",
    section="A.1",
    description="Custom test requirement",
    category="Performance",
    mandatory=True,
    acceptance_criteria="Must meet internal specs"
)

result = await checker.check_compliance(
    report_data,
    standard="Internal Standard",
    custom_requirements=[custom_req]
)
```

## Multi-Language Support

Supported languages for summaries:

- English (en)
- German (de)
- Spanish (es)
- French (fr)
- Italian (it)
- Portuguese (pt)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)

```python
config = SummaryConfig(language=Language.GERMAN)
summary = await summarizer.generate_summary(report_data, config)
```

## Testing

### Run All Tests

```bash
pytest src/llm/tests/
```

### Run Specific Test Categories

```bash
# Unit tests only (default)
pytest src/llm/tests/ -v

# Include integration tests
pytest src/llm/tests/ --integration

# Include tests requiring API keys
pytest src/llm/tests/ --api-tests

# Run with coverage
pytest src/llm/tests/ --cov=src/llm --cov-report=html
```

### Test Markers

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_api_key` - Tests requiring real API keys

## Performance Optimization

### Caching Strategy

The module implements intelligent caching:

1. **Request-level caching**: Identical requests are cached
2. **TTL-based expiration**: Default 7 days, configurable
3. **Cost optimization**: Reduces API calls by 60-80% in typical usage

### Async Batch Processing

Process multiple items concurrently:

```python
# Process 100 reports in parallel
reports = [...]  # 100 reports
summaries = await summarizer.batch_summarize(reports)
```

### Rate Limit Management

Automatic rate limiting prevents API throttling:

- Token bucket algorithm
- Exponential backoff on retries
- Configurable limits per provider

## Error Handling

### Automatic Retries

```python
# Automatically retries on failure
try:
    response = await gpt.complete_async(messages)
except Exception as e:
    # All retries exhausted
    print(f"Failed after {max_retries} attempts: {e}")
```

### Error Tracking

```python
# Errors are tracked in usage stats
stats = config.usage_stats["gpt-4-turbo-preview"]
print(f"Error rate: {stats.errors / stats.total_requests * 100:.1f}%")
```

## Best Practices

1. **Use async methods** for better performance
2. **Enable caching** to reduce costs
3. **Monitor usage** regularly to track spending
4. **Set appropriate rate limits** for your API tier
5. **Use appropriate models** - GPT-3.5 for simple tasks, GPT-4 for complex analysis
6. **Batch process** when analyzing multiple reports
7. **Handle errors gracefully** with try/except blocks

## Troubleshooting

### Common Issues

**Issue**: `ValueError: OpenAI API key not configured`
```python
# Solution: Set API key
config = LLMConfig()
config.set_api_key(LLMProvider.OPENAI, "your-key")
```

**Issue**: Rate limit errors
```python
# Solution: Configure rate limits
config.rate_limiters[LLMProvider.OPENAI] = RateLimiter(
    RateLimitConfig(requests_per_minute=30)
)
```

**Issue**: High costs
```python
# Solutions:
# 1. Enable caching
gpt = GPTIntegration(enable_cache=True)

# 2. Use cheaper models for simple tasks
gpt = GPTIntegration(model_type=ModelType.GPT_35_TURBO)

# 3. Reduce max_tokens
response = gpt.complete(messages, max_tokens=500)
```

## License

Part of PV Test Report Automation System - See main project LICENSE file.

## Support

For issues and questions, see the main project repository.
