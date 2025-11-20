# LLM Integration - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install openai google-generativeai
```

### 2. Set API Keys
```bash
export OPENAI_API_KEY="sk-your-key-here"
export GOOGLE_API_KEY="AIza-your-key-here"
```

### 3. Basic Usage

#### Analyze a Report
```python
from llm import GPTIntegration
import asyncio

async def analyze():
    gpt = GPTIntegration()

    report = {
        'module_id': 'PV-001',
        'test_results': {
            'power': 305,
            'efficiency': 18.5
        }
    }

    response = await gpt.analyze_report_async(report)
    print(response.content)
    print(f"Cost: ${response.cost:.4f}")

asyncio.run(analyze())
```

#### Check Compliance
```python
from llm import ComplianceChecker

async def check():
    checker = ComplianceChecker()

    report = {
        'module_id': 'PV-001',
        'test_results': {...}
    }

    result = await checker.check_compliance(report, "IEC 61215")
    print(f"Compliance: {result.compliance_rate}%")

asyncio.run(check())
```

#### Generate Summary
```python
from llm import ReportSummarizer, SummaryConfig, SummaryType

async def summarize():
    summarizer = ReportSummarizer()

    config = SummaryConfig(
        summary_type=SummaryType.EXECUTIVE,
        max_words=300
    )

    summary = await summarizer.generate_summary(report, config)
    summarizer.export_summary(summary, "output.md")

asyncio.run(summarize())
```

## Common Patterns

### Batch Processing
```python
reports = [report1, report2, report3]
responses = await gpt.batch_analyze(reports)
```

### Multi-Modal Analysis
```python
from llm import GeminiIntegration
from pathlib import Path

gemini = GeminiIntegration()
response = await gemini.analyze_chart(
    Path("chart.png"),
    context="Power degradation chart"
)
```

### Track Costs
```python
from llm import get_config

config = get_config()
summary = config.get_usage_summary()
print(f"Total spent: ${summary['total_cost']:.2f}")
```

## Best Practices

1. **Always use async** for better performance
2. **Enable caching** to reduce costs
3. **Monitor usage** with `get_usage_summary()`
4. **Use appropriate models** (GPT-3.5 for simple, GPT-4 for complex)
5. **Handle errors** with try/except

## Troubleshooting

**Problem**: API key error
```python
# Solution
from llm import LLMConfig, LLMProvider
config = LLMConfig()
config.set_api_key(LLMProvider.OPENAI, "your-key")
```

**Problem**: Rate limits
```python
# Solution: Lower rate limits
from llm import RateLimitConfig, RateLimiter
config.rate_limiters[LLMProvider.OPENAI] = RateLimiter(
    RateLimitConfig(requests_per_minute=30)
)
```

**Problem**: High costs
```python
# Solutions:
# 1. Enable caching (default)
# 2. Use GPT-3.5 Turbo for simple tasks
# 3. Set max_tokens limit
response = await gpt.complete_async(messages, max_tokens=500)
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the [tests/](tests/) directory for more examples
- Review cost optimization strategies
- Explore multi-language support

## Quick Reference

### Models
- `ModelType.GPT_4_TURBO` - Best quality, vision support
- `ModelType.GPT_35_TURBO` - Fast and cheap
- `ModelType.GEMINI_15_PRO` - Large context, multi-modal

### Summary Types
- `SummaryType.EXECUTIVE` - Business focused
- `SummaryType.TECHNICAL` - Engineering focused
- `SummaryType.REGULATORY` - Compliance focused

### Languages
- `Language.ENGLISH`, `Language.GERMAN`, `Language.SPANISH`
- `Language.FRENCH`, `Language.CHINESE`, `Language.JAPANESE`

### Formats
- `SummaryFormat.MARKDOWN` - Markdown
- `SummaryFormat.HTML` - HTML
- `SummaryFormat.JSON` - JSON

## Support

For detailed documentation, see [README.md](README.md)
