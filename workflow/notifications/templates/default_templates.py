"""
Default Notification Templates

Pre-defined templates for common notification scenarios in PV test lab.
"""

from typing import Dict
from ..models import NotificationTemplate, NotificationType, NotificationPriority, DeliveryChannel


def get_default_templates() -> Dict[str, NotificationTemplate]:
    """
    Get default notification templates

    Returns:
        Dictionary of template_id -> NotificationTemplate
    """
    templates = {}

    # Test Completion Template
    templates['test_complete'] = NotificationTemplate(
        template_id='test_complete',
        notification_type=NotificationType.TEST_COMPLETE,
        subject_template='Test Completed: {test_id}',
        message_template=(
            'Test {test_id} has been completed successfully.\n\n'
            'Module: {module_id}\n'
            'Test Type: {test_type}\n'
            'Duration: {duration}\n'
            'Status: {status}\n\n'
            'The test report is now available for review.'
        ),
        priority=NotificationPriority.MEDIUM,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.IN_APP],
        variables=['test_id', 'module_id', 'test_type', 'duration', 'status']
    )

    # Review Request Template
    templates['review_request'] = NotificationTemplate(
        template_id='review_request',
        notification_type=NotificationType.REVIEW_REQUEST,
        subject_template='Review Request: Report {report_id}',
        message_template=(
            'A test report requires your review.\n\n'
            'Report ID: {report_id}\n'
            'Test Type: {test_type}\n'
            'Module: {module_id}\n'
            'Submitted by: {submitted_by}\n'
            'Submitted on: {submitted_date}\n\n'
            'Please review the report at your earliest convenience.'
        ),
        priority=NotificationPriority.HIGH,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.SLACK, DeliveryChannel.IN_APP],
        variables=['report_id', 'test_type', 'module_id', 'submitted_by', 'submitted_date']
    )

    # Calibration Due Template
    templates['calibration_due'] = NotificationTemplate(
        template_id='calibration_due',
        notification_type=NotificationType.CALIBRATION_DUE,
        subject_template='Equipment Calibration Due: {equipment_id}',
        message_template=(
            'Equipment calibration is due soon.\n\n'
            'Equipment ID: {equipment_id}\n'
            'Equipment Name: {equipment_name}\n'
            'Last Calibration: {last_calibration_date}\n'
            'Due Date: {due_date}\n'
            'Days Remaining: {days_remaining}\n\n'
            'Please schedule calibration to maintain compliance.'
        ),
        priority=NotificationPriority.HIGH,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.IN_APP],
        variables=['equipment_id', 'equipment_name', 'last_calibration_date', 'due_date', 'days_remaining']
    )

    # Test Failure Template
    templates['test_failure'] = NotificationTemplate(
        template_id='test_failure',
        notification_type=NotificationType.TEST_FAILURE,
        subject_template='ALERT: Test Failed - {test_id}',
        message_template=(
            'Test {test_id} has failed.\n\n'
            'Module: {module_id}\n'
            'Test Type: {test_type}\n'
            'Failure Reason: {failure_reason}\n'
            'Timestamp: {timestamp}\n\n'
            'Immediate attention required.'
        ),
        priority=NotificationPriority.CRITICAL,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.SMS, DeliveryChannel.SLACK],
        variables=['test_id', 'module_id', 'test_type', 'failure_reason', 'timestamp']
    )

    # System Error Template
    templates['system_error'] = NotificationTemplate(
        template_id='system_error',
        notification_type=NotificationType.SYSTEM_ERROR,
        subject_template='SYSTEM ERROR: {error_type}',
        message_template=(
            'A system error has occurred.\n\n'
            'Error Type: {error_type}\n'
            'Error Message: {error_message}\n'
            'Component: {component}\n'
            'Timestamp: {timestamp}\n\n'
            'System administrators have been notified.'
        ),
        priority=NotificationPriority.CRITICAL,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.SMS, DeliveryChannel.SLACK],
        variables=['error_type', 'error_message', 'component', 'timestamp']
    )

    # System Warning Template
    templates['system_warning'] = NotificationTemplate(
        template_id='system_warning',
        notification_type=NotificationType.SYSTEM_WARNING,
        subject_template='System Warning: {warning_type}',
        message_template=(
            'A system warning has been triggered.\n\n'
            'Warning Type: {warning_type}\n'
            'Message: {warning_message}\n'
            'Component: {component}\n'
            'Timestamp: {timestamp}\n\n'
            'Please investigate when possible.'
        ),
        priority=NotificationPriority.MEDIUM,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.IN_APP],
        variables=['warning_type', 'warning_message', 'component', 'timestamp']
    )

    # Approval Request Template
    templates['approval_request'] = NotificationTemplate(
        template_id='approval_request',
        notification_type=NotificationType.APPROVAL_REQUEST,
        subject_template='Approval Required: {item_type} {item_id}',
        message_template=(
            'Your approval is required.\n\n'
            'Item Type: {item_type}\n'
            'Item ID: {item_id}\n'
            'Requested by: {requested_by}\n'
            'Request Date: {request_date}\n'
            'Description: {description}\n\n'
            'Please review and approve/reject.'
        ),
        priority=NotificationPriority.HIGH,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.IN_APP],
        variables=['item_type', 'item_id', 'requested_by', 'request_date', 'description']
    )

    # Equipment Issue Template
    templates['equipment_issue'] = NotificationTemplate(
        template_id='equipment_issue',
        notification_type=NotificationType.EQUIPMENT_ISSUE,
        subject_template='Equipment Issue: {equipment_id}',
        message_template=(
            'An issue has been detected with equipment.\n\n'
            'Equipment ID: {equipment_id}\n'
            'Equipment Name: {equipment_name}\n'
            'Issue Type: {issue_type}\n'
            'Description: {description}\n'
            'Reported by: {reported_by}\n'
            'Timestamp: {timestamp}\n\n'
            'Please investigate and resolve.'
        ),
        priority=NotificationPriority.HIGH,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.SLACK],
        variables=['equipment_id', 'equipment_name', 'issue_type', 'description', 'reported_by', 'timestamp']
    )

    # Compliance Alert Template
    templates['compliance_alert'] = NotificationTemplate(
        template_id='compliance_alert',
        notification_type=NotificationType.COMPLIANCE_ALERT,
        subject_template='COMPLIANCE ALERT: {compliance_type}',
        message_template=(
            'A compliance issue requires attention.\n\n'
            'Compliance Type: {compliance_type}\n'
            'Standard: {standard}\n'
            'Issue: {issue}\n'
            'Severity: {severity}\n'
            'Required Action: {required_action}\n'
            'Deadline: {deadline}\n\n'
            'Immediate action required to maintain compliance.'
        ),
        priority=NotificationPriority.CRITICAL,
        default_channels=[DeliveryChannel.EMAIL, DeliveryChannel.SMS, DeliveryChannel.TEAMS],
        variables=['compliance_type', 'standard', 'issue', 'severity', 'required_action', 'deadline']
    )

    return templates
