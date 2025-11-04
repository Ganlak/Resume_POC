"""
Database Package
Contains all database models, connections, and operations
"""

from app.database.connection import (
    get_db,
    engine,
    SessionLocal,
    DatabaseSession,
    get_session,
    test_connection,
    close_all_sessions,
    get_database_info
)

from app.database.models import (
    Base,
    Job,
    Candidate,
    AnalysisResult,
    JobStatus,
    AnalysisStatus
)

from app.database.init_db import (
    create_tables,
    drop_tables,
    reset_database,
    check_tables_exist,
    initialize_database
)

__all__ = [
    # Connection utilities
    "get_db",
    "engine",
    "SessionLocal",
    "DatabaseSession",
    "get_session",
    "test_connection",
    "close_all_sessions",
    "get_database_info",
    
    # Models
    "Base",
    "Job",
    "Candidate",
    "AnalysisResult",
    "JobStatus",
    "AnalysisStatus",
    
    # Database operations
    "create_tables",
    "drop_tables",
    "reset_database",
    "check_tables_exist",
    "initialize_database",
]