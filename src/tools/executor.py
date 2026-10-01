"""
Database Query Executor Tool for PydanticAI Text-to-SQL Agent.
Provides safe, read-only SQL query execution with guardrail validation, hard row limits,
and error capture for agent self-correction.
"""

from typing import Any, Dict
from src.database import get_readonly_connection
from src.utils.guardrails import validate_sql_security

# Hard Maximum Row Limit ceiling to prevent context/RAM overflow
DEFAULT_MAX_ROWS = 100
HARD_MAX_ROWS_CEILING = 500


def execute_query(query: str, max_rows: int = DEFAULT_MAX_ROWS) -> Dict[str, Any]:
    """
    Executes a SQL query against the read-only SQLite database.
    Passes query through security guardrails before execution.
    Enforces a hard limit ceiling on returned rows to prevent memory overflow.
    Catches syntax/runtime errors and returns structured result for agent self-correction.
    
    Args:
        query: SQL SELECT or WITH (CTE) query string to execute.
        max_rows: Maximum number of rows to return (default: 100, capped at 500)
        
    Returns:
        Dictionary containing execution status ('success' or 'error'),
        column names, row count, data rows, or exact error message.
    """
    try:
        # 1. Guardrail de Sintaxe e Injeção de SQL
        validate_sql_security(query)
        
        # Enforce hard limit ceiling on max_rows
        effective_max_rows = min(max(1, max_rows), HARD_MAX_ROWS_CEILING)
        
        # 2. Guardrail de Conexão (Strict Read-Only Connection)
        conn = get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Extract column names if description is present
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results strictly limited to effective_max_rows via fetchmany
            rows = cursor.fetchmany(effective_max_rows)
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "status": "success",
                "columns": columns,
                "row_count": len(data),
                "max_rows_applied": effective_max_rows,
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
    print("--- Testing CTE WITH query execution ---")
    cte_query = """
    WITH genre_count AS (
        SELECT sk_genre_id, COUNT(*) as total FROM bridge_movie_genre GROUP BY sk_genre_id
    )
    SELECT * FROM genre_count LIMIT 3;
    """
    res = execute_query(cte_query)
    print("Status:", res["status"])
    print("Data:", res.get("data"))
