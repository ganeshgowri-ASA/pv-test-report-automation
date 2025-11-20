"""
Unit tests for Storage Manager module.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..storage_manager import (
    StorageManager,
    TestDataModel,
    ReportModel,
    BlobStorageModel,
    DataVersionModel,
    AuditLogModel,
    TestDataCreate,
    ReportCreate,
    BlobCreate,
    Base,
)


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def storage_manager(tmp_path):
    """Create a storage manager with temporary database."""
    db_path = tmp_path / "test.db"
    manager = StorageManager(
        database_url=f"sqlite:///{db_path}",
        blob_storage_path=tmp_path / "blobs",
    )
    manager.create_tables()
    return manager


class TestTestDataModel:
    """Test TestDataModel."""

    def test_create_test_data(self, test_db):
        """Test creating test data record."""
        test_data = TestDataModel(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime(2025, 1, 15),
            test_standard="IEC 61215",
            results={"voc": 38.5, "isc": 8.9},
            voc=38.5,
            isc=8.9,
            pmax=300.0,
        )

        test_db.add(test_data)
        test_db.commit()

        assert test_data.id is not None
        assert test_data.module_id == "MOD-001"

    def test_test_data_relationships(self, test_db):
        """Test test data relationships."""
        report = ReportModel(
            report_number="RPT-001",
            report_type="test_report",
        )
        test_db.add(report)
        test_db.commit()

        test_data = TestDataModel(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime.utcnow(),
            test_standard="IEC 61215",
            results={},
            report_id=report.id,
        )
        test_db.add(test_data)
        test_db.commit()

        assert test_data.report is not None
        assert test_data.report.report_number == "RPT-001"


class TestReportModel:
    """Test ReportModel."""

    def test_create_report(self, test_db):
        """Test creating report record."""
        report = ReportModel(
            report_number="RPT-2025-001",
            report_type="test_report",
            title="PV Module Test Report",
            lab_name="Test Laboratory",
            test_standard="IEC 61215",
            status="draft",
        )

        test_db.add(report)
        test_db.commit()

        assert report.id is not None
        assert report.report_number == "RPT-2025-001"
        assert report.status == "draft"

    def test_report_relationships(self, test_db):
        """Test report relationships."""
        report = ReportModel(
            report_number="RPT-001",
            report_type="test_report",
        )
        test_db.add(report)
        test_db.commit()

        # Add test data
        test_data = TestDataModel(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime.utcnow(),
            test_standard="IEC 61215",
            results={},
            report_id=report.id,
        )
        test_db.add(test_data)
        test_db.commit()

        # Refresh and check relationship
        test_db.refresh(report)
        assert len(report.test_data) == 1


class TestBlobStorageModel:
    """Test BlobStorageModel."""

    def test_create_blob(self, test_db):
        """Test creating blob record."""
        blob = BlobStorageModel(
            blob_type="image",
            file_name="chart.png",
            file_path="/data/blobs/chart.png",
            file_hash="abc123def456",
            file_size_bytes=102400,
            mime_type="image/png",
            width=800,
            height=600,
        )

        test_db.add(blob)
        test_db.commit()

        assert blob.id is not None
        assert blob.blob_type == "image"


class TestStorageManager:
    """Test StorageManager class."""

    def test_initialization(self, storage_manager):
        """Test storage manager initialization."""
        assert storage_manager.database_url is not None
        assert storage_manager.blob_storage_path.exists()

    def test_create_tables(self, tmp_path):
        """Test table creation."""
        db_path = tmp_path / "test.db"
        manager = StorageManager(f"sqlite:///{db_path}")
        manager.create_tables()

        # Verify tables exist
        session = manager.get_session()
        # If this doesn't raise an error, tables were created
        session.query(TestDataModel).first()
        session.close()

    def test_create_test_data(self, storage_manager):
        """Test creating test data through manager."""
        test_data_create = TestDataCreate(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime(2025, 1, 15),
            test_standard="IEC 61215",
            results={"voc": 38.5, "isc": 8.9},
            voc=38.5,
            isc=8.9,
            pmax=300.0,
            created_by="test_user",
        )

        result = storage_manager.create_test_data(test_data_create)

        assert result.id is not None
        assert result.module_id == "MOD-001"
        assert result.voc == 38.5

    def test_get_test_data(self, storage_manager):
        """Test retrieving test data."""
        # Create test data
        test_data_create = TestDataCreate(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime.utcnow(),
            test_standard="IEC 61215",
            results={},
        )
        created = storage_manager.create_test_data(test_data_create)

        # Retrieve it
        retrieved = storage_manager.get_test_data(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.module_id == "MOD-001"

    def test_get_test_data_by_module(self, storage_manager):
        """Test retrieving test data by module ID."""
        # Create multiple test data records
        for i in range(3):
            test_data_create = TestDataCreate(
                module_id="MOD-001",
                test_type=f"test_{i}",
                test_date=datetime.utcnow(),
                test_standard="IEC 61215",
                results={},
            )
            storage_manager.create_test_data(test_data_create)

        # Retrieve all for module
        results = storage_manager.get_test_data_by_module("MOD-001")

        assert len(results) == 3

    def test_update_test_data(self, storage_manager):
        """Test updating test data with versioning."""
        # Create test data
        test_data_create = TestDataCreate(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime.utcnow(),
            test_standard="IEC 61215",
            results={},
            voc=38.5,
        )
        created = storage_manager.create_test_data(test_data_create)

        # Update it
        updates = {"voc": 39.0, "isc": 9.0}
        updated = storage_manager.update_test_data(
            created.id, updates, "test_user"
        )

        assert updated.voc == 39.0
        assert updated.isc == 9.0
        assert updated.version == 2

    def test_create_report(self, storage_manager):
        """Test creating report."""
        report_create = ReportCreate(
            report_number="RPT-2025-001",
            report_type="test_report",
            title="Test Report",
            lab_name="PV Lab",
            created_by="test_user",
        )

        result = storage_manager.create_report(report_create)

        assert result.id is not None
        assert result.report_number == "RPT-2025-001"

    def test_get_report_by_number(self, storage_manager):
        """Test retrieving report by number."""
        # Create report
        report_create = ReportCreate(
            report_number="RPT-UNIQUE-001",
            report_type="test_report",
        )
        storage_manager.create_report(report_create)

        # Retrieve it
        retrieved = storage_manager.get_report_by_number("RPT-UNIQUE-001")

        assert retrieved is not None
        assert retrieved.report_number == "RPT-UNIQUE-001"

    def test_store_blob(self, storage_manager, tmp_path):
        """Test storing blob file."""
        # Create a test file
        test_file = tmp_path / "test_image.png"
        test_file.write_text("fake image data")

        blob_create = BlobCreate(
            blob_type="image",
            file_name="test_image.png",
            file_path=str(test_file),
            file_size_bytes=test_file.stat().st_size,
            mime_type="image/png",
            width=800,
            height=600,
            created_by="test_user",
        )

        result = storage_manager.store_blob(test_file, blob_create)

        assert result.id is not None
        assert result.file_hash is not None
        assert Path(result.file_path).exists()

    def test_store_blob_deduplication(self, storage_manager, tmp_path):
        """Test blob deduplication by hash."""
        # Create a test file
        test_file = tmp_path / "test_image.png"
        test_file.write_text("same content")

        blob_create = BlobCreate(
            blob_type="image",
            file_name="test_image.png",
            file_path=str(test_file),
            file_size_bytes=test_file.stat().st_size,
        )

        # Store twice
        result1 = storage_manager.store_blob(test_file, blob_create)
        result2 = storage_manager.store_blob(test_file, blob_create)

        # Should return same blob (deduplication)
        assert result1.id == result2.id
        assert result1.file_hash == result2.file_hash

    def test_get_blobs_by_report(self, storage_manager, tmp_path):
        """Test retrieving blobs for a report."""
        # Create report
        report_create = ReportCreate(
            report_number="RPT-001",
            report_type="test_report",
        )
        report = storage_manager.create_report(report_create)

        # Store blobs
        for i in range(3):
            test_file = tmp_path / f"image_{i}.png"
            test_file.write_text(f"image {i}")

            blob_create = BlobCreate(
                blob_type="image",
                file_name=f"image_{i}.png",
                file_path=str(test_file),
                file_size_bytes=test_file.stat().st_size,
                report_id=report.id,
            )
            storage_manager.store_blob(test_file, blob_create)

        # Retrieve blobs
        blobs = storage_manager.get_blobs_by_report(report.id)

        assert len(blobs) == 3

    def test_version_history(self, storage_manager):
        """Test version history tracking."""
        # Create and update test data
        test_data_create = TestDataCreate(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime.utcnow(),
            test_standard="IEC 61215",
            results={},
            voc=38.5,
        )
        created = storage_manager.create_test_data(test_data_create)

        # Make multiple updates
        for i in range(3):
            updates = {"voc": 38.5 + i}
            storage_manager.update_test_data(created.id, updates, "test_user")

        # Get version history
        history = storage_manager.get_version_history("test_data", created.id)

        assert len(history) >= 3

    def test_file_hash_calculation(self, storage_manager, tmp_path):
        """Test file hash calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        file_hash = storage_manager._calculate_file_hash(test_file)

        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA-256 produces 64 hex chars

    def test_entity_to_dict(self, storage_manager):
        """Test entity to dictionary conversion."""
        test_data_create = TestDataCreate(
            module_id="MOD-001",
            test_type="flash_test",
            test_date=datetime.utcnow(),
            test_standard="IEC 61215",
            results={},
        )
        entity = storage_manager.create_test_data(test_data_create)

        result = storage_manager._entity_to_dict(entity)

        assert isinstance(result, dict)
        assert "module_id" in result
        assert result["module_id"] == "MOD-001"


class TestDatabaseModels:
    """Test database model validations and constraints."""

    def test_unique_report_number(self, storage_manager):
        """Test unique constraint on report number."""
        report1 = ReportCreate(
            report_number="RPT-UNIQUE",
            report_type="test_report",
        )
        storage_manager.create_report(report1)

        # Try to create another with same number
        report2 = ReportCreate(
            report_number="RPT-UNIQUE",
            report_type="test_report",
        )

        with pytest.raises(Exception):  # Will raise IntegrityError
            storage_manager.create_report(report2)

    def test_audit_log_creation(self, test_db):
        """Test creating audit log."""
        audit_log = AuditLogModel(
            action="create",
            entity_type="test_data",
            entity_id=1,
            user="test_user",
            new_value={"voc": 38.5},
        )

        test_db.add(audit_log)
        test_db.commit()

        assert audit_log.id is not None


@pytest.mark.asyncio
async def test_async_operations():
    """Test async database operations."""
    # Note: This requires an async-compatible database
    # SQLite with aiosqlite is used here
    manager = StorageManager(
        "sqlite+aiosqlite:///:memory:",
        blob_storage_path=Path(tempfile.mkdtemp()),
    )

    # Test would require async setup
    # Skipping detailed async tests for now
    assert manager.async_engine is not None
