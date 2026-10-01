"""
Database Information Retriever Tools for PydanticAI Text-to-SQL Agent.
Provides schema inspection with sample data and SQL-injection-hardened column value lookups.
"""

import re
from typing import Any, Optional
from src.database import get_readonly_connection

# Whitelist of the 10 dimensional database tables for security hardening
ALLOWED_TABLES = {
    "dim_movies",
    "fact_movies_performance",
    "dim_genres",
    "dim_people",
    "dim_companies",
    "dim_reviews",
    "movie_reviews",
    "bridge_movie_genre",
    "bridge_movie_person",
    "bridge_movie_company",
}


def get_table_info(table_name: Optional[str] = None) -> str:
    """
    Retrieves database schema information AND sample rows (2-3 rows) for one or all allowed tables.
    
    Args:
        table_name: Optional name of a specific table. If None, returns info for all allowed tables.
        
    Returns:
        Formatted string containing table schemas, column data types, primary keys, and sample data rows.
    """
    conn = get_readonly_connection()
    try:
        cursor = conn.cursor()
        
        if table_name:
            if table_name not in ALLOWED_TABLES:
                return f"Error: Table '{table_name}' is not in the whitelist of allowed tables. Allowed tables: {sorted(list(ALLOWED_TABLES))}"
            tables = [table_name]
        else:
            tables = sorted(list(ALLOWED_TABLES))
            
        schema_info = []
        for table in tables:
            # 1. Schema info via PRAGMA table_info
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            if not columns:
                schema_info.append(f"Table '{table}' does not exist or has no columns.")
                continue
                
            col_descriptions = []
            col_names = []
            for col in columns:
                c_name = col["name"]
                c_type = col["type"]
                is_pk = " (PRIMARY KEY)" if col["pk"] else ""
                col_descriptions.append(f"  - {c_name}: {c_type}{is_pk}")
                col_names.append(c_name)
                
            # 2. Sample data rows (SELECT * FROM table LIMIT 3)
            cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
            sample_rows = cursor.fetchall()
            
            sample_str_lines = []
            if sample_rows:
                sample_str_lines.append("  Sample Rows (3 max):")
                for idx, row in enumerate(sample_rows, 1):
                    row_dict = {col_name: row[col_name] for col_name in col_names}
                    sample_str_lines.append(f"    Row {idx}: {row_dict}")
            else:
                sample_str_lines.append("  Sample Rows: [No data rows found]")

            table_block = (
                f"Table: {table}\n"
                f"Columns:\n" + "\n".join(col_descriptions) + "\n" +
                "\n".join(sample_str_lines)
            )
            schema_info.append(table_block)
            
        return "\n\n" + ("=" * 40) + "\n\n".join(schema_info)
    except Exception as e:
        return f"Error retrieving table info: {str(e)}"
    finally:
        conn.close()


def get_distinct_values(
    table_name: str,
    column_name: str,
    search_term: Optional[str] = None,
    limit: int = 20
) -> list[Any]:
    """
    Retrieves distinct values from a specific table column with strict identifier validation to assist in constructing accurate WHERE filters.
    
    Args:
        table_name: Name of the table (must be in ALLOWED_TABLES whitelist)
        column_name: Name of the column (alphanumeric and underscore only, verified against table schema)
        search_term: Optional filter string using SQL bind parameter LIKE ?
        limit: Maximum number of distinct values to return (default: 20)
        
    Returns:
        List of unique non-null values found in the target column.
    """
    # 1. Whitelist validation for table_name
    if table_name not in ALLOWED_TABLES:
        return [f"Error: Invalid or untrusted table_name '{table_name}'. Must be one of {sorted(list(ALLOWED_TABLES))}"]
        
    # 2. Strict regex check for column_name to prevent SQL identifier injection
    if not re.match(r"^[a-zA-Z0-9_]+$", column_name):
        return [f"Error: Invalid column_name format '{column_name}'. Only alphanumeric characters and underscores are allowed."]

    conn = get_readonly_connection()
    try:
        cursor = conn.cursor()
        
        # 3. Verify column existence in table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        valid_columns = [col["name"] for col in cursor.fetchall()]
        if column_name not in valid_columns:
            return [f"Error: Column '{column_name}' does not exist in table '{table_name}'. Valid columns: {valid_columns}"]
            
        # 4. Parameterized query execution
        if search_term:
            query = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} LIKE ? AND {column_name} IS NOT NULL LIMIT ?"
            cursor.execute(query, (f"%{search_term}%", limit))
        else:
            query = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT ?"
            cursor.execute(query, (limit,))
            
        results = [row[0] for row in cursor.fetchall()]
        return results
    except Exception as e:
        return [f"Error: {str(e)}"]
    finally:
        conn.close()


if __name__ == "__main__":
    print("--- Testing get_table_info('dim_genres') with sample rows ---")
    print(get_table_info("dim_genres"))
    print("\n--- Testing get_distinct_values with whitelist & regex checks ---")
    print(get_distinct_values("dim_genres", "nome_genero", search_term="Sci"))
