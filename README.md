# PV Test Report Automation with GPT Integration

World-class PV (Photovoltaic) test lab report automation system with **GPT-4 Turbo LLM integration** for intelligent analysis, compliance checking, and report generation.

## Overview

This system automates PV module testing workflows using OpenAI's GPT models to provide:

- **Intelligent Test Analysis**: AI-powered analysis of I-V curves and test results
- **Compliance Verification**: Automated checking against IEC/ISO standards (61215, 61730, 62804, 61853, ISO 9001)
- **Report Generation**: Multi-language executive summaries and detailed reports
- **Anomaly Detection**: Automatic identification of issues and data quality problems
- **Recommendation Engine**: AI-generated corrective actions and improvements
- **Cost Optimization**: Built-in caching, rate limiting, and cost tracking

## Features

### 🤖 GPT Integration Capabilities

| Feature | Description |
|---------|-------------|
| **Test Result Analysis** | Analyze I-V curves, detect patterns, assess performance |
| **Compliance Checking** | Verify against IEC 61215, 61730, 62804, 61853, ISO 9001 |
| **Report Summarization** | Generate executive summaries for stakeholders |
| **Anomaly Detection** | Identify outliers, inconsistencies, and data quality issues |
| **Recommendations** | Suggest corrective actions and improvements |
| **Multi-language** | Generate reports in English, Spanish, German, French, Chinese, Japanese |
| **Natural Language Queries** | Answer questions about test data conversationally |

### 🛠️ Technical Features

- **Error Handling**: Automatic retry with exponential backoff
- **Response Caching**: LRU cache with configurable TTL
- **Rate Limiting**: Request and token-based rate limiting
- **Cost Tracking**: Real-time cost monitoring with alerts
- **Token Management**: Automatic token estimation and optimization
- **Type Safety**: Full Pydantic models for requests/responses

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=your-api-key-here
```

## Quick Start

### Basic Usage

```python
from src.gpt_integration import GPTIntegration

# Initialize
gpt = GPTIntegration(api_key="your-api-key")

# Simple query
response = gpt.query("What are the key IEC 61215 requirements?")
print(response)
```

### Analyze I-V Curve

```python
from src.gpt_integration import GPTIntegration
from src.gpt_integration.analyzers import TestResultAnalyzer

gpt = GPTIntegration(api_key="your-api-key")
analyzer = TestResultAnalyzer(gpt)

iv_data = {
    "voltage_V": [0, 10, 20, 30, 40, 45, 48],
    "current_A": [9.2, 9.0, 8.5, 7.0, 3.0, 0.5, 0],
    "irradiance": 1000,
    "temperature": 25
}

result = analyzer.analyze_iv_curve(iv_data)
print(f"Summary: {result.summary}")
print(f"Data Quality: {result.data_quality_score:.2f}")
```

### Check Compliance

```python
from src.gpt_integration import GPTIntegration
from src.gpt_integration.analyzers import ComplianceChecker
from src.models.gpt_models import ComplianceStandard

gpt = GPTIntegration(api_key="your-api-key")
checker = ComplianceChecker(gpt)

result = checker.check_compliance(
    report="Test report content...",
    test_data={"thermal_cycling": "PASS", "damp_heat": "PASS"},
    standard=ComplianceStandard.IEC_61215
)

print(f"Status: {result.status.value}")
print(f"Confidence: {result.confidence_score:.2%}")
```

### Generate Report

```python
from src.gpt_integration import GPTIntegration
from src.gpt_integration.generators import ReportGenerator
from src.models.gpt_models import Language

gpt = GPTIntegration(api_key="your-api-key")
generator = ReportGenerator(gpt)

report = generator.generate_executive_summary(
    test_data={"pmax_W": 305, "efficiency_pct": 19.2},
    language=Language.ENGLISH
)

print(report.executive_summary)
```

### Detect Anomalies

```python
from src.gpt_integration import GPTIntegration
from src.gpt_integration.analyzers import AnomalyDetector

gpt = GPTIntegration(api_key="your-api-key")
detector = AnomalyDetector(gpt)

test_data = {
    "voltage_V": [48.5, 48.6, 35.0, 48.5],  # Outlier present
    "current_A": [9.2, 9.3, 9.1, 9.2]
}

anomalies = detector.detect_anomalies(test_data)
for anomaly in anomalies:
    print(f"{anomaly.type}: {anomaly.description}")
```

## Architecture

```
src/
├── gpt_integration/
│   ├── client.py           # Core GPT client with retry & caching
│   ├── analyzers.py        # Test analysis, compliance, anomalies
│   └── generators.py       # Reports and recommendations
├── models/
│   └── gpt_models.py       # Pydantic models
└── utils/
    ├── config.py           # Configuration management
    ├── cache.py            # Response caching
    ├── rate_limiter.py     # Rate limiting
    └── cost_tracker.py     # Cost tracking
```

## Use Cases

### 1. Test Result Analysis

Analyze I-V curves, detect performance patterns, and assess module quality:

```python
analyzer = TestResultAnalyzer(gpt)
result = analyzer.analyze_iv_curve(iv_data)
# Returns: summary, key findings, patterns, anomalies, quality score
```

### 2. Compliance Verification

Check compliance with international standards:

```python
checker = ComplianceChecker(gpt)
result = checker.check_compliance(report, test_data, ComplianceStandard.IEC_61215)
# Returns: status, requirements met/failed, recommendations, confidence
```

### 3. Report Generation

Generate professional reports in multiple languages:

```python
generator = ReportGenerator(gpt)
report = generator.generate_executive_summary(test_data, language=Language.SPANISH)
# Returns: executive summary, test overview, key metrics, recommendations
```

### 4. Anomaly Detection

Identify outliers, missing data, and inconsistencies:

```python
detector = AnomalyDetector(gpt)
anomalies = detector.detect_anomalies(test_data)
# Returns: list of anomalies with type, severity, location, suggested actions
```

### 5. Recommendation Engine

Get AI-powered recommendations for improvements:

```python
engine = RecommendationEngine(gpt)
recommendations = engine.generate_recommendations(test_data, analysis_results)
# Returns: prioritized list of actionable recommendations
```

### 6. Natural Language Queries

Ask questions about test data in plain language:

```python
query = NaturalLanguageQuery(
    query="What was the peak power output?",
    context=test_data
)
response = engine.answer_query(query)
# Returns: answer, relevant data, confidence, suggested visualizations
```

## Configuration

Configure via environment variables or `.env` file:

```bash
# OpenAI Settings
OPENAI_API_KEY=your-key
GPT_DEFAULT_MODEL=gpt-4-turbo
GPT_DEFAULT_TEMPERATURE=0.7
GPT_DEFAULT_MAX_TOKENS=2000

# Rate Limiting
RATE_LIMIT_RPM=60              # Requests per minute
RATE_LIMIT_TPM=90000           # Tokens per minute

# Caching
ENABLE_CACHE=True
CACHE_TTL=3600                 # 1 hour
CACHE_MAX_SIZE=1000

# Cost Tracking
ENABLE_COST_TRACKING=True
COST_ALERT_THRESHOLD=100.0     # Alert at $100

# Retry Logic
MAX_RETRIES=3
RETRY_DELAY=1.0
EXPONENTIAL_BACKOFF=True
```

## Performance & Cost Optimization

### Caching

Responses are automatically cached to reduce API calls and costs:

```python
# First call - hits API
response1 = gpt.query("What is fill factor?")  # Cost: $0.02

# Second call - hits cache
response2 = gpt.query("What is fill factor?")  # Cost: $0.00
```

### Rate Limiting

Automatic rate limiting prevents exceeding API limits:

```python
# Configure limits
config.rate_limit_requests_per_minute = 60
config.rate_limit_tokens_per_minute = 90000

# Automatically waits if limits would be exceeded
```

### Cost Tracking

Monitor costs in real-time:

```python
stats = gpt.get_stats()
print(f"Total Cost: ${stats['costs']['total_cost_usd']:.4f}")
print(f"Average per Request: ${stats['costs']['average_cost_per_request']:.4f}")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_gpt_integration.py
```

## Examples

See the `examples/` directory for comprehensive examples:

- `basic_usage.py` - Simple examples for all features
- `advanced_usage.py` - Advanced patterns and optimizations

Run examples:

```bash
# Make sure .env is configured
python examples/basic_usage.py
python examples/advanced_usage.py
```

## Supported Standards

| Standard | Description |
|----------|-------------|
| **IEC 61215** | Design qualification and type approval |
| **IEC 61730** | Module safety qualification |
| **IEC 62804** | Potential-induced degradation testing |
| **IEC 61853** | Performance testing and energy rating |
| **ISO 9001** | Quality management systems |

## Supported Languages

- 🇬🇧 English
- 🇪🇸 Spanish
- 🇩🇪 German
- 🇫🇷 French
- 🇨🇳 Chinese
- 🇯🇵 Japanese

## API Reference

### Core Classes

#### `GPTIntegration`
Main client for GPT interactions.

**Methods:**
- `query(prompt, system_message, model, temperature, max_tokens) -> str`
- `generate_completion(request, use_cache) -> GPTResponse`
- `get_stats() -> Dict`

#### `TestResultAnalyzer`
Analyze PV test results.

**Methods:**
- `analyze_iv_curve(iv_data) -> AnalysisResult`
- `analyze_test_results(test_data) -> AnalysisResult`

#### `ComplianceChecker`
Check compliance with standards.

**Methods:**
- `check_compliance(report, test_data, standard) -> ComplianceCheck`

#### `AnomalyDetector`
Detect anomalies in test data.

**Methods:**
- `detect_anomalies(test_data, context) -> List[Anomaly]`
- `check_data_quality(test_data) -> Dict`

#### `ReportGenerator`
Generate reports in multiple languages.

**Methods:**
- `generate_executive_summary(test_data, language) -> ReportSummary`
- `generate_detailed_report(test_data, language) -> str`
- `translate_report(report_text, source_lang, target_lang) -> str`

#### `RecommendationEngine`
Generate recommendations.

**Methods:**
- `generate_recommendations(test_data, analysis_results) -> List[str]`
- `suggest_corrective_actions(failures, context) -> Dict`
- `answer_query(query) -> QueryResponse`

## Pricing

Approximate costs using GPT-4 Turbo (as of 2024):

| Operation | Tokens | Cost |
|-----------|--------|------|
| I-V curve analysis | ~2,000 | $0.03 |
| Compliance check | ~2,500 | $0.04 |
| Report generation | ~3,000 | $0.05 |
| Anomaly detection | ~1,500 | $0.02 |

**Cost savings with caching:** 60-80% reduction on repeated queries

## Best Practices

1. **Use caching** for repeated queries
2. **Lower temperature** (0.2-0.3) for technical accuracy
3. **Batch similar requests** to optimize costs
4. **Monitor costs** with built-in tracking
5. **Handle errors** with automatic retry logic
6. **Validate responses** using Pydantic models

## Troubleshooting

### API Key Issues
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Or in Python
import os
print(os.getenv("OPENAI_API_KEY"))
```

### Rate Limiting
```python
# Check rate limiter stats
stats = gpt.get_stats()
print(stats['rate_limiter'])
```

### Cost Alerts
Configure cost alerts in `.env`:
```bash
COST_ALERT_THRESHOLD=100.0  # Alert at $100
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: See `examples/` directory
- **Issues**: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues
- **Email**: support@example.com

## Changelog

### Version 1.0.0 (2024-11-18)
- ✅ GPT-4 Turbo integration
- ✅ Test result analysis
- ✅ Compliance checking (IEC 61215, 61730, 62804, 61853)
- ✅ Anomaly detection
- ✅ Multi-language report generation
- ✅ Recommendation engine
- ✅ Response caching
- ✅ Rate limiting
- ✅ Cost tracking
- ✅ Comprehensive test suite
- ✅ Example usage scripts

## Acknowledgments

Built with:
- OpenAI GPT-4 Turbo
- Pydantic for data validation
- Tenacity for retry logic

---

**Phase 7 | Session 35 | GPT LLM Integration** ✓ Complete
