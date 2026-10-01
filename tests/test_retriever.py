import unittest
from src.tools.retriever import get_table_info, get_distinct_values, ALLOWED_TABLES


class TestRetrieverTools(unittest.TestCase):
    def test_get_table_info_includes_sample_data(self):
        info = get_table_info("dim_genres")
        self.assertIn("Table: dim_genres", info)
        self.assertIn("sk_genre_id", info)
        self.assertIn("nome_genero", info)
        self.assertIn("Sample Rows", info)

    def test_get_table_info_all_allowed(self):
        info = get_table_info()
        self.assertIn("Table: dim_movies", info)
        self.assertIn("Table: dim_genres", info)
        self.assertIn("Sample Rows", info)

    def test_get_table_info_untrusted_table(self):
        info = get_table_info("untrusted_table")
        self.assertIn("Error: Table 'untrusted_table' is not in the whitelist", info)

    def test_get_distinct_values_valid(self):
        values = get_distinct_values("dim_genres", "nome_genero")
        self.assertIsInstance(values, list)
        self.assertIn("Action", values)

    def test_get_distinct_values_with_search_term_parameterized(self):
        values = get_distinct_values("dim_genres", "nome_genero", search_term="Sci")
        self.assertIsInstance(values, list)
        self.assertIn("Science Fiction", values)

    def test_get_distinct_values_untrusted_table_whitelist(self):
        res = get_distinct_values("sqlite_master", "name")
        self.assertTrue(any("Error: Invalid or untrusted table_name" in str(x) for x in res))

    def test_get_distinct_values_invalid_column_regex(self):
        # Attempting SQL injection via column name
        res = get_distinct_values("dim_genres", "nome_genero; DROP TABLE dim_genres; --")
        self.assertTrue(any("Error: Invalid column_name format" in str(x) for x in res))

    def test_get_distinct_values_non_existent_column(self):
        res = get_distinct_values("dim_genres", "coluna_inexistente")
        self.assertTrue(any("does not exist in table" in str(x) for x in res))


if __name__ == "__main__":
    unittest.main()
