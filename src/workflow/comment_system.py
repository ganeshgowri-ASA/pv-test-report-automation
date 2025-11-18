"""
Comment System for Report Review Workflow

Features:
- Inline comments on specific report sections
- Threaded discussions with replies
- @mentions for tagging reviewers
- File/image attachments
- Resolve/unresolve status tracking
- Comment categories (critical, suggestion, clarification, approval)
- Full audit trail for ISO 17025 compliance
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Set
import json
import re
from pathlib import Path


class CommentCategory(Enum):
    """Comment category for classification"""
    CRITICAL = "critical"  # Must be addressed before approval
    SUGGESTION = "suggestion"  # Recommended improvement
    CLARIFICATION = "clarification"  # Question or clarification needed
    APPROVAL = "approval"  # Approval comment
    GENERAL = "general"  # General comment


class CommentStatus(Enum):
    """Comment resolution status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


@dataclass
class Attachment:
    """File or image attachment"""
    attachment_id: str
    filename: str
    file_path: str
    file_type: str  # image, pdf, document, etc.
    file_size: int  # bytes
    uploaded_by: str
    uploaded_at: datetime
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'attachment_id': self.attachment_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat(),
            'description': self.description
        }


@dataclass
class Mention:
    """User mention in comment"""
    user_id: str
    user_name: str
    mentioned_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'mentioned_at': self.mentioned_at.isoformat()
        }


@dataclass
class Comment:
    """Individual comment"""
    comment_id: str
    report_id: str
    version_id: str
    parent_comment_id: Optional[str]  # None for root comments
    author_id: str
    author_name: str
    created_at: datetime
    modified_at: Optional[datetime]
    content: str
    category: CommentCategory
    status: CommentStatus
    section: str  # Report section (e.g., "test_results", "methodology", "page_3")
    line_number: Optional[int]  # For specific line references
    mentions: List[Mention] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'comment_id': self.comment_id,
            'report_id': self.report_id,
            'version_id': self.version_id,
            'parent_comment_id': self.parent_comment_id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'content': self.content,
            'category': self.category.value,
            'status': self.status.value,
            'section': self.section,
            'line_number': self.line_number,
            'mentions': [m.to_dict() for m in self.mentions],
            'attachments': [a.to_dict() for a in self.attachments],
            'tags': self.tags,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_note': self.resolution_note
        }


@dataclass
class CommentThread:
    """Comment thread with root comment and replies"""
    thread_id: str
    root_comment: Comment
    replies: List[Comment] = field(default_factory=list)
    participants: Set[str] = field(default_factory=set)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'thread_id': self.thread_id,
            'root_comment': self.root_comment.to_dict(),
            'replies': [r.to_dict() for r in self.replies],
            'participants': list(self.participants),
            'last_activity': self.last_activity.isoformat()
        }


class CommentSystem:
    """
    Comprehensive comment system for report review

    Features:
    - Create inline comments on specific sections
    - Thread comments with replies
    - @mention functionality
    - File attachments
    - Comment categories and status
    - Search and filter
    - Audit trail
    """

    def __init__(self, data_dir: str = "data/comments"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Storage
        self.comments: Dict[str, Comment] = {}
        self.threads: Dict[str, CommentThread] = {}
        self.attachments: Dict[str, Attachment] = {}

        # For quick lookups
        self.report_comments: Dict[str, List[str]] = {}  # report_id -> comment_ids
        self.user_mentions: Dict[str, List[str]] = {}  # user_id -> comment_ids

        self._load_data()

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{prefix}_{timestamp}"

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from comment content"""
        # Pattern: @username or @user.name
        pattern = r'@([\w.]+)'
        return re.findall(pattern, content)

    def create_comment(
        self,
        report_id: str,
        version_id: str,
        author_id: str,
        author_name: str,
        content: str,
        category: CommentCategory,
        section: str,
        parent_comment_id: Optional[str] = None,
        line_number: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Comment:
        """Create a new comment"""
        comment_id = self._generate_id("CMT")

        # Extract mentions
        mentioned_usernames = self._extract_mentions(content)
        mentions = [
            Mention(
                user_id=username,  # In real system, would lookup actual user_id
                user_name=username,
                mentioned_at=datetime.now()
            )
            for username in mentioned_usernames
        ]

        comment = Comment(
            comment_id=comment_id,
            report_id=report_id,
            version_id=version_id,
            parent_comment_id=parent_comment_id,
            author_id=author_id,
            author_name=author_name,
            created_at=datetime.now(),
            modified_at=None,
            content=content,
            category=category,
            status=CommentStatus.OPEN,
            section=section,
            line_number=line_number,
            mentions=mentions,
            tags=tags or []
        )

        self.comments[comment_id] = comment

        # Update report comments index
        if report_id not in self.report_comments:
            self.report_comments[report_id] = []
        self.report_comments[report_id].append(comment_id)

        # Update mentions index
        for mention in mentions:
            if mention.user_id not in self.user_mentions:
                self.user_mentions[mention.user_id] = []
            self.user_mentions[mention.user_id].append(comment_id)

        # Handle threading
        if parent_comment_id:
            # This is a reply
            self._add_to_thread(parent_comment_id, comment)
        else:
            # This is a root comment - create new thread
            thread_id = self._generate_id("THR")
            thread = CommentThread(
                thread_id=thread_id,
                root_comment=comment,
                participants={author_id},
                last_activity=datetime.now()
            )
            self.threads[thread_id] = thread

        self._save_data()
        return comment

    def reply_to_comment(
        self,
        parent_comment_id: str,
        author_id: str,
        author_name: str,
        content: str,
        category: CommentCategory = CommentCategory.GENERAL
    ) -> Comment:
        """Reply to an existing comment"""
        if parent_comment_id not in self.comments:
            raise ValueError(f"Parent comment {parent_comment_id} not found")

        parent_comment = self.comments[parent_comment_id]

        return self.create_comment(
            report_id=parent_comment.report_id,
            version_id=parent_comment.version_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            category=category,
            section=parent_comment.section,
            parent_comment_id=parent_comment_id,
            line_number=parent_comment.line_number
        )

    def _add_to_thread(self, parent_comment_id: str, reply: Comment) -> None:
        """Add a reply to a comment thread"""
        # Find the thread containing the parent comment
        for thread in self.threads.values():
            if thread.root_comment.comment_id == parent_comment_id:
                thread.replies.append(reply)
                thread.participants.add(reply.author_id)
                thread.last_activity = datetime.now()
                return

            # Check if parent is in replies
            if any(r.comment_id == parent_comment_id for r in thread.replies):
                thread.replies.append(reply)
                thread.participants.add(reply.author_id)
                thread.last_activity = datetime.now()
                return

    def add_attachment(
        self,
        comment_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        uploaded_by: str,
        description: str = ""
    ) -> Attachment:
        """Add an attachment to a comment"""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")

        attachment_id = self._generate_id("ATT")

        attachment = Attachment(
            attachment_id=attachment_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.now(),
            description=description
        )

        self.comments[comment_id].attachments.append(attachment)
        self.attachments[attachment_id] = attachment

        self._save_data()
        return attachment

    def edit_comment(
        self,
        comment_id: str,
        new_content: str,
        editor_id: str
    ) -> Comment:
        """Edit an existing comment"""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")

        comment = self.comments[comment_id]

        # Only author can edit (in real system, add permission checks)
        if comment.author_id != editor_id:
            raise PermissionError("Only comment author can edit")

        comment.content = new_content
        comment.modified_at = datetime.now()

        # Re-extract mentions
        mentioned_usernames = self._extract_mentions(new_content)
        comment.mentions = [
            Mention(
                user_id=username,
                user_name=username,
                mentioned_at=datetime.now()
            )
            for username in mentioned_usernames
        ]

        self._save_data()
        return comment

    def resolve_comment(
        self,
        comment_id: str,
        resolved_by: str,
        resolution_note: str = ""
    ) -> Comment:
        """Mark a comment as resolved"""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")

        comment = self.comments[comment_id]
        comment.status = CommentStatus.RESOLVED
        comment.resolved_by = resolved_by
        comment.resolved_at = datetime.now()
        comment.resolution_note = resolution_note

        self._save_data()
        return comment

    def unresolve_comment(
        self,
        comment_id: str,
        unresolved_by: str
    ) -> Comment:
        """Reopen a resolved comment"""
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")

        comment = self.comments[comment_id]
        comment.status = CommentStatus.OPEN
        comment.resolved_by = None
        comment.resolved_at = None

        self._save_data()
        return comment

    def get_report_comments(
        self,
        report_id: str,
        version_id: Optional[str] = None,
        section: Optional[str] = None,
        category: Optional[CommentCategory] = None,
        status: Optional[CommentStatus] = None,
        include_resolved: bool = True
    ) -> List[Comment]:
        """Get comments for a report with filters"""
        comment_ids = self.report_comments.get(report_id, [])
        comments = [self.comments[cid] for cid in comment_ids if cid in self.comments]

        # Apply filters
        if version_id:
            comments = [c for c in comments if c.version_id == version_id]

        if section:
            comments = [c for c in comments if c.section == section]

        if category:
            comments = [c for c in comments if c.category == category]

        if status:
            comments = [c for c in comments if c.status == status]

        if not include_resolved:
            comments = [c for c in comments if c.status != CommentStatus.RESOLVED]

        return sorted(comments, key=lambda x: x.created_at, reverse=True)

    def get_comment_threads(
        self,
        report_id: str,
        section: Optional[str] = None
    ) -> List[CommentThread]:
        """Get comment threads for a report"""
        threads = [
            t for t in self.threads.values()
            if t.root_comment.report_id == report_id
        ]

        if section:
            threads = [t for t in threads if t.root_comment.section == section]

        return sorted(threads, key=lambda x: x.last_activity, reverse=True)

    def get_user_mentions(self, user_id: str) -> List[Comment]:
        """Get all comments where user is mentioned"""
        comment_ids = self.user_mentions.get(user_id, [])
        comments = [self.comments[cid] for cid in comment_ids if cid in self.comments]
        return sorted(comments, key=lambda x: x.created_at, reverse=True)

    def get_critical_comments(
        self,
        report_id: str,
        unresolved_only: bool = True
    ) -> List[Comment]:
        """Get critical comments that must be addressed"""
        comments = self.get_report_comments(
            report_id,
            category=CommentCategory.CRITICAL
        )

        if unresolved_only:
            comments = [c for c in comments if c.status != CommentStatus.RESOLVED]

        return comments

    def get_comment_statistics(self, report_id: str) -> Dict[str, Any]:
        """Get statistics about comments for a report"""
        comments = self.get_report_comments(report_id)

        stats = {
            'total_comments': len(comments),
            'by_category': {},
            'by_status': {},
            'by_section': {},
            'critical_unresolved': 0,
            'total_threads': 0,
            'total_attachments': 0
        }

        # Count by category
        for category in CommentCategory:
            stats['by_category'][category.value] = len([
                c for c in comments if c.category == category
            ])

        # Count by status
        for status in CommentStatus:
            stats['by_status'][status.value] = len([
                c for c in comments if c.status == status
            ])

        # Count by section
        sections = set(c.section for c in comments)
        for section in sections:
            stats['by_section'][section] = len([
                c for c in comments if c.section == section
            ])

        # Critical unresolved
        stats['critical_unresolved'] = len([
            c for c in comments
            if c.category == CommentCategory.CRITICAL
            and c.status != CommentStatus.RESOLVED
        ])

        # Threads
        threads = self.get_comment_threads(report_id)
        stats['total_threads'] = len(threads)

        # Attachments
        stats['total_attachments'] = sum(len(c.attachments) for c in comments)

        return stats

    def search_comments(
        self,
        query: str,
        report_id: Optional[str] = None
    ) -> List[Comment]:
        """Search comments by content"""
        comments = list(self.comments.values())

        if report_id:
            comment_ids = self.report_comments.get(report_id, [])
            comments = [c for c in comments if c.comment_id in comment_ids]

        # Simple text search (in production, use proper search engine)
        query_lower = query.lower()
        matching_comments = [
            c for c in comments
            if query_lower in c.content.lower()
            or query_lower in c.author_name.lower()
            or any(query_lower in tag.lower() for tag in c.tags)
        ]

        return sorted(matching_comments, key=lambda x: x.created_at, reverse=True)

    def export_comments(
        self,
        report_id: str,
        output_path: str,
        include_resolved: bool = True
    ) -> None:
        """Export comments to JSON for archival/compliance"""
        comments = self.get_report_comments(
            report_id,
            include_resolved=include_resolved
        )
        threads = self.get_comment_threads(report_id)
        stats = self.get_comment_statistics(report_id)

        export_data = {
            'report_id': report_id,
            'exported_at': datetime.now().isoformat(),
            'statistics': stats,
            'comments': [c.to_dict() for c in comments],
            'threads': [t.to_dict() for t in threads]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

    def _save_data(self) -> None:
        """Save all data to disk"""
        data = {
            'comments': {k: v.to_dict() for k, v in self.comments.items()},
            'threads': {k: v.to_dict() for k, v in self.threads.items()},
            'attachments': {k: v.to_dict() for k, v in self.attachments.items()},
            'report_comments': self.report_comments,
            'user_mentions': self.user_mentions
        }

        with open(self.data_dir / 'comment_system.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_data(self) -> None:
        """Load data from disk"""
        data_file = self.data_dir / 'comment_system.json'
        if not data_file.exists():
            return

        try:
            with open(data_file, 'r') as f:
                data = json.load(f)

            # Load comments
            for comment_id, comment_data in data.get('comments', {}).items():
                self.comments[comment_id] = Comment(
                    comment_id=comment_data['comment_id'],
                    report_id=comment_data['report_id'],
                    version_id=comment_data['version_id'],
                    parent_comment_id=comment_data.get('parent_comment_id'),
                    author_id=comment_data['author_id'],
                    author_name=comment_data['author_name'],
                    created_at=datetime.fromisoformat(comment_data['created_at']),
                    modified_at=datetime.fromisoformat(comment_data['modified_at']) if comment_data.get('modified_at') else None,
                    content=comment_data['content'],
                    category=CommentCategory(comment_data['category']),
                    status=CommentStatus(comment_data['status']),
                    section=comment_data['section'],
                    line_number=comment_data.get('line_number'),
                    mentions=[
                        Mention(
                            user_id=m['user_id'],
                            user_name=m['user_name'],
                            mentioned_at=datetime.fromisoformat(m['mentioned_at'])
                        )
                        for m in comment_data.get('mentions', [])
                    ],
                    attachments=[
                        Attachment(
                            attachment_id=a['attachment_id'],
                            filename=a['filename'],
                            file_path=a['file_path'],
                            file_type=a['file_type'],
                            file_size=a['file_size'],
                            uploaded_by=a['uploaded_by'],
                            uploaded_at=datetime.fromisoformat(a['uploaded_at']),
                            description=a.get('description', '')
                        )
                        for a in comment_data.get('attachments', [])
                    ],
                    tags=comment_data.get('tags', []),
                    resolved_by=comment_data.get('resolved_by'),
                    resolved_at=datetime.fromisoformat(comment_data['resolved_at']) if comment_data.get('resolved_at') else None,
                    resolution_note=comment_data.get('resolution_note', '')
                )

            # Load threads
            for thread_id, thread_data in data.get('threads', {}).items():
                root_comment_id = thread_data['root_comment']['comment_id']
                reply_ids = [r['comment_id'] for r in thread_data.get('replies', [])]

                self.threads[thread_id] = CommentThread(
                    thread_id=thread_data['thread_id'],
                    root_comment=self.comments[root_comment_id],
                    replies=[self.comments[rid] for rid in reply_ids if rid in self.comments],
                    participants=set(thread_data.get('participants', [])),
                    last_activity=datetime.fromisoformat(thread_data['last_activity'])
                )

            # Load attachments
            for attachment_id, attachment_data in data.get('attachments', {}).items():
                self.attachments[attachment_id] = Attachment(
                    attachment_id=attachment_data['attachment_id'],
                    filename=attachment_data['filename'],
                    file_path=attachment_data['file_path'],
                    file_type=attachment_data['file_type'],
                    file_size=attachment_data['file_size'],
                    uploaded_by=attachment_data['uploaded_by'],
                    uploaded_at=datetime.fromisoformat(attachment_data['uploaded_at']),
                    description=attachment_data.get('description', '')
                )

            # Load indices
            self.report_comments = data.get('report_comments', {})
            self.user_mentions = data.get('user_mentions', {})

        except Exception as e:
            print(f"Error loading data: {e}")
