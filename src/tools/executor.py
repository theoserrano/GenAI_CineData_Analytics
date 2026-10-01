"""
Database Query Executor Tool for PydanticAI Text-to-SQL Agent.
Provides safe, read-only SQL query execution with regex blocklist validation and error capture for agent self-correction.
"""

import re
from typing import Any, Dict
from src.database import get_readonly_connection

# Forbidden DML/DDL operations regex pattern (case-insensitive with word boundaries)
FORBIDDEN_KEYWORDS_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|EXECUTE|REPLACE|CREATE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE
)


def validate_query_safety(query: str) -> None:
    """
    Validates SQL query string against regex blocklist of destructive keywords.
    Raises ValueError if a forbidden keyword is found.
    """
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty.")
        
    matches = FORBIDDEN_KEYWORDS_PATTERN.findall(query)
    if matches:
        forbidden = ", ".join(sorted(set(m.upper() for m in matches)))
        raise ValueError(
            f"Security Error: Query blocked by Regex Blocklist Guardrail. "
            f"Forbidden keyword(s) detected: [{forbidden}]. Only SELECT queries are permitted."
        )


def execute_query(query: str, max_rows: int = 100) -> Dict[str, Any]:
    """
    Executes a SQL query against the read-only SQLite database.
    Catches errors and returns structured result for agent self-correction.
    
    Args:
        query: SQL SELECT query string to execute.
        max_rows: Maximum number of rows to return (default: 100)
        
    Returns:
        Dictionary containing execution status ('success' or 'error'),
        column names, row count, data rows, or exact error message.
    """
    try:
        # 1. Guardrail de Sintaxe (Regex Blocklist)
        validate_query_safety(query)
        
        # 2. Guardrail de Conexão (Strict Read-Only Connection)
        conn = get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Extract column names if description is present
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results limited to max_rows
            rows = cursor.fetchmany(max_rows)
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "status": "success",
                "columns": columns,
                "row_count": len(data),
                "data": data
            }
        finally:
            conn.close()
            
    except ValueError as ve:
        return {
            "status": "error",
            "error_type": "security_guardrail",
            "error_message": str(ve)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "sqlite_execution_error",
            "error_message": str(e)
        }


if __name__ == "__main__":
    print("--- Testing valid query execution ---")
    res1 = execute_query("SELECT * FROM dim_genres LIMIT 3;")
    print("Status:", res1["status"])
    print("Columns:", res1.get("columns"))
    print("Data:", res1.get("data"))

    print("\n--- Testing forbidden DDL query interception ---")
    res2 = execute_query("DROP TABLE dim_movies;")
    print("Status:", res2["status"])
    print("Error:", res2.get("error_message"))

    print("\n--- Testing SQL syntax error capture ---")
    res3 = execute_query("SELECT * FORM dim_movies;")
    print("Status:", res3["status"])
    print("Error:", res3.get("error_message"))
