"""
Database Configuration Module

Provides database engine, session management, and initialization utilities
for the PV test report automation system.
"""

from typing import Optional, Generator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool


class DatabaseConfig:
    """Database configuration and management."""

    def __init__(
        self,
        database_url: str = "sqlite:///./pv_test_lab.db",
        echo: bool = False,
        connect_args: Optional[dict] = None
    ):
        """
        Initialize database configuration.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements (for debugging)
            connect_args: Additional connection arguments
        """
        self.database_url = database_url
        self.echo = echo

        # Default connect args for SQLite
        if connect_args is None and database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        self.connect_args = connect_args or {}

        # Create engine
        self.engine = create_engine(
            database_url,
            echo=echo,
            connect_args=self.connect_args
        )

    def create_db_and_tables(self) -> None:
        """
        Create all database tables.

        This should be called during application initialization.
        """
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session.

        Yields:
            SQLModel Session

        Example:
            >>> db_config = DatabaseConfig()
            >>> with db_config.get_session() as session:
            ...     sample = Sample(...)
            ...     session.add(sample)
            ...     session.commit()
        """
        with Session(self.engine) as session:
            yield session

    def drop_all_tables(self) -> None:
        """
        Drop all database tables.

        WARNING: This will delete all data! Use with caution.
        Only use in testing/development environments.
        """
        SQLModel.metadata.drop_all(self.engine)

    def reset_database(self) -> None:
        """
        Drop and recreate all tables.

        WARNING: This will delete all data! Use with caution.
        Only use in testing/development environments.
        """
        self.drop_all_tables()
        self.create_db_and_tables()


# Global database configuration instance
# Can be overridden by application
_db_config: Optional[DatabaseConfig] = None


def init_db(
    database_url: str = "sqlite:///./pv_test_lab.db",
    echo: bool = False,
    connect_args: Optional[dict] = None,
    create_tables: bool = True
) -> DatabaseConfig:
    """
    Initialize the global database configuration.

    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        connect_args: Additional connection arguments
        create_tables: Whether to create tables immediately

    Returns:
        DatabaseConfig instance

    Example:
        >>> # Initialize with SQLite (default)
        >>> db_config = init_db()
        >>>
        >>> # Initialize with PostgreSQL
        >>> db_config = init_db(
        ...     database_url="postgresql://user:pass@localhost/pvtestlab",
        ...     echo=True
        ... )
    """
    global _db_config

    _db_config = DatabaseConfig(
        database_url=database_url,
        echo=echo,
        connect_args=connect_args
    )

    if create_tables:
        _db_config.create_db_and_tables()

    return _db_config


def get_db_config() -> DatabaseConfig:
    """
    Get the global database configuration.

    Returns:
        DatabaseConfig instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _db_config is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )
    return _db_config


def get_session() -> Generator[Session, None, None]:
    """
    Get a database session from the global configuration.

    Yields:
        SQLModel Session

    Example:
        >>> from database import get_session
        >>> with get_session() as session:
        ...     samples = session.query(Sample).all()
    """
    db_config = get_db_config()
    yield from db_config.get_session()


# Testing utilities
def create_test_engine():
    """
    Create an in-memory SQLite engine for testing.

    Returns:
        SQLAlchemy engine configured for testing
    """
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )


def create_test_session():
    """
    Create a test database session with in-memory SQLite.

    Returns:
        SQLModel Session for testing

    Example:
        >>> from database import create_test_session
        >>> session = create_test_session()
        >>> # Use session for testing
        >>> session.close()
    """
    engine = create_test_engine()
    SQLModel.metadata.create_all(engine)
    return Session(engine)


__all__ = [
    "DatabaseConfig",
    "init_db",
    "get_db_config",
    "get_session",
    "create_test_engine",
    "create_test_session",
]
