"""
Example Usage of PV Test Report Review Workflow System

This script demonstrates how to use the review workflow system programmatically.
"""

from datetime import datetime, timedelta
from src.workflow import (
    ReviewEngine, ReviewLevel, ReviewerRole, Reviewer,
    CommentSystem, CommentCategory,
    NotificationSystem, NotificationPreferences, NotificationType
)


def demo_review_workflow():
    """Demonstrate complete review workflow"""
    print("=" * 80)
    print("PV Test Report Review Workflow - Demo")
    print("=" * 80)

    # 1. Initialize systems
    print("\n1. Initializing systems...")
    review_engine = ReviewEngine(data_dir="data/reviews")
    comment_system = CommentSystem(data_dir="data/comments")
    notification_system = NotificationSystem(data_dir="data/notifications")
    print("✓ Systems initialized")

    # 2. Register reviewers
    print("\n2. Registering reviewers...")
    reviewers = [
        Reviewer(
            user_id="tech1",
            name="John Technician",
            email="john.tech@pvlab.com",
            role=ReviewerRole.TECHNICIAN,
            specializations=["PV Testing", "Performance Analysis"],
            max_concurrent_reviews=5
        ),
        Reviewer(
            user_id="tech2",
            name="Jane Expert",
            email="jane.expert@pvlab.com",
            role=ReviewerRole.TECHNICIAN,
            specializations=["PV Testing", "Thermal Analysis"]
        ),
        Reviewer(
            user_id="super1",
            name="Sarah Supervisor",
            email="sarah.super@pvlab.com",
            role=ReviewerRole.SUPERVISOR,
            specializations=["PV Testing", "Quality Control"]
        ),
        Reviewer(
            user_id="qa1",
            name="Mike Quality",
            email="mike.qa@pvlab.com",
            role=ReviewerRole.QUALITY_MANAGER,
            specializations=["ISO 17025", "Quality Assurance"]
        ),
        Reviewer(
            user_id="dir1",
            name="David Director",
            email="david.dir@pvlab.com",
            role=ReviewerRole.TECHNICAL_DIRECTOR,
            specializations=["All"]
        )
    ]

    for reviewer in reviewers:
        review_engine.register_reviewer(reviewer)
        print(f"  ✓ Registered: {reviewer.name} ({reviewer.role.value})")

    # 3. Create report version
    print("\n3. Creating report version...")
    report_id = "RPT-2024-001"
    version = review_engine.create_report_version(
        report_id=report_id,
        file_path="reports/sample_report_v1.pdf",
        created_by="tech1",
        changes_summary="Initial PV module testing report - IEC 61215",
        metadata={
            'test_type': 'PV Module Testing',
            'standard': 'IEC 61215-1:2021',
            'customer': 'Solar Corp',
            'module_type': 'Monocrystalline'
        }
    )
    print(f"  ✓ Created version: {version.version_id} (v{version.version_number})")

    # 4. Initiate review workflow
    print("\n4. Initiating multi-level review workflow...")
    assignments = review_engine.initiate_review_workflow(
        report_id=report_id,
        version_id=version.version_id,
        test_type="PV Testing",
        technician_id="tech1",
        initiated_by="super1"
    )
    print(f"  ✓ Created {len(assignments)} review assignments:")
    for assignment in assignments:
        print(f"    - {assignment.review_level.value}: {assignment.reviewer.name}")
        print(f"      Due: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}")

    # 5. Add comments
    print("\n5. Adding review comments...")

    # Critical comment
    comment1 = comment_system.create_comment(
        report_id=report_id,
        version_id=version.version_id,
        author_id="tech2",
        author_name="Jane Expert",
        content="The Voc measurement in Table 3 shows 45.2V, but the raw data indicates 45.8V. Please verify which is correct @john.tech",
        category=CommentCategory.CRITICAL,
        section="test_results",
        line_number=156
    )
    print(f"  ✓ Added CRITICAL comment: {comment1.comment_id}")

    # Suggestion comment
    comment2 = comment_system.create_comment(
        report_id=report_id,
        version_id=version.version_id,
        author_id="super1",
        author_name="Sarah Supervisor",
        content="Consider adding a graph showing the temperature coefficient trend for better visualization",
        category=CommentCategory.SUGGESTION,
        section="data_analysis"
    )
    print(f"  ✓ Added SUGGESTION comment: {comment2.comment_id}")

    # Clarification comment
    comment3 = comment_system.create_comment(
        report_id=report_id,
        version_id=version.version_id,
        author_id="qa1",
        author_name="Mike Quality",
        content="Which version of IEC 61215 was used for testing? The report should explicitly state IEC 61215-1:2021",
        category=CommentCategory.CLARIFICATION,
        section="methodology"
    )
    print(f"  ✓ Added CLARIFICATION comment: {comment3.comment_id}")

    # 6. Reply to comment
    print("\n6. Replying to comments...")
    reply1 = comment_system.reply_to_comment(
        parent_comment_id=comment1.comment_id,
        author_id="tech1",
        author_name="John Technician",
        content="Thank you for catching that! The correct value is 45.8V from the raw data. I will update Table 3."
    )
    print(f"  ✓ Added reply: {reply1.comment_id}")

    # 7. Resolve comment
    print("\n7. Resolving comments...")
    comment_system.resolve_comment(
        comment_id=comment3.comment_id,
        resolved_by="tech1",
        resolution_note="Updated to explicitly state IEC 61215-1:2021 in methodology section"
    )
    print(f"  ✓ Resolved comment: {comment3.comment_id}")

    # 8. Create new version with fixes
    print("\n8. Creating updated version...")
    version2 = review_engine.create_report_version(
        report_id=report_id,
        file_path="reports/sample_report_v2.pdf",
        created_by="tech1",
        changes_summary="Fixed Voc value in Table 3, added IEC standard version, improved graphs",
        metadata={
            'test_type': 'PV Module Testing',
            'standard': 'IEC 61215-1:2021',
            'customer': 'Solar Corp',
            'module_type': 'Monocrystalline',
            'revision': 'Addressed technical review comments'
        }
    )
    print(f"  ✓ Created version: {version2.version_id} (v{version2.version_number})")

    # 9. Update review status
    print("\n9. Updating review status...")
    if assignments:
        technical_assignment = assignments[0]
        review_engine.update_review_status(
            assignment_id=technical_assignment.assignment_id,
            new_status=review_engine.ReviewStatus.APPROVED,
            updated_by="tech2",
            decision="Approved after addressing critical comments"
        )
        print(f"  ✓ Technical review approved by {technical_assignment.reviewer.name}")

    # 10. Get review status
    print("\n10. Getting overall review status...")
    status = review_engine.get_report_review_status(report_id)
    print(f"  Report ID: {status['report_id']}")
    print(f"  Overall Status: {status['overall_status']}")
    print(f"  Total Assignments: {len(status['assignments'])}")
    print(f"  Version History: {len(status['version_history'])} versions")

    # 11. Get comment statistics
    print("\n11. Comment statistics...")
    stats = comment_system.get_comment_statistics(report_id)
    print(f"  Total Comments: {stats['total_comments']}")
    print(f"  Critical Unresolved: {stats['critical_unresolved']}")
    print(f"  Total Threads: {stats['total_threads']}")
    print("  By Category:")
    for category, count in stats['by_category'].items():
        if count > 0:
            print(f"    - {category}: {count}")

    # 12. Get overdue reviews
    print("\n12. Checking for overdue reviews...")
    overdue = review_engine.get_overdue_reviews()
    if overdue:
        print(f"  ⚠ {len(overdue)} overdue reviews found")
        for assignment in overdue:
            print(f"    - {assignment.report_id} ({assignment.reviewer.name})")
    else:
        print("  ✓ No overdue reviews")

    # 13. Export audit report
    print("\n13. Exporting audit report...")
    audit_file = f"audit_report_{report_id}.json"
    review_engine.export_audit_report(report_id, audit_file)
    print(f"  ✓ Exported to: {audit_file}")

    # 14. Export comments
    print("\n14. Exporting comments...")
    comments_file = f"comments_{report_id}.json"
    comment_system.export_comments(report_id, comments_file)
    print(f"  ✓ Exported to: {comments_file}")

    # 15. Notification setup (demo - no actual emails sent)
    print("\n15. Setting up notifications...")
    prefs = NotificationPreferences(
        user_id="tech1",
        email="john.tech@pvlab.com",
        immediate_notifications=[
            NotificationType.REVIEW_ASSIGNED,
            NotificationType.MENTION,
            NotificationType.REVIEW_OVERDUE
        ],
        quiet_hours_start=22,
        quiet_hours_end=8
    )
    notification_system.set_user_preferences(prefs)
    print(f"  ✓ Configured notifications for: {prefs.email}")

    # 16. Get audit trail
    print("\n16. Audit trail...")
    audit_trail = review_engine.get_audit_trail(report_id)
    print(f"  Total audit entries: {len(audit_trail)}")
    print("  Recent actions:")
    for entry in audit_trail[:5]:
        print(f"    - {entry.action} by {entry.performed_by} at {entry.performed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)

    print("\n📊 Summary:")
    print(f"  Reports: 1")
    print(f"  Versions: {len(review_engine.get_version_history(report_id))}")
    print(f"  Reviewers: {len(review_engine.reviewers)}")
    print(f"  Review Assignments: {len(assignments)}")
    print(f"  Comments: {stats['total_comments']}")
    print(f"  Audit Trail Entries: {len(audit_trail)}")

    print("\n💡 Next Steps:")
    print("  1. Launch Streamlit UI: streamlit run src/workflow/review_ui.py")
    print("  2. View audit reports in JSON files")
    print("  3. Configure SMTP for email notifications")
    print("  4. Add more reviewers and reports")


if __name__ == "__main__":
    demo_review_workflow()
