"""
Database Connection Management
Handles SQLAlchemy engine and session creation
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


# ==========================================
# Database Engine Configuration
# ==========================================

def get_engine():
    """
    Create and configure SQLAlchemy engine
    """
    database_url = settings.get_database_url()
    
    # SQLite specific configuration
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DEBUG  # Log SQL queries in debug mode
        )
        
        # Enable foreign key constraints for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        logger.info(f"SQLite engine created: {database_url}")
    
    # PostgreSQL specific configuration
    elif database_url.startswith("postgresql"):
        engine = create_engine(
            database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.DEBUG
        )
        logger.info("PostgreSQL engine created")
    
    else:
        # Generic configuration for other databases
        engine = create_engine(
            database_url,
            echo=settings.DEBUG
        )
        logger.info(f"Database engine created: {database_url}")
    
    return engine


# Create engine instance
engine = get_engine()


# ==========================================
# Session Factory
# ==========================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==========================================
# Dependency Injection for FastAPI/Streamlit
# ==========================================

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    Yields a database session and ensures it's closed after use
    
    Usage:
        db = next(get_db())
        try:
            # Your database operations
            pass
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ==========================================
# Context Manager for Database Sessions
# ==========================================

class DatabaseSession:
    """
    Context manager for database sessions
    
    Usage:
        with DatabaseSession() as db:
            # Your database operations
            result = db.query(Job).all()
    """
    
    def __init__(self):
        self.db = None
    
    def __enter__(self) -> Session:
        """Enter context manager"""
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        try:
            if exc_type is not None:
                # Exception occurred, rollback
                self.db.rollback()
                logger.error(f"Database error: {exc_val}")
            else:
                # No exception, commit
                self.db.commit()
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            self.db.rollback()
            raise
        finally:
            self.db.close()


# ==========================================
# Utility Functions
# ==========================================

def test_connection() -> bool:
    """
    Test database connection
    Returns True if connection is successful, False otherwise
    """
    try:
        with DatabaseSession() as db:
            # Use text() wrapper for SQLAlchemy 2.0
            db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_session() -> Session:
    """
    Get a new database session
    Note: Caller is responsible for closing the session
    
    Usage:
        db = get_session()
        try:
            # Your operations
            pass
        finally:
            db.close()
    """
    return SessionLocal()


def close_all_sessions():
    """
    Close all database sessions and dispose engine
    Useful for cleanup during shutdown
    """
    try:
        engine.dispose()
        logger.info("All database sessions closed")
    except Exception as e:
        logger.error(f"Error closing sessions: {e}")


# ==========================================
# Database Info
# ==========================================

def get_database_info() -> dict:
    """
    Get database connection information
    """
    return {
        "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
        "pool_size": settings.DB_POOL_SIZE if hasattr(settings, 'DB_POOL_SIZE') else None,
        "max_overflow": settings.DB_MAX_OVERFLOW if hasattr(settings, 'DB_MAX_OVERFLOW') else None,
        "is_sqlite": settings.DATABASE_URL.startswith("sqlite"),
        "is_postgresql": settings.DATABASE_URL.startswith("postgresql"),
    }


# ==========================================
# Initialization
# ==========================================

if __name__ == "__main__":
    """Test database connection"""
    print("=" * 50)
    print("Testing Database Connection")
    print("=" * 50)
    
    # Display database info
    info = get_database_info()
    print(f"Database Type: {'SQLite' if info['is_sqlite'] else 'PostgreSQL' if info['is_postgresql'] else 'Other'}")
    print(f"Database URL: {info['url']}")
    
    # Test connection
    if test_connection():
        print("SUCCESS: Database connection successful!")
    else:
        print("ERROR: Database connection failed!")
    
    print("=" * 50)