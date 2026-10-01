"""
Security Guardrails for Text-to-SQL Agent.
Includes Regex Blocklist for DDL/DML prevention, CTE (WITH) & SELECT query validation,
trailing semicolon normalization, and system prompt guardrails.
"""

import re

# Regex pattern for forbidden DDL/DML keywords (case-insensitive with word boundaries)
FORBIDDEN_KEYWORDS_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|EXECUTE|REPLACE|CREATE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE
)

# Allowed read-only statement starting keywords
ALLOWED_START_KEYWORDS = {"SELECT", "WITH", "EXPLAIN"}


def validate_sql_security(query: str) -> None:
    """
    Validates a SQL query string against security guardrails.
    Allows SELECT and CTE (WITH ... AS) queries.
    Allows single or multiple trailing semicolons.
    Prohibits DDL/DML data manipulation and stacked multi-statement queries.
    
    Args:
        query: The SQL query string to validate.
        
    Raises:
        ValueError: If any security guardrail rule is violated.
    """
    if not query or not query.strip():
        raise ValueError("Security Error: Query string cannot be empty.")

    clean_query = query.strip()

    # 1. Validate starting keyword (must be SELECT, WITH, or EXPLAIN)
    first_word = clean_query.split()[0].upper() if clean_query.split() else ""
    # Strip any leading parentheses if present e.g. (SELECT ...)
    first_word = first_word.lstrip("(")
    
    if first_word not in ALLOWED_START_KEYWORDS:
        raise ValueError(
            f"Security Error: Query must begin with SELECT or WITH (CTE). Found starting command: [{first_word}]."
        )

    # 2. Check for forbidden DDL/DML keywords
    matches = FORBIDDEN_KEYWORDS_PATTERN.findall(clean_query)
    if matches:
        forbidden = ", ".join(sorted(set(m.upper() for m in matches)))
        raise ValueError(
            f"Security Error: Query blocked by DDL/DML Blocklist Guardrail. "
            f"Forbidden keyword(s) detected: [{forbidden}]. Only read-only queries are permitted."
        )

    # 3. Handle trailing semicolons & check for stacked multi-statement queries
    # Remove all trailing whitespace and semicolons
    without_trailing_semicolons = clean_query.rstrip().rstrip(";")
    
    # If a semicolon is still present inside the body, multiple statements are being attempted
    if ";" in without_trailing_semicolons:
        raise ValueError(
            "Security Error: Query blocked by Guardrail. Multiple stacked SQL statements are not allowed."
        )


# Guardrail Semântico de Prompt (System Prompt Directive)
SYSTEM_GUARDRAIL_PROMPT = (
    "Você é um assistente de leitura de dados focado exclusivamente em dados de filmes e audiovisual. "
    "Se o usuário solicitar qualquer ação de alteração de dados, deleção, criação de tabelas, "
    "ou fizer perguntas fora do escopo de análise de dados audiovisuais, recuse-se a responder."
)


if __name__ == "__main__":
    print("--- Testing validate_sql_security ---")
    valid_samples = [
        "SELECT * FROM dim_movies LIMIT 5;",
        "SELECT * FROM dim_movies;   ",
        "WITH top_genres AS (SELECT sk_genre_id FROM dim_genres) SELECT * FROM top_genres LIMIT 3;"
    ]
    for sample in valid_samples:
        try:
            validate_sql_security(sample)
            print(f"PASSED: {sample}")
        except ValueError as e:
            print(f"FAILED: {sample} -> {e}")
