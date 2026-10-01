"""
End-to-End Pipeline Integration Tests.
Includes offline mocked tests (default) and optional live API end-to-end integration test (--live).
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.models.schemas import SchemaLink, SQLResult
from src.main import run_text_to_sql_pipeline, format_table_output


class TestEndToEndPipeline(unittest.TestCase):
    @patch("src.main.schema_linker_agent")
    @patch("src.main.sql_generator_agent")
    def test_run_text_to_sql_pipeline_offline_mocked(self, mock_sql_agent, mock_linker_agent):
        """Offline end-to-end pipeline test mocking LLM responses."""
        # 1. Setup mock outputs
        mock_linker_run = MagicMock()
        mock_linker_run.output = SchemaLink(
            tables=["dim_movies", "bridge_movie_genre", "dim_genres"],
            columns=["dim_movies.titulo", "dim_genres.nome_genero"],
            reasoning="Seleção para filtro por gênero de filme."
        )
        mock_linker_agent.run_sync.return_value = mock_linker_run

        mock_sql_run = MagicMock()
        mock_sql_run.output = SQLResult(
            reasoning="Testei com execute_query e a busca retornou os gêneros ordenados.",
            sql="SELECT nome_genero FROM dim_genres LIMIT 3;",
            confidence=0.98
        )
        mock_sql_agent.run_sync.return_value = mock_sql_run

        # 2. Run pipeline
        user_query = "Quais são os gêneros disponíveis no catálogo?"
        result = run_text_to_sql_pipeline(user_query)

        # 3. Assertions
        self.assertEqual(result["query"], user_query)
        self.assertIn("schema_link", result)
        self.assertIn("sql_result", result)
        self.assertIn("execution", result)

        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(result["execution"]["row_count"], 3)
        self.assertEqual(result["sql_result"]["confidence"], 0.98)

    def test_format_table_output(self):
        """Validates tabular output formatting helper."""
        data = [{"titulo": "Movie A", "ano": 2020}, {"titulo": "Movie B", "ano": 2021}]
        columns = ["titulo", "ano"]
        output = format_table_output(data, columns)
        self.assertIn("Movie A", output)
        self.assertIn("2020", output)


def run_live_test():
    """Runs a single live call against OpenRouter API to validate full end-to-end pipeline."""
    print("\n--- Running Live OpenRouter End-to-End Pipeline Test ---")
    question = "Quais são os 3 filmes com maior nota média no catálogo?"
    print(f"User Query: {question}")
    
    try:
        result = run_text_to_sql_pipeline(question)
        
        print("\n--- Pipeline Execution Completed Successfully ---")
        print(f"Schema Tables: {result['schema_link']['tables']}")
        print(f"SQL Result: {result['sql_result']['sql']}")
        print(f"Confidence: {result['sql_result']['confidence']}")
        print(f"Execution Status: {result['execution']['status']}")
        print(f"Rows Returned: {result['execution']['row_count']}")
        
        assert result["execution"]["status"] == "success", f"Pipeline failed execution: {result['execution'].get('error_message')}"
        assert result["execution"]["row_count"] > 0, "Should return at least 1 row"
        print("\nLive Pipeline Integration Test: PASSED! [OK]")
    except Exception as e:
        print(f"\nLive Pipeline Integration Test FAILED [ERROR]: {e}")


if __name__ == "__main__":
    if "--live" in sys.argv:
        run_live_test()
    else:
        unittest.main()
