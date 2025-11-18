"""
Review UI - Streamlit Dashboard for Report Review Workflow

Features:
- Review dashboard showing assigned reports
- Side-by-side comparison (previous vs current version)
- Highlight changes from last version
- Comment panel with filters
- Bulk approve/reject actions
- Export review summary
- ISO 17025 compliant interface
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import difflib
import json
from pathlib import Path

from review_engine import (
    ReviewEngine, ReviewStatus, ReviewLevel, ReviewerRole,
    Reviewer, ReviewAssignment
)
from comment_system import (
    CommentSystem, Comment, CommentCategory, CommentStatus,
    CommentThread
)
from notifications import NotificationSystem, NotificationType


class ReviewUI:
    """Streamlit UI for review workflow"""

    def __init__(self):
        self.review_engine = ReviewEngine()
        self.comment_system = CommentSystem()
        self.notification_system = NotificationSystem()

        # Initialize session state
        if 'current_user_id' not in st.session_state:
            st.session_state.current_user_id = None
        if 'current_user_name' not in st.session_state:
            st.session_state.current_user_name = None
        if 'selected_report' not in st.session_state:
            st.session_state.selected_report = None

    def run(self):
        """Main entry point for Streamlit app"""
        st.set_page_config(
            page_title="PV Test Report Review System",
            page_icon="📋",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Sidebar for navigation and user selection
        with st.sidebar:
            st.title("🔬 PV Test Review")
            st.markdown("---")

            # User selection (in production, use real authentication)
            self._render_user_selection()

            if st.session_state.current_user_id:
                st.markdown("---")
                page = st.radio(
                    "Navigation",
                    ["📋 My Reviews", "💬 Comments", "📊 Dashboard", "⚙️ Admin"]
                )
            else:
                page = None

        # Main content area
        if not st.session_state.current_user_id:
            self._render_login_prompt()
        elif page == "📋 My Reviews":
            self._render_my_reviews()
        elif page == "💬 Comments":
            self._render_comments_view()
        elif page == "📊 Dashboard":
            self._render_dashboard()
        elif page == "⚙️ Admin":
            self._render_admin()

    def _render_user_selection(self):
        """Render user selection (mock login)"""
        st.subheader("User Login")

        # Get available reviewers
        reviewers = list(self.review_engine.reviewers.values())

        if not reviewers:
            st.warning("No reviewers registered. Please add reviewers via Admin panel.")
            # Quick add demo users
            if st.button("Add Demo Users"):
                self._create_demo_users()
                st.rerun()
            return

        reviewer_options = {f"{r.name} ({r.role.value})": r for r in reviewers}
        selected = st.selectbox("Select User", [""] + list(reviewer_options.keys()))

        if selected:
            reviewer = reviewer_options[selected]
            st.session_state.current_user_id = reviewer.user_id
            st.session_state.current_user_name = reviewer.name
            st.success(f"Logged in as {reviewer.name}")

        if st.button("Logout") and st.session_state.current_user_id:
            st.session_state.current_user_id = None
            st.session_state.current_user_name = None
            st.rerun()

    def _render_login_prompt(self):
        """Render login prompt"""
        st.title("PV Test Report Review System")
        st.markdown("---")
        st.info("👈 Please select a user from the sidebar to continue")

        st.markdown("""
        ### Features
        - 📋 Review assigned reports with comprehensive workflow
        - 💬 Inline comments with threading and mentions
        - 📊 Track review progress and statistics
        - 🔔 Email notifications and reminders
        - ✅ ISO 17025 compliant audit trail
        - 📈 Version control and change tracking
        """)

    def _render_my_reviews(self):
        """Render my reviews page"""
        st.title("📋 My Reviews")

        current_user = st.session_state.current_user_id

        # Get pending reviews
        pending_reviews = self.review_engine.get_pending_reviews(current_user)

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["Pending", "Completed", "All"])

        with tab1:
            self._render_pending_reviews(pending_reviews)

        with tab2:
            completed = [
                a for a in self.review_engine.assignments.values()
                if a.reviewer.user_id == current_user
                and a.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]
            ]
            self._render_completed_reviews(completed)

        with tab3:
            all_reviews = [
                a for a in self.review_engine.assignments.values()
                if a.reviewer.user_id == current_user
            ]
            self._render_all_reviews(all_reviews)

    def _render_pending_reviews(self, assignments: List[ReviewAssignment]):
        """Render pending reviews"""
        st.subheader("Pending Reviews")

        if not assignments:
            st.info("No pending reviews")
            return

        # Display as table
        data = []
        for a in assignments:
            time_remaining = a.due_date - datetime.now()
            hours_remaining = int(time_remaining.total_seconds() / 3600)

            data.append({
                'Report ID': a.report_id,
                'Level': a.review_level.value,
                'Assigned': a.assigned_at.strftime("%Y-%m-%d %H:%M"),
                'Due': a.due_date.strftime("%Y-%m-%d %H:%M"),
                'Hours Remaining': hours_remaining,
                'Status': a.status.value,
                'Assignment ID': a.assignment_id
            })

        df = pd.DataFrame(data)

        # Color code by urgency
        def highlight_urgency(row):
            if row['Hours Remaining'] < 0:
                return ['background-color: #ffcccc'] * len(row)
            elif row['Hours Remaining'] < 24:
                return ['background-color: #fff3cd'] * len(row)
            else:
                return [''] * len(row)

        st.dataframe(
            df.style.apply(highlight_urgency, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # Select review to work on
        st.markdown("---")
        selected_assignment = st.selectbox(
            "Select review to work on",
            [a.assignment_id for a in assignments],
            format_func=lambda x: f"{[a for a in assignments if a.assignment_id == x][0].report_id}"
        )

        if selected_assignment:
            assignment = [a for a in assignments if a.assignment_id == selected_assignment][0]
            self._render_review_detail(assignment)

    def _render_review_detail(self, assignment: ReviewAssignment):
        """Render detailed review interface"""
        st.markdown("---")
        st.subheader(f"Review: {assignment.report_id}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Review Details")
            st.markdown(f"**Level:** {assignment.review_level.value}")
            st.markdown(f"**Status:** {assignment.status.value}")
            st.markdown(f"**Due:** {assignment.due_date.strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Notes:** {assignment.notes}")

        with col2:
            st.markdown("### Quick Actions")

            # Update status
            new_status = st.selectbox(
                "Update Status",
                [s.value for s in ReviewStatus],
                index=[s.value for s in ReviewStatus].index(assignment.status.value)
            )

            if st.button("Update Status"):
                self.review_engine.update_review_status(
                    assignment.assignment_id,
                    ReviewStatus(new_status),
                    st.session_state.current_user_id
                )
                st.success("Status updated!")
                st.rerun()

        # Version comparison
        st.markdown("---")
        self._render_version_comparison(assignment.report_id)

        # Comments section
        st.markdown("---")
        self._render_comments_section(assignment.report_id, assignment.version_id)

        # Review actions
        st.markdown("---")
        self._render_review_actions(assignment)

    def _render_version_comparison(self, report_id: str):
        """Render side-by-side version comparison"""
        st.subheader("📑 Version History & Comparison")

        versions = self.review_engine.get_version_history(report_id)

        if len(versions) < 1:
            st.info("No versions available")
            return

        col1, col2 = st.columns(2)

        with col1:
            version1_idx = st.selectbox(
                "Previous Version",
                range(len(versions)),
                format_func=lambda x: f"v{versions[x].version_number} - {versions[x].created_at.strftime('%Y-%m-%d')}"
            )

        with col2:
            version2_idx = st.selectbox(
                "Current Version",
                range(len(versions)),
                index=len(versions) - 1,
                format_func=lambda x: f"v{versions[x].version_number} - {versions[x].created_at.strftime('%Y-%m-%d')}"
            )

        if version1_idx != version2_idx:
            v1 = versions[version1_idx]
            v2 = versions[version2_idx]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### Version {v1.version_number}")
                st.markdown(f"**Created:** {v1.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**By:** {v1.created_by}")
                st.markdown(f"**Changes:** {v1.changes_summary}")
                st.markdown(f"**Hash:** `{v1.file_hash[:12]}...`")

            with col2:
                st.markdown(f"### Version {v2.version_number}")
                st.markdown(f"**Created:** {v2.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**By:** {v2.created_by}")
                st.markdown(f"**Changes:** {v2.changes_summary}")
                st.markdown(f"**Hash:** `{v2.file_hash[:12]}...`")

            # Show diff (if files exist)
            if Path(v1.file_path).exists() and Path(v2.file_path).exists():
                with st.expander("📊 View Changes"):
                    self._render_diff(v1.file_path, v2.file_path)

    def _render_diff(self, file1: str, file2: str):
        """Render diff between two files"""
        try:
            with open(file1, 'r') as f:
                lines1 = f.readlines()
            with open(file2, 'r') as f:
                lines2 = f.readlines()

            diff = difflib.unified_diff(
                lines1, lines2,
                fromfile='Previous', tofile='Current',
                lineterm=''
            )

            diff_text = '\n'.join(diff)
            st.code(diff_text, language='diff')

        except Exception as e:
            st.error(f"Error loading files: {e}")

    def _render_comments_section(self, report_id: str, version_id: str):
        """Render comments section"""
        st.subheader("💬 Comments")

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            category_filter = st.selectbox(
                "Category",
                ["All"] + [c.value for c in CommentCategory]
            )

        with col2:
            status_filter = st.selectbox(
                "Status",
                ["All"] + [s.value for s in CommentStatus]
            )

        with col3:
            section_filter = st.text_input("Section", "")

        # Get comments
        comments = self.comment_system.get_report_comments(
            report_id,
            version_id=version_id,
            category=CommentCategory(category_filter) if category_filter != "All" else None,
            status=CommentStatus(status_filter) if status_filter != "All" else None,
            section=section_filter if section_filter else None
        )

        # Display comment statistics
        stats = self.comment_system.get_comment_statistics(report_id)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Comments", stats['total_comments'])
        col2.metric("Critical Unresolved", stats['critical_unresolved'])
        col3.metric("Threads", stats['total_threads'])
        col4.metric("Attachments", stats['total_attachments'])

        # Add new comment
        with st.expander("➕ Add New Comment"):
            self._render_add_comment_form(report_id, version_id)

        # Display comments
        st.markdown("---")
        for comment in comments:
            self._render_comment(comment)

    def _render_add_comment_form(self, report_id: str, version_id: str):
        """Render form to add new comment"""
        category = st.selectbox(
            "Category",
            [c.value for c in CommentCategory]
        )

        section = st.text_input("Section", placeholder="e.g., test_results, page_3")

        content = st.text_area(
            "Comment",
            placeholder="Use @username to mention reviewers"
        )

        line_number = st.number_input("Line Number (optional)", min_value=0, value=0)

        if st.button("Add Comment"):
            if content and section:
                self.comment_system.create_comment(
                    report_id=report_id,
                    version_id=version_id,
                    author_id=st.session_state.current_user_id,
                    author_name=st.session_state.current_user_name,
                    content=content,
                    category=CommentCategory(category),
                    section=section,
                    line_number=line_number if line_number > 0 else None
                )
                st.success("Comment added!")
                st.rerun()
            else:
                st.error("Please fill in content and section")

    def _render_comment(self, comment: Comment):
        """Render individual comment"""
        # Color code by category
        category_colors = {
            CommentCategory.CRITICAL: "#ffcccc",
            CommentCategory.SUGGESTION: "#cce5ff",
            CommentCategory.CLARIFICATION: "#fff3cd",
            CommentCategory.APPROVAL: "#d4edda",
            CommentCategory.GENERAL: "#f8f9fa"
        }

        bg_color = category_colors.get(comment.category, "#f8f9fa")

        with st.container():
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>{comment.author_name}</strong>
                    <span style="color: #666; font-size: 0.9em;">
                        {comment.created_at.strftime('%Y-%m-%d %H:%M')}
                    </span>
                    <span style="float: right; background-color: #fff; padding: 2px 8px; border-radius: 3px; font-size: 0.8em;">
                        {comment.category.value}
                    </span>
                    <br/>
                    <span style="color: #666; font-size: 0.9em;">
                        Section: {comment.section}
                        {f'| Line: {comment.line_number}' if comment.line_number else ''}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(comment.content)

            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 3])

            with col1:
                if comment.status != CommentStatus.RESOLVED:
                    if st.button("✅ Resolve", key=f"resolve_{comment.comment_id}"):
                        self.comment_system.resolve_comment(
                            comment.comment_id,
                            st.session_state.current_user_id
                        )
                        st.rerun()
                else:
                    st.markdown("✅ Resolved")

            with col2:
                if st.button("💬 Reply", key=f"reply_{comment.comment_id}"):
                    st.session_state[f"show_reply_{comment.comment_id}"] = True

            # Reply form
            if st.session_state.get(f"show_reply_{comment.comment_id}", False):
                reply_content = st.text_area(
                    "Reply",
                    key=f"reply_content_{comment.comment_id}"
                )
                if st.button("Send Reply", key=f"send_reply_{comment.comment_id}"):
                    if reply_content:
                        self.comment_system.reply_to_comment(
                            comment.comment_id,
                            st.session_state.current_user_id,
                            st.session_state.current_user_name,
                            reply_content
                        )
                        st.session_state[f"show_reply_{comment.comment_id}"] = False
                        st.rerun()

            st.markdown("---")

    def _render_review_actions(self, assignment: ReviewAssignment):
        """Render review action buttons"""
        st.subheader("Review Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Approve", type="primary", use_container_width=True):
                # Check for critical unresolved comments
                critical = self.comment_system.get_critical_comments(
                    assignment.report_id, unresolved_only=True
                )
                if critical:
                    st.error(f"Cannot approve: {len(critical)} critical comments unresolved")
                else:
                    self.review_engine.update_review_status(
                        assignment.assignment_id,
                        ReviewStatus.APPROVED,
                        st.session_state.current_user_id,
                        decision="Approved"
                    )
                    st.success("Review approved!")
                    st.rerun()

        with col2:
            if st.button("❌ Reject", use_container_width=True):
                reason = st.text_area("Rejection Reason")
                if reason:
                    self.review_engine.update_review_status(
                        assignment.assignment_id,
                        ReviewStatus.REJECTED,
                        st.session_state.current_user_id,
                        decision=f"Rejected: {reason}"
                    )
                    st.success("Review rejected")
                    st.rerun()

        with col3:
            if st.button("📥 Export Review Summary", use_container_width=True):
                output_path = f"review_summary_{assignment.report_id}.json"
                self.review_engine.export_audit_report(
                    assignment.report_id,
                    output_path
                )
                st.success(f"Exported to {output_path}")

    def _render_completed_reviews(self, assignments: List[ReviewAssignment]):
        """Render completed reviews"""
        st.subheader("Completed Reviews")

        if not assignments:
            st.info("No completed reviews")
            return

        data = []
        for a in assignments:
            data.append({
                'Report ID': a.report_id,
                'Level': a.review_level.value,
                'Completed': a.completed_at.strftime("%Y-%m-%d %H:%M") if a.completed_at else "N/A",
                'Decision': a.decision or "N/A",
                'Status': a.status.value
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _render_all_reviews(self, assignments: List[ReviewAssignment]):
        """Render all reviews"""
        st.subheader("All Reviews")

        if not assignments:
            st.info("No reviews")
            return

        data = []
        for a in assignments:
            data.append({
                'Report ID': a.report_id,
                'Level': a.review_level.value,
                'Assigned': a.assigned_at.strftime("%Y-%m-%d"),
                'Due': a.due_date.strftime("%Y-%m-%d"),
                'Status': a.status.value,
                'Decision': a.decision or "N/A"
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _render_comments_view(self):
        """Render comments view"""
        st.title("💬 Comments")

        current_user = st.session_state.current_user_id

        # Get mentions
        mentions = self.comment_system.get_user_mentions(current_user)

        st.subheader("Your Mentions")
        if mentions:
            for comment in mentions[:10]:
                self._render_comment(comment)
        else:
            st.info("No mentions")

    def _render_dashboard(self):
        """Render analytics dashboard"""
        st.title("📊 Dashboard")

        # Overall statistics
        col1, col2, col3, col4 = st.columns(4)

        total_assignments = len(self.review_engine.assignments)
        pending_count = len([
            a for a in self.review_engine.assignments.values()
            if a.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]
        ])
        approved_count = len([
            a for a in self.review_engine.assignments.values()
            if a.status == ReviewStatus.APPROVED
        ])
        overdue_count = len(self.review_engine.get_overdue_reviews())

        col1.metric("Total Reviews", total_assignments)
        col2.metric("Pending", pending_count)
        col3.metric("Approved", approved_count)
        col4.metric("Overdue", overdue_count)

        # Charts would go here (using plotly, etc.)
        st.info("📈 Analytics charts would be displayed here")

    def _render_admin(self):
        """Render admin panel"""
        st.title("⚙️ Admin")

        tab1, tab2 = st.tabs(["Reviewers", "System Config"])

        with tab1:
            self._render_reviewer_management()

        with tab2:
            self._render_system_config()

    def _render_reviewer_management(self):
        """Render reviewer management"""
        st.subheader("Reviewer Management")

        # Add new reviewer
        with st.expander("➕ Add New Reviewer"):
            user_id = st.text_input("User ID")
            name = st.text_input("Name")
            email = st.text_input("Email")
            role = st.selectbox("Role", [r.value for r in ReviewerRole])
            specializations = st.text_input("Specializations (comma-separated)")

            if st.button("Add Reviewer"):
                if user_id and name and email:
                    reviewer = Reviewer(
                        user_id=user_id,
                        name=name,
                        email=email,
                        role=ReviewerRole(role),
                        specializations=[s.strip() for s in specializations.split(',') if s.strip()]
                    )
                    self.review_engine.register_reviewer(reviewer)
                    st.success(f"Added reviewer: {name}")
                    st.rerun()

        # List existing reviewers
        st.markdown("### Current Reviewers")
        if self.review_engine.reviewers:
            data = []
            for r in self.review_engine.reviewers.values():
                data.append({
                    'User ID': r.user_id,
                    'Name': r.name,
                    'Email': r.email,
                    'Role': r.role.value,
                    'Specializations': ', '.join(r.specializations)
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No reviewers registered")

    def _render_system_config(self):
        """Render system configuration"""
        st.subheader("System Configuration")

        st.json(self.review_engine.review_config)

    def _create_demo_users(self):
        """Create demo users for testing"""
        demo_users = [
            Reviewer(
                user_id="tech1",
                name="John Technician",
                email="john.tech@example.com",
                role=ReviewerRole.TECHNICIAN,
                specializations=["PV Testing", "Performance Analysis"]
            ),
            Reviewer(
                user_id="super1",
                name="Sarah Supervisor",
                email="sarah.super@example.com",
                role=ReviewerRole.SUPERVISOR,
                specializations=["PV Testing", "Quality Control"]
            ),
            Reviewer(
                user_id="qa1",
                name="Mike Quality",
                email="mike.qa@example.com",
                role=ReviewerRole.QUALITY_MANAGER,
                specializations=["ISO 17025", "Quality Assurance"]
            )
        ]

        for user in demo_users:
            self.review_engine.register_reviewer(user)


def main():
    """Main entry point"""
    app = ReviewUI()
    app.run()


if __name__ == "__main__":
    main()
