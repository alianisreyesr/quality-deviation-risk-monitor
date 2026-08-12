import csv
import sqlite3
from pathlib import Path

from app.config import DATA_FILE, DATABASE_FILE, SCHEMA_FILE
from app.logger import setup_logger

logger = setup_logger(__name__)


def connection(database_file: Path = DATABASE_FILE) -> sqlite3.Connection:
    """Create and return a database connection.
    
    Args:
        database_file: Path to the database file
        
    Returns:
        sqlite3.Connection: Active database connection
        
    Raises:
        sqlite3.DatabaseError: If connection fails
    """
    try:
        database_file.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(database_file)
        conn.row_factory = sqlite3.Row
        logger.debug(f"Database connection established to {database_file}")
        return conn
    except sqlite3.DatabaseError as e:
        logger.error(f"Failed to connect to database at {database_file}: {e}")
        raise


def initialize_database(database_file: Path = DATABASE_FILE) -> None:
    """Initialize database schema and seed data.
    
    Args:
        database_file: Path to the database file
        
    Raises:
        FileNotFoundError: If schema or data files are missing
        sqlite3.DatabaseError: If database operations fail
    """
    try:
        if not SCHEMA_FILE.exists():
            raise FileNotFoundError(f"Schema file not found at {SCHEMA_FILE}")
        if not DATA_FILE.exists():
            raise FileNotFoundError(f"Data file not found at {DATA_FILE}")
        
        logger.info("Initializing database schema and data...")
        
        with connection(database_file) as conn:
            conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
            existing = conn.execute("SELECT COUNT(*) FROM deviations").fetchone()[0]
            
            if existing:
                logger.info(f"Database already contains {existing} records")
                return
            
            logger.info("Seeding database from CSV...")
            with DATA_FILE.open(newline="", encoding="utf-8") as source:
                rows = list(csv.DictReader(source))
            
            if not rows:
                logger.warning("CSV file is empty")
                return
            
            conn.executemany(
                """INSERT INTO deviations (deviation_id, title, severity, opened_date, due_date, investigation_owner, repeat_occurrence, record_complete, review_status) VALUES (:deviation_id, :title, :severity, :opened_date, :due_date, NULLIF(:investigation_owner, ''), :repeat_occurrence, :record_complete, :review_status)""",
                rows,
            )
            conn.commit()
            logger.info(f"Successfully seeded {len(rows)} records into database")
            
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        raise
    except sqlite3.DatabaseError as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise


def fetch_deviations(database_file: Path = DATABASE_FILE) -> list[dict[str, object]]:
    """Fetch all deviation records from database.
    
    Args:
        database_file: Path to the database file
        
    Returns:
        list[dict]: List of deviation records
        
    Raises:
        sqlite3.DatabaseError: If query fails
    """
    try:
        with connection(database_file) as conn:
            rows = [dict(row) for row in conn.execute("SELECT * FROM deviations ORDER BY due_date, deviation_id")]
        logger.debug(f"Retrieved {len(rows)} deviations from database")
        return rows
    except sqlite3.DatabaseError as e:
        logger.error(f"Failed to fetch deviations: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching deviations: {e}")
        raise
