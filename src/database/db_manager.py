"""
Database manager for PV Test Report Automation.

Provides connection pooling, session management, and database operations
with ISO 17025 compliance.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from src.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 40,
        echo: bool = False,
    ):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            echo: Enable SQL echo for debugging
        """
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo

    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        logger.info("Initializing database connection...")

        # Create engine with connection pooling
        if "sqlite" in self.database_url:
            # SQLite doesn't support connection pooling
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
                echo=self.echo,
            )
        else:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,  # Verify connections before using
                echo=self.echo,
            )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        logger.info("Database connection initialized successfully")

    def create_tables(self) -> None:
        """Create all database tables."""
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self) -> None:
        """Drop all database tables. USE WITH CAUTION."""
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup.

        Yields:
            SQLAlchemy session

        Example:
            with db_manager.get_session() as session:
                result = session.query(TestReportDB).all()
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Check database health.

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self) -> None:
        """Close database connections and cleanup."""
        if self.engine:
            logger.info("Closing database connections...")
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager(
    database_url="postgresql://postgres:postgres@localhost:5432/pv_test_automation"
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Yields:
        Database session
    """
    with db_manager.get_session() as session:
        yield session
