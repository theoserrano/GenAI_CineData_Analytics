import os
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "cinerocket.db"


def get_readonly_connection() -> sqlite3.Connection:
    """
    Establishes a strictly Read-Only connection to the SQLite database (cinerocket.db).
    Uses URI mode=ro to prevent any data mutation or structural alterations (DROP, DELETE, INSERT, etc.).
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found at path: {DB_PATH}")

    # SQLite read-only connection URI format
    # Replace backslashes with forward slashes for URI compatibility on Windows
    db_uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    
    conn = sqlite3.connect(db_uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables() -> list[str]:
    """
    Utility function to retrieve all table names from the database.
    """
    conn = get_readonly_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    finally:
        conn.close()


if __name__ == "__main__":
    print("Testing Read-Only Database Connection...")
    tables = list_tables()
    print(f"Total tables found ({len(tables)}):", tables)
