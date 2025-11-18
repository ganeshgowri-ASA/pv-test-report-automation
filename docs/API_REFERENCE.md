# LLM Integration API Reference

## Claude Client API

### `ClaudeClient`

**Initialize:**
```python
ClaudeClient(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None
)
```

**Methods:**

#### `create_message()`
```python
create_message(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs: Any
) -> Message
```
Create a synchronous message.

#### `create_message_async()`
```python
async create_message_async(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs: Any
) -> Message
```
Create an asynchronous message.

#### `simple_prompt()`
```python
simple_prompt(
    prompt: str,
    system: Optional[str] = None,
    **kwargs: Any
) -> str
```
Send a simple prompt and get text response.

#### `get_usage_summary()`
```python
get_usage_summary() -> Dict[str, Any]
```
Get token usage statistics.

Returns:
```python
{
    "total_calls": int,
    "total_input_tokens": int,
    "total_output_tokens": int,
    "total_tokens": int,
    "total_cost_usd": float,
    "average_tokens_per_call": float,
    "average_cost_per_call": float
}
```

---

## Compliance Checker API

### `ComplianceChecker`

**Initialize:**
```python
ComplianceChecker(claude_client: Optional[ClaudeClient] = None)
```

**Methods:**

#### `check_compliance()`
```python
check_compliance(
    report: TestReport,
    user_id: str = "system"
) -> ComplianceSummary
```
Check report compliance (synchronous).

#### `check_compliance_async()`
```python
async check_compliance_async(
    report: TestReport,
    user_id: str = "system"
) -> ComplianceSummary
```
Check report compliance (asynchronous).

#### `validate_standard_requirements()`
```python
validate_standard_requirements(
    report: TestReport
) -> Dict[str, Any]
```
Rule-based validation (no LLM).

Returns:
```python
{
    "valid": bool,
    "issues": List[str],
    "warnings": List[str],
    "missing_sections": List[str],
    "missing_parameters": List[str]
}
```

#### `batch_check_compliance()`
```python
async batch_check_compliance(
    reports: List[TestReport],
    user_id: str = "system"
) -> List[ComplianceSummary]
```
Check multiple reports in parallel.

---

## Report Summarizer API

### `ReportSummarizer`

**Initialize:**
```python
ReportSummarizer(claude_client: Optional[ClaudeClient] = None)
```

**Methods:**

#### `generate_summary()`
```python
generate_summary(
    report: TestReport,
    summary_type: SummaryType = SummaryType.EXECUTIVE,
    length: SummaryLength = SummaryLength.STANDARD,
    language: str = "en",
    include_recommendations: bool = True
) -> str
```
Generate report summary (synchronous).

**Parameters:**
- `summary_type`: EXECUTIVE, TECHNICAL, COMPLIANCE, FINDINGS, QUICK
- `length`: BRIEF, STANDARD, DETAILED
- `language`: ISO 639-1 code (en, es, fr, de, zh, ja, hi)

#### `generate_summary_async()`
```python
async generate_summary_async(
    report: TestReport,
    summary_type: SummaryType = SummaryType.EXECUTIVE,
    length: SummaryLength = SummaryLength.STANDARD,
    language: str = "en",
    include_recommendations: bool = True
) -> str
```
Generate report summary (asynchronous).

#### `extract_key_findings()`
```python
extract_key_findings(report: TestReport) -> List[str]
```
Extract key findings from report.

#### `generate_multi_language_summaries()`
```python
async generate_multi_language_summaries(
    report: TestReport,
    languages: List[str]
) -> Dict[str, str]
```
Generate summaries in multiple languages.

---

## Intelligent Assistant API

### `IntelligentAssistant`

**Initialize:**
```python
IntelligentAssistant(claude_client: Optional[ClaudeClient] = None)
```

**Methods:**

#### `ask()`
```python
ask(
    question: str,
    mode: AssistantMode = AssistantMode.GENERAL,
    context: Optional[Dict[str, Any]] = None,
    use_history: bool = True
) -> str
```
Ask the assistant a question (synchronous).

**Modes:**
- `PROCEDURE_HELP`: Test procedure guidance
- `STANDARD_INTERPRETATION`: Standard interpretation
- `TEST_PLANNING`: Test sequence planning
- `TROUBLESHOOTING`: Problem diagnosis
- `CALIBRATION`: Equipment calibration
- `QUALITY_ASSURANCE`: QA guidance
- `GENERAL`: General questions

#### `ask_async()`
```python
async ask_async(
    question: str,
    mode: AssistantMode = AssistantMode.GENERAL,
    context: Optional[Dict[str, Any]] = None,
    use_history: bool = True
) -> str
```
Ask the assistant a question (asynchronous).

#### `suggest_test_sequence()`
```python
suggest_test_sequence(
    module_type: ModuleType,
    standard: StandardType = StandardType.IEC_61215
) -> List[str]
```
Get recommended test sequence.

#### `get_procedure_guidance()`
```python
get_procedure_guidance(test_name: str) -> str
```
Get detailed test procedure guidance.

#### `interpret_standard_clause()`
```python
interpret_standard_clause(
    standard: StandardType,
    clause: str
) -> str
```
Interpret a specific standard clause.

#### `troubleshoot()`
```python
troubleshoot(
    problem_description: str,
    test_context: Optional[Dict[str, Any]] = None
) -> str
```
Get troubleshooting help.

#### `get_calibration_reminder()`
```python
get_calibration_reminder(
    equipment_type: str,
    last_calibration_date: datetime
) -> Dict[str, Any]
```
Check equipment calibration status.

Returns:
```python
{
    "equipment_type": str,
    "last_calibration": str,
    "calibration_interval_days": int,
    "days_since_calibration": int,
    "days_until_due": int,
    "status": str,  # OK, DUE_SOON, OVERDUE
    "recommendation": str
}
```

#### `clear_history()`
```python
clear_history() -> None
```
Clear conversation history.

---

## Data Models

### `ComplianceSummary`

```python
ComplianceSummary(
    overall_status: PassFailStatus,
    compliance_score: float,  # 0-100
    total_tests: int,
    tests_passed: int,
    tests_failed: int,
    critical_failures: List[str],
    warnings: List[str],
    missing_tests: List[str],
    recommendations: List[str],
    generated_at: datetime,
    generated_by_llm: bool
)
```

### `AuditEntry`

```python
AuditEntry(
    audit_id: str,
    timestamp: datetime,
    action: AuditAction,
    resource_type: ResourceType,
    resource_id: str,
    user_id: str,
    status: AuditStatus,
    llm_usage: Optional[LLMUsageMetrics],
    llm_prompt: Optional[str],
    llm_response: Optional[str],
    ...
)
```

### `LLMUsageMetrics`

```python
LLMUsageMetrics(
    model_name: str,
    operation_type: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    duration_seconds: float,
    estimated_cost: Optional[float],
    prompt_hash: Optional[str]
)
```

---

## Exceptions

### `ClaudeAPIException`

```python
ClaudeAPIException(
    message: str,
    status_code: Optional[int] = None,
    error_code: Optional[str] = None,
    tokens_used: Optional[Dict[str, int]] = None,
    request_id: Optional[str] = None
)
```

**Attributes:**
- `message`: Error message
- `status_code`: HTTP status code
- `error_code`: Error code
- `tokens_used`: Tokens used before error
- `request_id`: API request ID

### `RateLimitException`

```python
RateLimitException(
    message: str = "API rate limit exceeded",
    retry_after: Optional[int] = None
)
```

**Attributes:**
- `retry_after`: Seconds until retry allowed

### `TokenLimitException`

```python
TokenLimitException(
    message: str = "Token limit exceeded",
    token_count: Optional[int] = None,
    token_limit: Optional[int] = None
)
```

---

## Enums

### `SummaryType`
- `EXECUTIVE`: High-level summary for executives
- `TECHNICAL`: Detailed technical summary
- `COMPLIANCE`: Compliance-focused summary
- `FINDINGS`: Key findings and issues only
- `QUICK`: Brief overview

### `SummaryLength`
- `BRIEF`: 1-2 paragraphs (100-150 words)
- `STANDARD`: 3-5 paragraphs (250-400 words)
- `DETAILED`: Comprehensive (500-800 words)

### `AssistantMode`
- `PROCEDURE_HELP`: Test procedure guidance
- `STANDARD_INTERPRETATION`: Standard interpretation
- `TEST_PLANNING`: Test sequence planning
- `TROUBLESHOOTING`: Problem diagnosis
- `CALIBRATION`: Equipment calibration
- `QUALITY_ASSURANCE`: QA guidance
- `GENERAL`: General questions

---

## Configuration Settings

All settings can be configured via environment variables or `.env` file:

```python
# Claude API
CLAUDE_API_KEY: str
CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
CLAUDE_MAX_TOKENS: int = 4096
CLAUDE_TEMPERATURE: float = 0.3
CLAUDE_TIMEOUT: int = 120

# Rate Limiting
CLAUDE_MAX_RETRIES: int = 3
CLAUDE_RETRY_DELAY: float = 2.0
CLAUDE_RATE_LIMIT_REQUESTS: int = 50

# Cost Tracking
ENABLE_COST_TRACKING: bool = True
COST_ALERT_THRESHOLD: float = 100.0

# Audit
ENABLE_AUDIT_TRAIL: bool = True
AUDIT_LOG_LLM_PROMPTS: bool = True
```
