># Claude AI Integration for PV Test Report Automation

## Overview

This document describes the Claude AI integration for the PV Test Report Automation system. The integration provides intelligent analysis, compliance checking, and assistance capabilities for photovoltaic module testing.

## Architecture

### Core Components

1. **ClaudeClient** (`src/llm/claude_client.py`)
   - Base API client with authentication
   - Synchronous and asynchronous operations
   - Streaming response support
   - Token usage tracking
   - Automatic retry with exponential backoff
   - Rate limit handling

2. **ComplianceChecker** (`src/llm/compliance_checker.py`)
   - Validates test reports against IEC/ISO standards
   - Identifies missing mandatory sections
   - Checks data completeness
   - Verifies pass/fail criteria consistency
   - Generates compliance scores

3. **ReportSummarizer** (`src/llm/report_summarizer.py`)
   - Auto-generates executive summaries
   - Extracts key findings
   - Supports multiple languages
   - Customizable summary length and detail level
   - Identifies critical failures

4. **IntelligentAssistant** (`src/llm/intelligent_assistant.py`)
   - Answers questions about test procedures
   - Suggests test sequences based on module type
   - Provides standard interpretation guidance
   - Equipment calibration reminders
   - Troubleshooting assistance

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Claude API Configuration
CLAUDE_API_KEY=your-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.3

# Rate Limiting
CLAUDE_MAX_RETRIES=3
CLAUDE_RETRY_DELAY=2.0
CLAUDE_RATE_LIMIT_REQUESTS=50

# Cost Tracking
ENABLE_COST_TRACKING=true
COST_ALERT_THRESHOLD=100.0
```

### API Key Management

**Development:**
```bash
export CLAUDE_API_KEY="your-api-key"
```

**Production:**
- Use encrypted environment variables
- Consider secret management systems (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Never commit keys to version control

## Usage Examples

### 1. Claude Client Basic Usage

```python
from src.llm.claude_client import ClaudeClient

# Initialize client
client = ClaudeClient()

# Simple prompt
response = client.simple_prompt("What is the purpose of thermal cycling test in IEC 61215?")
print(response)

# Async usage
import asyncio

async def main():
    response = await client.simple_prompt_async("Explain damp heat test requirements")
    print(response)

asyncio.run(main())

# Check token usage
summary = client.get_usage_summary()
print(f"Total cost: ${summary['total_cost_usd']}")
```

### 2. Compliance Checking

```python
from src.llm.compliance_checker import ComplianceChecker
from src.models.test_report import TestReport

# Load test report
report = TestReport(...)

# Initialize checker
checker = ComplianceChecker()

# Check compliance
compliance_summary = checker.check_compliance(report)

print(f"Compliance Score: {compliance_summary.compliance_score}%")
print(f"Overall Status: {compliance_summary.overall_status}")
print(f"Critical Failures: {compliance_summary.critical_failures}")
print(f"Recommendations: {compliance_summary.recommendations}")

# Validate basic requirements (rule-based, no LLM)
validation = checker.validate_standard_requirements(report)
if not validation['valid']:
    print(f"Issues: {validation['issues']}")
```

### 3. Report Summarization

```python
from src.llm.report_summarizer import (
    ReportSummarizer,
    SummaryType,
    SummaryLength,
)

summarizer = ReportSummarizer()

# Generate executive summary
executive_summary = summarizer.generate_summary(
    report=report,
    summary_type=SummaryType.EXECUTIVE,
    length=SummaryLength.BRIEF,
    language="en",
    include_recommendations=True,
)

print(executive_summary)

# Generate in multiple languages
summaries = await summarizer.generate_multi_language_summaries(
    report=report,
    languages=["en", "es", "fr", "de"]
)

for lang, summary in summaries.items():
    print(f"\n=== {lang.upper()} ===\n{summary}")

# Extract key findings
findings = summarizer.extract_key_findings(report)
for i, finding in enumerate(findings, 1):
    print(f"{i}. {finding}")
```

### 4. Intelligent Assistant

```python
from src.llm.intelligent_assistant import (
    IntelligentAssistant,
    AssistantMode,
)
from src.models.test_report import ModuleType, StandardType

assistant = IntelligentAssistant()

# Ask a general question
answer = assistant.ask(
    "What are the key differences between IEC 61215 and IEC 61730?",
    mode=AssistantMode.GENERAL
)
print(answer)

# Get procedure guidance
procedure = assistant.get_procedure_guidance("Thermal Cycling Test")
print(procedure)

# Interpret standard clause
interpretation = assistant.interpret_standard_clause(
    standard=StandardType.IEC_61215,
    clause="10.9 (Thermal Cycling)"
)
print(interpretation)

# Suggest test sequence
sequence = assistant.suggest_test_sequence(
    module_type=ModuleType.CRYSTALLINE_SILICON,
    standard=StandardType.IEC_61215
)
print("Recommended test sequence:")
for i, test in enumerate(sequence, 1):
    print(f"{i}. {test}")

# Troubleshooting
help_text = assistant.troubleshoot(
    problem_description="Module failed damp heat test with 7% power degradation",
    test_context={
        "test": "Damp Heat",
        "module_type": "Crystalline Silicon",
        "measured": "7% degradation",
        "specification": "≤ 5% degradation"
    }
)
print(help_text)

# Check calibration status
from datetime import datetime, timedelta

calibration_status = assistant.get_calibration_reminder(
    equipment_type="solar_simulator",
    last_calibration_date=datetime.utcnow() - timedelta(days=350)
)
print(calibration_status)
```

## Token Usage & Cost Management

### Cost Estimation

Claude 3.5 Sonnet pricing (January 2024):
- Input: $3 per million tokens
- Output: $15 per million tokens

```python
# Track costs
client = ClaudeClient()

# After operations
summary = client.get_usage_summary()
print(f"""
Token Usage Summary:
- Total Calls: {summary['total_calls']}
- Input Tokens: {summary['total_input_tokens']}
- Output Tokens: {summary['total_output_tokens']}
- Total Cost: ${summary['total_cost_usd']}
- Avg Cost/Call: ${summary['average_cost_per_call']}
""")

# Check if cost threshold exceeded
if client.check_cost_threshold():
    print("⚠️ Cost threshold exceeded!")
```

### Cost Optimization Tips

1. **Use rule-based validation first**: Run `validate_standard_requirements()` before LLM analysis
2. **Cache common queries**: Store responses for frequently asked questions
3. **Batch operations**: Use `batch_check_compliance()` for multiple reports
4. **Optimize prompts**: Be concise and specific in prompts
5. **Set appropriate max_tokens**: Don't request more tokens than needed
6. **Use appropriate temperature**: Lower temperature (0.2-0.3) for consistent analytical tasks

## Audit Trail Integration

All LLM interactions are logged in the audit trail:

```python
from src.models.audit_trail import AuditEntry, AuditAction

# LLM interactions automatically create audit entries
audit_entry = AuditEntry(
    audit_id="AUD-2024-001",
    action=AuditAction.LLM_COMPLIANCE_CHECK,
    resource_type="TestReport",
    resource_id="RPT-2024-001",
    user_id="USR-123",
    status="SUCCESS",
    llm_usage={
        "model_name": "claude-3-5-sonnet-20241022",
        "input_tokens": 1500,
        "output_tokens": 800,
        "total_tokens": 2300,
        "estimated_cost": 0.023,
    },
    llm_prompt="...",  # If AUDIT_LOG_LLM_PROMPTS=true
    llm_response="...",  # If AUDIT_LOG_LLM_PROMPTS=true
)
```

## Error Handling

### Exception Hierarchy

```
PVReportException
├── APIException
│   └── ClaudeAPIException
│       ├── RateLimitException
│       ├── AuthenticationException
│       └── TokenLimitException
├── ComplianceCheckException
└── ReportGenerationException
```

### Handling Errors

```python
from src.utils.exceptions import (
    ClaudeAPIException,
    RateLimitException,
    AuthenticationException,
)

try:
    summary = checker.check_compliance(report)
except RateLimitException as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except AuthenticationException as e:
    print(f"Authentication failed: {e.message}")
except ClaudeAPIException as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")
    print(f"Request ID: {e.request_id}")
```

## Streaming Responses

For long-running analyses, use streaming:

```python
# Synchronous streaming
with client.create_message_stream(
    messages=[{"role": "user", "content": "Analyze this report..."}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)

# Async streaming
async def stream_analysis():
    async for event in client.create_message_stream_async(
        messages=[{"role": "user", "content": "Analyze..."}]
    ):
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run LLM tests only (requires API key)
pytest -m llm

# Run with coverage
pytest --cov=src/llm --cov-report=html
```

### Test Fixtures

```python
from tests.fixtures.sample_report import create_sample_report

# Use in tests
def test_compliance_checker():
    report = create_sample_report()
    checker = ComplianceChecker()
    result = checker.validate_standard_requirements(report)
    assert result['valid'] == True
```

## Security Best Practices

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables
   - Rotate keys regularly
   - Restrict key permissions

2. **Data Privacy**
   - Sanitize sensitive data before sending to LLM
   - Be aware of data retention policies
   - Consider data residency requirements

3. **Audit Logging**
   - Enable `AUDIT_LOG_LLM_PROMPTS` in development only
   - Review audit logs regularly
   - Implement access controls on logs

4. **Rate Limiting**
   - Configure appropriate rate limits
   - Implement circuit breakers
   - Monitor usage patterns

## Monitoring & Observability

### Logging

```python
from src.logging.logger import get_logger

logger = get_logger(__name__)

# LLM interactions are automatically logged
# Check logs at:
# - logs/app.log - Application logs
# - logs/llm.log - LLM-specific logs
# - logs/audit.log - Audit trail
```

### Metrics to Monitor

1. **Token Usage**: Track input/output tokens per operation
2. **Cost**: Monitor daily/monthly costs
3. **Response Time**: Average API response time
4. **Error Rate**: Failed requests / total requests
5. **Compliance Scores**: Track trends over time

## Performance Considerations

### Async Operations

Always use async for batch operations:

```python
import asyncio

async def process_reports(reports):
    checker = ComplianceChecker()
    summaries = await checker.batch_check_compliance(reports)
    return summaries

# Process 10 reports in parallel
reports = [...]
results = asyncio.run(process_reports(reports))
```

### Caching

Implement caching for repeated queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_procedure(test_name: str) -> str:
    assistant = IntelligentAssistant()
    return assistant.get_procedure_guidance(test_name)
```

## Support & Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API key is set correctly
   - Check key has not expired
   - Ensure key has necessary permissions

2. **Rate Limiting**
   - Reduce request frequency
   - Implement exponential backoff
   - Consider upgrading API tier

3. **Token Limit Exceeded**
   - Reduce input size
   - Split large reports
   - Increase max_tokens setting

4. **Unexpected Responses**
   - Check prompt clarity
   - Adjust temperature setting
   - Review system prompts

### Debug Mode

Enable debug logging:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Future Enhancements

- [ ] Response caching layer
- [ ] Fine-tuning for PV-specific tasks
- [ ] Batch processing optimization
- [ ] Real-time streaming dashboards
- [ ] Multi-model support (fallback to other LLMs)
- [ ] Prompt template management
- [ ] A/B testing framework for prompts

## References

- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [IEC 61215 Standard](https://webstore.iec.ch/publication/61215)
- [ISO 17025 Standard](https://www.iso.org/standard/66912.html)
