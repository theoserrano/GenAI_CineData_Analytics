import unittest
from src.tools.executor import execute_query, validate_query_safety


class TestExecutorTools(unittest.TestCase):
    def test_execute_valid_select(self):
        result = execute_query("SELECT nome_genero FROM dim_genres LIMIT 2;")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["row_count"], 2)
        self.assertIn("nome_genero", result["columns"])

    def test_regex_blocklist_drop_table(self):
        result = execute_query("DROP TABLE dim_movies;")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "security_guardrail")
        self.assertIn("Security Error", result["error_message"])

    def test_regex_blocklist_delete(self):
        result = execute_query("DELETE FROM dim_genres WHERE 1=1;")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "security_guardrail")
        self.assertIn("Security Error", result["error_message"])

    def test_regex_blocklist_update(self):
        result = execute_query("UPDATE dim_movies SET ano_lancamento = 2026;")
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
