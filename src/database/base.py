"""
Database Base Configuration
============================

Provides SQLAlchemy engine, session management, and declarative base for all models.

This module handles:
    - Database engine creation with connection pooling
    - Session factory and context managers
    - Declarative base class for all ORM models
    - Database initialization and table creation

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (default: sqlite:///./pv_test_automation.db)
    DB_POOL_SIZE: Connection pool size (default: 5)
    DB_MAX_OVERFLOW: Max overflow connections (default: 10)
    DB_ECHO: Enable SQL query logging (default: False)

Example:
    >>> from src.database.base import engine, get_session, Base
    >>> Base.metadata.create_all(bind=engine)
    >>> with get_session() as session:
    ...     # Perform database operations
    ...     pass
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./pv_test_automation.db"
)

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Create database engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=DB_ECHO
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using
        echo=DB_ECHO
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base for models
Base = declarative_base(metadata=metadata)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup.

    Provides a context manager that:
        - Creates a new database session
        - Automatically commits on success
        - Rolls back on exceptions
        - Closes the session when done

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> with get_session() as session:
        ...     user = session.query(User).first()
        ...     print(user.username)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This should be called once during application startup.
    It creates all tables defined in the models.

    Example:
        >>> from src.database.base import init_db
        >>> init_db()
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data. Use only in development/testing.

    Example:
        >>> from src.database.base import drop_db
        >>> drop_db()  # Caution: destroys all data!
    """
    Base.metadata.drop_all(bind=engine)
