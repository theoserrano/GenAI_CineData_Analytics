import unittest
from src.utils.guardrails import validate_sql_security, SYSTEM_GUARDRAIL_PROMPT


class TestGuardrails(unittest.TestCase):
    def test_valid_select_and_cte_queries(self):
        valid_queries = [
            "SELECT * FROM dim_movies LIMIT 10;",
            "SELECT * FROM dim_movies;   ",
            "SELECT * FROM dim_movies;;;",
            "WITH top_genres AS (SELECT sk_genre_id FROM dim_genres) SELECT * FROM top_genres LIMIT 3;",
            "WITH cte AS (SELECT 1 AS col) SELECT * FROM cte;",
            "SELECT g.nome_genero, COUNT(*) FROM dim_genres g JOIN bridge_movie_genre b ON g.sk_genre_id = b.sk_genre_id GROUP BY g.nome_genero;"
        ]
        for q in valid_queries:
            try:
                validate_sql_security(q)
            except ValueError as e:
                self.fail(f"Valid query failed guardrail: {q}. Error: {e}")

    def test_forbidden_starting_keyword(self):
        invalid_starting = [
            "UPDATE dim_movies SET ano_lancamento=2020",
            "DELETE FROM dim_genres",
            "SHOW TABLES"
        ]
        for q in invalid_starting:
            with self.assertRaises(ValueError) as ctx:
                validate_sql_security(q)
            self.assertIn("Security Error", str(ctx.exception))

    def test_forbidden_ddl_dml_keywords(self):
        forbidden_queries = [
            "DROP TABLE dim_movies;",
            "DELETE FROM dim_genres WHERE 1=1;",
            "UPDATE fact_movies_performance SET receita_total = 0;",
            "INSERT INTO dim_people (nome_pessoa) VALUES ('Attacker');",
            "ALTER TABLE dim_movies ADD COLUMN test VARCHAR(10);",
            "TRUNCATE TABLE dim_reviews;",
            "EXEC xp_cmdshell('dir');",
            "VACUUM;"
        ]
        for q in forbidden_queries:
            with self.assertRaises(ValueError) as ctx:
                validate_sql_security(q)
            self.assertIn("Security Error", str(ctx.exception))

    def test_stacked_queries_injection(self):
        stacked_query = "SELECT * FROM dim_genres; SELECT * FROM dim_movies;"
        with self.assertRaises(ValueError) as ctx:
            validate_sql_security(stacked_query)
        self.assertIn("stacked SQL statements", str(ctx.exception))

    def test_empty_query(self):
        with self.assertRaises(ValueError):
            validate_sql_security("")
        with self.assertRaises(ValueError):
            validate_sql_security("   ")

    def test_query_sanitization(self):
        noisy_queries = [
            "```sql\nSELECT * FROM dim_movies LIMIT 5;\n```",
            "```\n-- Comentário inicial\nSELECT * FROM dim_movies LIMIT 5;\n```",
            "-- Comentário de cabeçalho\n-- Outra linha\nSELECT * FROM dim_movies LIMIT 5;",
            "...\n-- Comentário com reticências\nWITH top_m AS (SELECT * FROM dim_movies) SELECT * FROM top_m;",
            "   \n\n   ```sql\n   SELECT * FROM dim_genres;\n   ```  "
        ]
        for q in noisy_queries:
            try:
                cleaned = validate_sql_security(q)
                self.assertTrue(cleaned.startswith("SELECT") or cleaned.startswith("WITH"))
            except ValueError as e:
                self.fail(f"Sanitizer failed for query: {q}. Error: {e}")

    def test_system_prompt_guardrail_present(self):
        self.assertIn("assistente de leitura de dados", SYSTEM_GUARDRAIL_PROMPT)
        self.assertIn("recuse-se a responder", SYSTEM_GUARDRAIL_PROMPT)


if __name__ == "__main__":
    unittest.main()
