"""
Storage Manager for PV Test Automation (Session 09)

Manages database integration, file storage, blob storage for images/PDFs,
and data versioning with SQLAlchemy.
"""

import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# SQLAlchemy Base
Base = declarative_base()


# ============================================================================
# SQLAlchemy Database Models
# ============================================================================


class TestDataModel(Base):
    """Test data storage model."""

    __tablename__ = "test_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(String(100), nullable=False, index=True)
    test_type = Column(String(50), nullable=False, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    test_standard = Column(String(50), nullable=False)

    # Test results (JSON for flexibility)
    results = Column(JSON, nullable=False)
    metadata = Column(JSON, default={})

    # Quality metrics
    voc = Column(Float)
    isc = Column(Float)
    pmax = Column(Float)
    vmp = Column(Float)
    imp = Column(Float)
    fill_factor = Column(Float)
    efficiency = Column(Float)

    # Environmental conditions
    irradiance = Column(Float)
    temperature = Column(Float)

    # File references
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    version = Column(Integer, default=1)

    # Relationships
    report = relationship("ReportModel", back_populates="test_data")
    audit_logs = relationship("AuditLogModel", back_populates="test_data")

    def __repr__(self):
        return f"<TestData(id={self.id}, module={self.module_id}, type={self.test_type})>"


class ReportModel(Base):
    """Test report storage model."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_number = Column(String(100), unique=True, nullable=False, index=True)
    report_type = Column(String(50), nullable=False)

    # Report metadata
    title = Column(String(500))
    lab_name = Column(String(200))
    accreditation = Column(String(100))
    test_standard = Column(String(50))

    # Module information
    module_manufacturer = Column(String(200))
    module_model = Column(String(200))
    module_serial = Column(String(100))

    # Dates
    test_start_date = Column(DateTime)
    test_end_date = Column(DateTime)
    issue_date = Column(DateTime)

    # Personnel
    test_engineer = Column(String(100))
    reviewer = Column(String(100))
    approver = Column(String(100))

    # File storage
    file_path = Column(String(500))
    file_hash = Column(String(64))  # SHA-256
    file_size_bytes = Column(Integer)
    file_format = Column(String(10))

    # Status
    status = Column(String(50), default="draft", index=True)
    is_active = Column(Boolean, default=True)

    # JSON fields
    metadata = Column(JSON, default={})
    extracted_data = Column(JSON, default={})

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    version = Column(Integer, default=1)

    # Relationships
    test_data = relationship("TestDataModel", back_populates="report")
    blobs = relationship("BlobStorageModel", back_populates="report")
    audit_logs = relationship("AuditLogModel", back_populates="report")
    versions = relationship("DataVersionModel", back_populates="report")

    def __repr__(self):
        return f"<Report(id={self.id}, number={self.report_number}, status={self.status})>"


class BlobStorageModel(Base):
    """Blob storage for images, PDFs, and binary data."""

    __tablename__ = "blob_storage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blob_type = Column(String(50), nullable=False, index=True)  # image, pdf, document
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)  # SHA-256
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100))

    # Image-specific fields
    width = Column(Integer)
    height = Column(Integer)
    dpi = Column(Integer)

    # Relationships
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    report = relationship("ReportModel", back_populates="blobs")

    # Metadata
    metadata = Column(JSON, default={})
    tags = Column(JSON, default=[])

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100))

    def __repr__(self):
        return f"<Blob(id={self.id}, type={self.blob_type}, file={self.file_name})>"


class DataVersionModel(Base):
    """Version control for test data and reports."""

    __tablename__ = "data_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # test_data, report
    entity_id = Column(Integer, nullable=False)
    version_number = Column(Integer, nullable=False)

    # Snapshot of data at this version
    data_snapshot = Column(JSON, nullable=False)
    changes = Column(JSON, default={})
    change_summary = Column(Text)

    # Version metadata
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    report = relationship("ReportModel", back_populates="versions")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False)
    change_reason = Column(Text)

    def __repr__(self):
        return f"<Version(id={self.id}, entity={self.entity_type}:{self.entity_id}, v{self.version_number})>"


class AuditLogModel(Base):
    """Audit log for traceability (linked to traceability_tracker)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)

    # Action details
    old_value = Column(JSON)
    new_value = Column(JSON)
    changes = Column(JSON, default={})
    description = Column(Text)

    # Relationships
    test_data_id = Column(Integer, ForeignKey("test_data.id"), nullable=True)
    test_data = relationship("TestDataModel", back_populates="audit_logs")
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    report = relationship("ReportModel", back_populates="audit_logs")

    # Compliance
    compliance_standard = Column(String(50))  # ISO 17025, etc.
    traceability_chain = Column(JSON, default=[])

    # Audit metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = Column(String(100), nullable=False)
    ip_address = Column(String(45))
    session_id = Column(String(100))

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user})>"


# ============================================================================
# Pydantic Models for API/Validation
# ============================================================================


class TestDataCreate(BaseModel):
    """Pydantic model for creating test data."""

    module_id: str
    test_type: str
    test_date: datetime
    test_standard: str
    results: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    voc: Optional[float] = None
    isc: Optional[float] = None
    pmax: Optional[float] = None
    vmp: Optional[float] = None
    imp: Optional[float] = None
    fill_factor: Optional[float] = None
    efficiency: Optional[float] = None
    irradiance: Optional[float] = None
    temperature: Optional[float] = None
    created_by: Optional[str] = None


class ReportCreate(BaseModel):
    """Pydantic model for creating reports."""

    report_number: str
    report_type: str
    title: Optional[str] = None
    lab_name: Optional[str] = None
    test_standard: Optional[str] = None
    module_manufacturer: Optional[str] = None
    module_model: Optional[str] = None
    module_serial: Optional[str] = None
    test_engineer: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class BlobCreate(BaseModel):
    """Pydantic model for blob storage."""

    blob_type: str
    file_name: str
    file_path: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    report_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None


# ============================================================================
# Storage Manager Class
# ============================================================================


class StorageManager:
    """
    Production-ready storage manager for PV test automation.

    Supports:
    - SQLAlchemy database operations (sync and async)
    - File storage management
    - Blob storage for images/PDFs
    - Data versioning
    - Transaction management
    - Batch operations
    - Connection pooling
    """

    def __init__(
        self,
        database_url: str,
        blob_storage_path: Optional[Union[str, Path]] = None,
        echo: bool = False,
    ):
        """
        Initialize storage manager.

        Args:
            database_url: SQLAlchemy database URL
            blob_storage_path: Path for blob file storage
            echo: Whether to echo SQL queries
        """
        self.database_url = database_url
        self.blob_storage_path = Path(blob_storage_path or "./data/blobs")
        self.blob_storage_path.mkdir(parents=True, exist_ok=True)

        # Create engine
        self.engine = create_engine(database_url, echo=echo, pool_pre_ping=True)

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Create async engine if database supports it
        if database_url.startswith("sqlite"):
            async_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        elif database_url.startswith("postgresql"):
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            async_url = None

        if async_url:
            self.async_engine = create_async_engine(async_url, echo=echo)
            self.AsyncSessionLocal = sessionmaker(
                self.async_engine, class_=AsyncSession, expire_on_commit=False
            )
        else:
            self.async_engine = None
            self.AsyncSessionLocal = None

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self):
        """Get database session."""
        return self.SessionLocal()

    async def get_async_session(self):
        """Get async database session."""
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async sessions not configured for this database")
        return self.AsyncSessionLocal()

    # ========================================================================
    # Test Data Operations
    # ========================================================================

    def create_test_data(
        self, test_data: TestDataCreate, session=None
    ) -> TestDataModel:
        """Create test data record."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            db_test_data = TestDataModel(**test_data.dict())
            session.add(db_test_data)
            session.commit()
            session.refresh(db_test_data)
            return db_test_data
        finally:
            if should_close:
                session.close()

    def get_test_data(self, test_id: int, session=None) -> Optional[TestDataModel]:
        """Get test data by ID."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return session.query(TestDataModel).filter(TestDataModel.id == test_id).first()
        finally:
            if should_close:
                session.close()

    def get_test_data_by_module(
        self, module_id: str, session=None
    ) -> List[TestDataModel]:
        """Get all test data for a module."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return (
                session.query(TestDataModel)
                .filter(TestDataModel.module_id == module_id)
                .order_by(TestDataModel.test_date.desc())
                .all()
            )
        finally:
            if should_close:
                session.close()

    def update_test_data(
        self,
        test_id: int,
        updates: Dict[str, Any],
        user: str,
        session=None,
    ) -> TestDataModel:
        """Update test data with versioning."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            test_data = session.query(TestDataModel).filter(TestDataModel.id == test_id).first()
            if not test_data:
                raise ValueError(f"Test data {test_id} not found")

            # Create version before update
            self._create_version(
                session, "test_data", test_id, test_data, user, "Update"
            )

            # Apply updates
            for key, value in updates.items():
                if hasattr(test_data, key):
                    setattr(test_data, key, value)

            test_data.version += 1
            test_data.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(test_data)
            return test_data
        finally:
            if should_close:
                session.close()

    # ========================================================================
    # Report Operations
    # ========================================================================

    def create_report(self, report: ReportCreate, session=None) -> ReportModel:
        """Create report record."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            db_report = ReportModel(**report.dict())
            session.add(db_report)
            session.commit()
            session.refresh(db_report)
            return db_report
        finally:
            if should_close:
                session.close()

    def get_report(self, report_id: int, session=None) -> Optional[ReportModel]:
        """Get report by ID."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return session.query(ReportModel).filter(ReportModel.id == report_id).first()
        finally:
            if should_close:
                session.close()

    def get_report_by_number(
        self, report_number: str, session=None
    ) -> Optional[ReportModel]:
        """Get report by report number."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return (
                session.query(ReportModel)
                .filter(ReportModel.report_number == report_number)
                .first()
            )
        finally:
            if should_close:
                session.close()

    # ========================================================================
    # Blob Storage Operations
    # ========================================================================

    def store_blob(
        self, file_path: Union[str, Path], blob_data: BlobCreate, session=None
    ) -> BlobStorageModel:
        """
        Store blob file and create database record.

        Args:
            file_path: Source file path
            blob_data: Blob metadata

        Returns:
            BlobStorageModel instance
        """
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Calculate file hash
            file_hash = self._calculate_file_hash(source_path)

            # Check if blob already exists
            existing = (
                session.query(BlobStorageModel)
                .filter(BlobStorageModel.file_hash == file_hash)
                .first()
            )
            if existing:
                return existing

            # Create storage path (organized by type and date)
            date_path = datetime.utcnow().strftime("%Y/%m/%d")
            storage_dir = self.blob_storage_path / blob_data.blob_type / date_path
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Copy file to blob storage
            dest_path = storage_dir / source_path.name
            counter = 1
            while dest_path.exists():
                dest_path = storage_dir / f"{source_path.stem}_{counter}{source_path.suffix}"
                counter += 1

            # Copy file
            import shutil
            shutil.copy2(source_path, dest_path)

            # Create database record
            db_blob = BlobStorageModel(
                blob_type=blob_data.blob_type,
                file_name=blob_data.file_name,
                file_path=str(dest_path),
                file_hash=file_hash,
                file_size_bytes=blob_data.file_size_bytes,
                mime_type=blob_data.mime_type,
                width=blob_data.width,
                height=blob_data.height,
                report_id=blob_data.report_id,
                metadata=blob_data.metadata,
                tags=blob_data.tags,
                created_by=blob_data.created_by,
            )

            session.add(db_blob)
            session.commit()
            session.refresh(db_blob)
            return db_blob

        finally:
            if should_close:
                session.close()

    def get_blob(self, blob_id: int, session=None) -> Optional[BlobStorageModel]:
        """Get blob by ID."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return session.query(BlobStorageModel).filter(BlobStorageModel.id == blob_id).first()
        finally:
            if should_close:
                session.close()

    def get_blobs_by_report(
        self, report_id: int, session=None
    ) -> List[BlobStorageModel]:
        """Get all blobs for a report."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return (
                session.query(BlobStorageModel)
                .filter(BlobStorageModel.report_id == report_id)
                .all()
            )
        finally:
            if should_close:
                session.close()

    # ========================================================================
    # Versioning Operations
    # ========================================================================

    def _create_version(
        self,
        session,
        entity_type: str,
        entity_id: int,
        entity_data: Any,
        user: str,
        reason: str,
    ) -> DataVersionModel:
        """Create version snapshot."""
        # Get current version number
        current_version = (
            session.query(DataVersionModel)
            .filter(
                DataVersionModel.entity_type == entity_type,
                DataVersionModel.entity_id == entity_id,
            )
            .count()
        )

        # Create snapshot
        snapshot = self._entity_to_dict(entity_data)

        version = DataVersionModel(
            entity_type=entity_type,
            entity_id=entity_id,
            version_number=current_version + 1,
            data_snapshot=snapshot,
            created_by=user,
            change_reason=reason,
        )

        session.add(version)
        return version

    def _entity_to_dict(self, entity) -> Dict[str, Any]:
        """Convert SQLAlchemy entity to dictionary."""
        result = {}
        for col in entity.__table__.columns:
            value = getattr(entity, col.name)
            if isinstance(value, datetime):
                result[col.name] = value.isoformat()
            else:
                result[col.name] = value
        return result

    def get_version_history(
        self, entity_type: str, entity_id: int, session=None
    ) -> List[DataVersionModel]:
        """Get version history for an entity."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            return (
                session.query(DataVersionModel)
                .filter(
                    DataVersionModel.entity_type == entity_type,
                    DataVersionModel.entity_id == entity_id,
                )
                .order_by(DataVersionModel.version_number.desc())
                .all()
            )
        finally:
            if should_close:
                session.close()

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def batch_create_async(
        self, items: List[BaseModel], model_class
    ) -> List[Any]:
        """Batch create records asynchronously."""
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async operations not supported")

        async with self.AsyncSessionLocal() as session:
            db_items = [model_class(**item.dict()) for item in items]
            session.add_all(db_items)
            await session.commit()
            return db_items

    def bulk_insert(self, items: List[Dict[str, Any]], model_class, session=None):
        """Bulk insert records (faster than individual inserts)."""
        should_close = session is None
        if session is None:
            session = self.get_session()

        try:
            session.bulk_insert_mappings(model_class, items)
            session.commit()
        finally:
            if should_close:
                session.close()
