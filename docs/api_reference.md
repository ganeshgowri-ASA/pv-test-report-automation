# API Reference

## Authentication

### POST /auth/login
Login to the system and obtain JWT token.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh
Refresh an expired token.

**Headers:**
- `Authorization: Bearer {token}`

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

## Sample Management

### POST /api/v1/samples
Create a new sample record.

**Request:**
```json
{
  "manufacturer": "string",
  "model_number": "string",
  "serial_number": "string",
  "technology_type": "mono-PERC",
  "rated_power": 550.0,
  "customer_id": "integer",
  "received_date": "2024-01-15"
}
```

**Response:**
```json
{
  "sample_id": "integer",
  "sample_code": "string",
  "status": "received",
  "created_at": "datetime"
}
```

### GET /api/v1/samples/{sample_id}
Get sample details.

**Response:**
```json
{
  "sample_id": 123,
  "sample_code": "PV2024-001",
  "manufacturer": "string",
  "model_number": "string",
  "status": "testing",
  "tests": []
}
```

### GET /api/v1/samples
List all samples with filtering.

**Query Parameters:**
- `status`: Filter by status
- `customer_id`: Filter by customer
- `date_from`: Start date
- `date_to`: End date
- `page`: Page number
- `limit`: Items per page

## Test Management

### POST /api/v1/tests
Create a new test.

**Request:**
```json
{
  "sample_id": "integer",
  "test_standard": "IEC 61215",
  "test_type": "MST10_thermal_cycling",
  "scheduled_date": "2024-01-20"
}
```

### PUT /api/v1/tests/{test_id}/results
Upload test results.

**Request:**
```json
{
  "test_id": "integer",
  "results": {
    "initial_power": 550.2,
    "final_power": 545.1,
    "degradation": 0.93,
    "pass": true
  },
  "files": ["file_ids"]
}
```

### GET /api/v1/tests/{test_id}
Get test details and results.

## Report Generation

### POST /api/v1/reports/generate
Generate a test report.

**Request:**
```json
{
  "sample_id": "integer",
  "report_type": "full",
  "template": "full_report_template",
  "include_images": true,
  "format": "pdf"
}
```

**Response:**
```json
{
  "report_id": "integer",
  "status": "generating",
  "estimated_completion": "datetime"
}
```

### GET /api/v1/reports/{report_id}
Get report status and download link.

**Response:**
```json
{
  "report_id": 456,
  "status": "completed",
  "download_url": "string",
  "generated_at": "datetime"
}
```

### GET /api/v1/reports/{report_id}/download
Download the generated report.

**Response:** Binary file (PDF, DOCX, etc.)

## Equipment Management

### GET /api/v1/equipment
List all equipment.

**Response:**
```json
{
  "equipment": [
    {
      "equipment_id": 1,
      "name": "Solar Simulator",
      "model": "XXX-1000",
      "calibration_due": "2024-06-15",
      "status": "active"
    }
  ]
}
```

### POST /api/v1/equipment/{equipment_id}/calibration
Record equipment calibration.

**Request:**
```json
{
  "calibration_date": "2024-01-15",
  "certificate_number": "CAL-2024-001",
  "next_due_date": "2024-07-15",
  "uncertainty": "±2%"
}
```

## Workflow Management

### POST /api/v1/workflow/submit-for-review
Submit test results for review.

**Request:**
```json
{
  "test_id": "integer",
  "reviewer_id": "integer",
  "notes": "string"
}
```

### PUT /api/v1/workflow/approve
Approve test results.

**Request:**
```json
{
  "test_id": "integer",
  "approval_notes": "string"
}
```

### PUT /api/v1/workflow/reject
Reject test results.

**Request:**
```json
{
  "test_id": "integer",
  "rejection_reason": "string",
  "required_actions": "string"
}
```

## LLM Analysis

### POST /api/v1/llm/analyze-compliance
Analyze test data for compliance.

**Request:**
```json
{
  "test_id": "integer",
  "standard": "IEC 61215",
  "provider": "anthropic"
}
```

**Response:**
```json
{
  "compliant": true,
  "findings": [],
  "confidence": 0.95
}
```

### POST /api/v1/llm/generate-summary
Generate executive summary.

**Request:**
```json
{
  "report_id": "integer",
  "length": "brief"
}
```

## File Upload

### POST /api/v1/files/upload
Upload files (images, documents, etc.).

**Request:** Multipart form data

**Response:**
```json
{
  "file_id": "integer",
  "filename": "string",
  "file_type": "string",
  "size": "integer",
  "upload_date": "datetime"
}
```

## Audit Logs

### GET /api/v1/audit/logs
Get audit logs.

**Query Parameters:**
- `user_id`: Filter by user
- `action`: Filter by action type
- `date_from`: Start date
- `date_to`: End date
- `entity_type`: Sample, Test, Report, etc.

**Response:**
```json
{
  "logs": [
    {
      "log_id": 1,
      "user": "string",
      "action": "create_test",
      "entity_type": "Test",
      "entity_id": 123,
      "timestamp": "datetime",
      "details": {}
    }
  ]
}
```

## Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

- Default: 100 requests per minute per user
- File uploads: 10 per minute
- LLM API calls: 60 per minute

Headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets
