# pv-test-report-automation
World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Approval Workflow Engine

Multi-level approval workflow engine for ISO 17025 compliance with digital signatures, immutable audit trail, and auto-escalation.

### Features

✅ **Multi-Level Approval Hierarchy**
- Technician: Data entry and initial verification
- Reviewer: Technical review and validation
- Approver: Final authorization
- Management: NABL report sign-off

✅ **Digital Signatures**
- Cryptographic signing with SHA256/SHA512
- Timestamp verification
- IP address tracking
- Certificate ID support

✅ **Immutable Audit Trail**
- Complete action history
- Tamper-proof logging
- ISO 17025 compliance
- Export capabilities (JSON/CSV)

✅ **Auto-Escalation**
- Configurable timeout rules
- Email notifications
- Escalation warnings
- Statistics tracking

✅ **Section Locking**
- Lock report sections post-approval
- Role-based unlock requirements
- Audit trail integration

✅ **Flexible Routing**
- Sequential approval flow
- Parallel approval support
- Hybrid routing options

✅ **Delegation Support**
- Authority delegation
- Delegated approver tracking
- Permission management

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from workflow.approval import ApprovalWorkflowEngine
from models.approval_models import Approver, ApprovalStage

# Initialize engine
engine = ApprovalWorkflowEngine()

# Define approvers
approvers = [
    Approver(
        user_id=100,
        name="John Tech",
        email="john@example.com",
        role=ApprovalStage.TECHNICIAN,
        authority_level=1
    ),
    Approver(
        user_id=200,
        name="Jane Reviewer",
        email="jane@example.com",
        role=ApprovalStage.REVIEWER,
        authority_level=2
    ),
]

# Create workflow
workflow = engine.create_workflow(
    workflow_id=123,
    report_id=456,
    approvers=approvers
)

# Approve stage
result = engine.approve(
    workflow_id=123,
    user_id=100,
    comments="Data entry completed and verified",
    sections_to_lock=["test_data", "measurements"]
)

print(f"Status: {workflow.status.value}")
print(f"Current Stage: {workflow.current_stage.value}")
print(f"Signature: {result.digital_signature.signature_hash}")
```

## Architecture

```
pv-test-report-automation/
├── models/
│   ├── __init__.py
│   └── approval_models.py       # Data models (Pydantic)
├── workflow/
│   ├── __init__.py
│   ├── approval.py              # Core workflow engine
│   └── escalation.py            # Escalation manager
├── utils/
│   ├── __init__.py
│   ├── signature_utils.py       # Digital signatures
│   └── audit_utils.py           # Audit trail logging
├── tests/
│   ├── __init__.py
│   └── test_approval_workflow.py
├── example_usage.py
└── requirements.txt
```

## Example Usage

See `example_usage.py` for complete demonstration:

```bash
python example_usage.py
```

## Testing

Run comprehensive test suite:

```bash
pytest tests/ -v
pytest tests/ --cov=workflow --cov=models --cov=utils
```

## ISO 17025 Compliance

This approval workflow engine meets ISO 17025 requirements:

- ✅ Multi-level approval hierarchy
- ✅ Digital signatures for non-repudiation
- ✅ Immutable audit trail
- ✅ Timestamp verification
- ✅ Role-based access control
- ✅ Section locking for data integrity
- ✅ Escalation and notification
- ✅ Delegation with tracking
