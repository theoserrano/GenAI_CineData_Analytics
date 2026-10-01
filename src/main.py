"""
CineData Analytics Text-to-SQL Main Entry Point
"""

import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database import list_tables

def main():
    print("=== CineData Analytics Text-to-SQL ===")
    try:
        tables = list_tables()
        print(f"Connected to database successfully ({len(tables)} tables loaded):")
        for table in tables:
            print(f" - {table}")
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    main()
