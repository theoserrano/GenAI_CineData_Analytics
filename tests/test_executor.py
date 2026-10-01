import unittest
from src.tools.executor import execute_query, HARD_MAX_ROWS_CEILING


class TestExecutorTools(unittest.TestCase):
    def test_execute_valid_select(self):
        result = execute_query("SELECT nome_genero FROM dim_genres LIMIT 2;")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["row_count"], 2)
        self.assertIn("nome_genero", result["columns"])

    def test_execute_cte_with_query(self):
        cte_query = "WITH temp_g AS (SELECT nome_genero FROM dim_genres) SELECT * FROM temp_g LIMIT 3;"
        result = execute_query(cte_query)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["data"]), 3)

    def test_execute_trailing_semicolon(self):
        result = execute_query("SELECT nome_genero FROM dim_genres LIMIT 1;   ")
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["data"]), 1)

    def test_hard_max_rows_ceiling(self):
        # Request 1000 rows, should be capped at HARD_MAX_ROWS_CEILING (500)
        result = execute_query("SELECT * FROM bridge_movie_genre", max_rows=1000)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["max_rows_applied"], HARD_MAX_ROWS_CEILING)
        self.assertLessEqual(result["row_count"], HARD_MAX_ROWS_CEILING)

    def test_regex_blocklist_drop_table(self):
        result = execute_query("DROP TABLE dim_movies;")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "security_guardrail")
        self.assertIn("Security Error", result["error_message"])

    def test_syntax_error_capture(self):
        result = execute_query("SELECT FROM WHERE;")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "sqlite_execution_error")
        self.assertIn("syntax error", result["error_message"])


if __name__ == "__main__":
    unittest.main()
