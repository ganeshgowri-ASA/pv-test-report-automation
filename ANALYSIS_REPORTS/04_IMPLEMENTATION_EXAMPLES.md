# Implementation Examples for Data Ingestion Branches

This document provides concrete code examples to guide implementation for each branch.

---

## Branch 06: Excel Data Ingestion - Reference Implementation

### Pydantic Models for IV Data

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class IVPoint(BaseModel):
    """Single IV curve data point"""
    voltage: float = Field(..., ge=0, description="Voltage in volts")
    current: float = Field(..., ge=0, description="Current in amps")
    power: Optional[float] = Field(None, description="Power in watts")
    
    @validator('power', pre=True, always=True)
    def calculate_power(cls, v, values):
        if 'voltage' in values and 'current' in values:
            return values['voltage'] * values['current']
        return v

class IVCurveData(BaseModel):
    """Complete IV curve dataset"""
    test_id: str = Field(..., min_length=1)
    module_sn: str = Field(..., description="Module serial number")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float = Field(..., ge=-50, le=150)
    irradiance: float = Field(..., ge=0, le=2000)
    points: List[IVPoint] = Field(..., min_items=2)
    voc: float = Field(..., gt=0, description="Open circuit voltage")
    isc: float = Field(..., gt=0, description="Short circuit current")
    mpp_voltage: float = Field(..., gt=0)
    mpp_current: float = Field(..., gt=0)
    fill_factor: float = Field(..., ge=0.5, le=1.0)
    efficiency: float = Field(..., ge=0.01, le=0.5)

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "TEST-2025-001",
                "module_sn": "MOD-2025-12345",
                "temperature": 25.0,
                "irradiance": 1000.0,
                "voc": 48.5,
                "isc": 10.5,
                "mpp_voltage": 38.5,
                "mpp_current": 9.8,
                "fill_factor": 0.79,
                "efficiency": 0.195
            }
        }
```

### Core Implementation Skeleton

```python
import logging
from pathlib import Path
from typing import Optional
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import pandas as pd
from .models import IVCurveData, IVPoint

logger = logging.getLogger(__name__)

class ExcelCore:
    """Excel parser for IV curve data"""
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
    MAGIC_NUMBERS = {
        b'\xd0\xcf\x11\xe0': '.xls',  # OLE2
        b'\x50\x4b\x03\x04': '.xlsx',  # ZIP
    }
    
    def __init__(self, validate_on_init: bool = True):
        """Initialize Excel parser"""
        self.validate_on_init = validate_on_init
        logger.info("ExcelCore initialized")
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate Excel file before processing"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.stat().st_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File exceeds max size of {self.MAX_FILE_SIZE} bytes")
        
        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file type: {file_path.suffix}")
        
        # Check magic numbers
        with open(file_path, 'rb') as f:
            header = f.read(4)
            valid = any(header.startswith(magic) for magic in self.MAGIC_NUMBERS)
            if not valid:
                raise ValueError("Invalid Excel file header (magic number check failed)")
        
        logger.debug(f"File validation passed for {file_path}")
        return True
    
    def parse_file(self, file_path: Path, sheet_name: str = "IV_DATA") -> List[IVCurveData]:
        """Parse Excel file and return IV curve data"""
        try:
            self.validate_file(file_path)
            logger.info(f"Parsing Excel file: {file_path}")
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Validate DataFrame structure
            required_columns = {
                'voltage', 'current', 'test_id', 'module_sn',
                'temperature', 'irradiance', 'voc', 'isc'
            }
            
            if not required_columns.issubset(set(df.columns)):
                raise ValueError(f"Missing required columns. Expected: {required_columns}")
            
            # Parse into Pydantic models
            results = []
            for _, row in df.iterrows():
                try:
                    data = IVCurveData(
                        test_id=str(row['test_id']),
                        module_sn=str(row['module_sn']),
                        temperature=float(row['temperature']),
                        irradiance=float(row['irradiance']),
                        points=[
                            IVPoint(
                                voltage=float(row['voltage']),
                                current=float(row['current'])
                            )
                        ],
                        voc=float(row['voc']),
                        isc=float(row['isc']),
                        mpp_voltage=float(row.get('mpp_voltage', 0)),
                        mpp_current=float(row.get('mpp_current', 0)),
                        fill_factor=float(row.get('fill_factor', 0.75)),
                        efficiency=float(row.get('efficiency', 0.19))
                    )
                    results.append(data)
                    logger.debug(f"Successfully parsed: {data.test_id}")
                except Exception as e:
                    logger.error(f"Error parsing row: {e}", exc_info=True)
                    raise
            
            logger.info(f"Successfully parsed {len(results)} records from {file_path}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}", exc_info=True)
            raise
```

---

## Branch 07: Document Parser - Reference Implementation

```python
import logging
from pathlib import Path
from typing import List, Dict, Optional
from python_docx import Document
import pypdf

logger = logging.getLogger(__name__)

class DocumentCore:
    """Word/PDF document parser"""
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    TIMEOUT_SECONDS = 30
    
    def __init__(self):
        """Initialize document parser"""
        logger.info("DocumentCore initialized")
    
    def validate_pdf(self, file_path: Path) -> bool:
        """Validate PDF file"""
        try:
            with open(file_path, 'rb') as f:
                # Check PDF signature
                if f.read(4) != b'%PDF':
                    raise ValueError("Invalid PDF signature")
            
            # Try to load and validate structure
            reader = pypdf.PdfReader(file_path)
            _ = len(reader.pages)  # Force read to validate
            logger.debug(f"PDF validation passed: {file_path}")
            return True
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            raise
    
    def validate_word(self, file_path: Path) -> bool:
        """Validate Word document"""
        try:
            doc = Document(file_path)
            _ = len(doc.paragraphs)  # Force read to validate
            logger.debug(f"Word validation passed: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Word validation failed: {e}")
            raise
    
    def extract_pdf_text(self, file_path: Path) -> Dict[str, str]:
        """Extract text from PDF"""
        try:
            self.validate_pdf(file_path)
            logger.info(f"Extracting text from PDF: {file_path}")
            
            reader = pypdf.PdfReader(file_path)
            text_by_page = {}
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                text_by_page[f"page_{page_num+1}"] = text
                logger.debug(f"Extracted {len(text)} chars from page {page_num+1}")
            
            return text_by_page
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}", exc_info=True)
            raise
    
    def extract_word_text(self, file_path: Path) -> str:
        """Extract text from Word document"""
        try:
            self.validate_word(file_path)
            logger.info(f"Extracting text from Word: {file_path}")
            
            doc = Document(file_path)
            full_text = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            text = "\n".join(full_text)
            logger.debug(f"Extracted {len(text)} chars from Word document")
            return text
        except Exception as e:
            logger.error(f"Word text extraction failed: {e}", exc_info=True)
            raise
```

---

## Branch 09: Storage with S3 - Reference Implementation

```python
import logging
import os
from pathlib import Path
from typing import Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class S3Config(BaseModel):
    """S3 configuration"""
    bucket_name: str = Field(..., min_length=3)
    region: str = Field(default="us-east-1")
    use_iam_role: bool = Field(default=True)
    enable_encryption: bool = Field(default=True)
    kms_key_id: Optional[str] = None
    enable_versioning: bool = Field(default=True)

class StorageCore:
    """S3 and local storage handler"""
    
    def __init__(self, config: S3Config):
        """Initialize storage with configuration"""
        self.config = config
        self.local_base_path = Path("./data_store")
        
        # Initialize S3 client
        try:
            if config.use_iam_role:
                # Use IAM role from instance metadata
                self.s3_client = boto3.client(
                    's3',
                    region_name=config.region,
                    config=Config(retries={'max_attempts': 3})
                )
            else:
                # Use credentials from environment/config file
                self.s3_client = boto3.client(
                    's3',
                    region_name=config.region,
                    config=Config(retries={'max_attempts': 3})
                )
            
            # Test credentials
            self.s3_client.head_bucket(Bucket=config.bucket_name)
            logger.info(f"S3 storage initialized: {config.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Check IAM role or credentials file.")
            raise
        except ClientError as e:
            logger.error(f"S3 bucket access failed: {e}")
            raise
    
    def upload_file_to_s3(self, local_path: Path, s3_key: str) -> bool:
        """Upload file to S3"""
        try:
            logger.info(f"Uploading {local_path} to s3://{self.config.bucket_name}/{s3_key}")
            
            # Validate local file
            if not local_path.exists():
                raise FileNotFoundError(f"Local file not found: {local_path}")
            
            # Prepare upload parameters
            extra_args = {}
            if self.config.enable_encryption:
                if self.config.kms_key_id:
                    extra_args['ServerSideEncryption'] = 'aws:kms'
                    extra_args['SSEKMSKeyId'] = self.config.kms_key_id
                else:
                    extra_args['ServerSideEncryption'] = 'AES256'
            
            # Upload with retry
            self.s3_client.upload_file(
                str(local_path),
                self.config.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
            raise
    
    def download_file_from_s3(self, s3_key: str, local_path: Path) -> bool:
        """Download file from S3"""
        try:
            logger.info(f"Downloading s3://{self.config.bucket_name}/{s3_key}")
            
            # Validate S3 key (prevent directory traversal)
            if ".." in s3_key or s3_key.startswith("/"):
                raise ValueError(f"Invalid S3 key format: {s3_key}")
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.config.bucket_name,
                s3_key,
                str(local_path)
            )
            
            logger.info(f"Successfully downloaded to: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"S3 download failed: {e}", exc_info=True)
            raise
    
    def save_file_locally(self, content: bytes, local_path: Path) -> bool:
        """Save file to local storage"""
        try:
            logger.info(f"Saving file locally: {local_path}")
            
            # Validate path (prevent directory traversal)
            if ".." in str(local_path):
                raise ValueError(f"Invalid path: {local_path}")
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with restricted permissions
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # Set secure permissions (owner read/write only)
            os.chmod(local_path, 0o640)
            
            logger.info(f"File saved: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Local file save failed: {e}", exc_info=True)
            raise
```

---

## Branch 10: Audit Trail - Reference Implementation

```python
import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class EventType(str, Enum):
    """Audit event types"""
    DATA_CREATED = "data_created"
    DATA_MODIFIED = "data_modified"
    DATA_ACCESSED = "data_accessed"
    DATA_DELETED = "data_deleted"
    EXPORT_INITIATED = "export_initiated"
    ACCESS_GRANTED = "access_granted"

class AuditEvent(Base):
    """Database model for audit events"""
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(36), unique=True, index=True)
    event_type = Column(String(50), index=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    user_id = Column(String(100), index=True)
    resource_type = Column(String(100))
    resource_id = Column(String(500))
    action = Column(String(50))
    details = Column(JSON)
    status = Column(String(20))  # success, failure
    ip_address = Column(String(45))

class TraceabilityCore:
    """Data lineage and audit trail tracking"""
    
    def __init__(self, database_url: str):
        """Initialize traceability system"""
        try:
            self.engine = create_engine(database_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("TraceabilityCore initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def log_event(
        self,
        event_type: EventType,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        details: Dict[str, Any],
        status: str = "success",
        ip_address: str = None
    ) -> str:
        """Log audit event to database"""
        try:
            import uuid
            event_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)
            
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type.value,
                timestamp=timestamp,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details,
                status=status,
                ip_address=ip_address
            )
            
            session = self.Session()
            try:
                session.add(event)
                session.commit()
                logger.info(f"Event logged: {event_id} - {event_type.value}")
                return event_id
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Event logging failed: {e}", exc_info=True)
            raise
    
    def get_lineage(self, resource_id: str) -> List[Dict]:
        """Get complete lineage for a resource"""
        try:
            session = self.Session()
            try:
                events = session.query(AuditEvent).filter(
                    AuditEvent.resource_id == resource_id
                ).order_by(AuditEvent.timestamp.asc()).all()
                
                lineage = []
                for event in events:
                    lineage.append({
                        'event_id': event.event_id,
                        'timestamp': event.timestamp.isoformat(),
                        'user_id': event.user_id,
                        'action': event.action,
                        'details': event.details
                    })
                
                logger.info(f"Retrieved lineage for {resource_id}: {len(lineage)} events")
                return lineage
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Lineage retrieval failed: {e}", exc_info=True)
            raise
```

---

## Key Security Implementations

### Input Validation Pattern
```python
def validate_input(value: str, max_length: int = 255, allowed_chars: str = None) -> str:
    """Validate and sanitize input"""
    if not isinstance(value, str):
        raise TypeError("Input must be string")
    
    if len(value) > max_length:
        raise ValueError(f"Input exceeds max length of {max_length}")
    
    if allowed_chars and not all(c in allowed_chars for c in value):
        raise ValueError(f"Input contains disallowed characters")
    
    # Remove potential injection payloads
    dangerous_patterns = ['..', '//', '\\\\', '${', '#{']
    for pattern in dangerous_patterns:
        if pattern in value:
            raise ValueError(f"Input contains suspicious pattern: {pattern}")
    
    return value.strip()
```

### Error Handling Pattern
```python
def safe_operation(operation_func, *args, **kwargs):
    """Wrapper for safe operation execution"""
    try:
        return operation_func(*args, **kwargs)
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

---

## Testing Examples

### Unit Test Pattern
```python
import pytest
from unittest.mock import Mock, patch

class TestExcelCore:
    """Unit tests for Excel parser"""
    
    @pytest.fixture
    def parser(self):
        return ExcelCore()
    
    def test_file_validation_invalid_extension(self, parser, tmp_path):
        """Test validation rejects invalid file types"""
        invalid_file = tmp_path / "test.csv"
        invalid_file.write_text("data")
        
        with pytest.raises(ValueError, match="Invalid file type"):
            parser.validate_file(invalid_file)
    
    def test_file_size_limit(self, parser, tmp_path):
        """Test validation enforces size limits"""
        large_file = tmp_path / "large.xlsx"
        large_file.write_bytes(b"x" * (100 * 1024 * 1024))
        
        with pytest.raises(ValueError, match="exceeds max size"):
            parser.validate_file(large_file)
    
    @patch('openpyxl.load_workbook')
    def test_parse_valid_excel(self, mock_load, parser, tmp_path):
        """Test parsing valid Excel file"""
        excel_file = tmp_path / "test.xlsx"
        excel_file.write_bytes(b"PK\x03\x04...")  # Minimal ZIP header
        
        # Mock workbook
        mock_ws = Mock()
        mock_ws.max_row = 10
        mock_load.return_value.active = mock_ws
        
        # Should not raise
        parser.validate_file(excel_file)
```

