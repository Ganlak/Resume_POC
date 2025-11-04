"""
Database Initialization Script
Creates all database tables and performs initial setup
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from sqlalchemy import inspect

from app.database.models import Base, Job, Candidate, AnalysisResult, JobStatus, AnalysisStatus
from app.database.connection import engine, test_connection, get_database_info
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================
# Database Initialization Functions
# ==========================================

def create_tables():
    """
    Create all database tables defined in models
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def drop_tables():
    """
    Drop all database tables
    WARNING: This will delete all data!
    """
    try:
        logger.info("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully!")
        return True
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return False


def reset_database():
    """
    Reset database by dropping and recreating all tables
    WARNING: This will delete all data!
    """
    logger.info("Resetting database...")
    if drop_tables():
        return create_tables()
    return False


def check_tables_exist() -> dict:
    """
    Check which tables exist in the database
    Returns dictionary with table names and existence status
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    expected_tables = {
        "jobs": "jobs" in existing_tables,
        "candidates": "candidates" in existing_tables,
        "analysis_results": "analysis_results" in existing_tables
    }
    
    return expected_tables


def get_table_info():
    """
    Get detailed information about all tables
    """
    inspector = inspect(engine)
    tables_info = {}
    
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        tables_info[table_name] = {
            "columns": [col["name"] for col in columns],
            "column_count": len(columns)
        }
    
    return tables_info


def initialize_database(reset: bool = False):
    """
    Initialize database with all required tables
    
    Args:
        reset: If True, drop existing tables and recreate them
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Database Initialization Starting")
    logger.info("=" * 60)
    
    # Test connection
    logger.info("Step 1: Testing database connection...")
    if not test_connection():
        logger.error("Database connection failed! Cannot proceed.")
        return False
    logger.info("Database connection successful!")
    
    # Show database info
    db_info = get_database_info()
    logger.info(f"Database Type: {'SQLite' if db_info['is_sqlite'] else 'PostgreSQL' if db_info['is_postgresql'] else 'Other'}")
    logger.info(f"Database URL: {db_info['url']}")
    
    # Reset if requested
    if reset:
        logger.info("Step 2: Resetting database (dropping existing tables)...")
        if not reset_database():
            logger.error("Failed to reset database!")
            return False
    else:
        # Create tables if they don't exist
        logger.info("Step 2: Creating database tables...")
        if not create_tables():
            logger.error("Failed to create tables!")
            return False
    
    # Verify tables
    logger.info("Step 3: Verifying tables...")
    tables = check_tables_exist()
    
    all_exist = all(tables.values())
    
    if all_exist:
        logger.info("All required tables exist:")
        for table, exists in tables.items():
            status = "EXISTS" if exists else "MISSING"
            logger.info(f"  - {table}: {status}")
        
        # Show table details
        logger.info("\nStep 4: Table Details:")
        table_info = get_table_info()
        for table_name, info in table_info.items():
            logger.info(f"\n  Table: {table_name}")
            logger.info(f"  Columns ({info['column_count']}): {', '.join(info['columns'])}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Database initialization completed successfully!")
        logger.info("=" * 60)
        return True
    else:
        logger.error("Some tables are missing!")
        for table, exists in tables.items():
            if not exists:
                logger.error(f"  - {table}: MISSING")
        return False


# ==========================================
# Main Execution
# ==========================================

if __name__ == "__main__":
    """
    Run database initialization
    Usage:
        python app/database/init_db.py           # Create tables
        python app/database/init_db.py --reset   # Reset database
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate all tables)"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        print("\nWARNING: This will delete all existing data!")
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        if confirm.lower() != "yes":
            print("Database reset cancelled.")
            sys.exit(0)
    
    # Initialize database
    success = initialize_database(reset=args.reset)
    
    if success:
        print("\nDatabase is ready to use!")
        sys.exit(0)
    else:
        print("\nDatabase initialization failed!")
        sys.exit(1)