"""
Unit and Integration Tests for Schema Linker Agent.
Includes offline Pydantic model validation and optional live API integration test.
"""

import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.models.schemas import SchemaLink
from src.agents.schema_linker import schema_linker_agent, SCHEMA_LINKER_SYSTEM_PROMPT


class TestSchemaLinker(unittest.TestCase):
    def test_schema_link_pydantic_model(self):
        """Offline validation of SchemaLink Pydantic output model structure."""
        data = SchemaLink(
            tables=["dim_movies", "bridge_movie_genre", "dim_genres"],
            columns=["dim_movies.titulo", "dim_genres.nome_genero"],
            reasoning="Para relacionar filmes e seus gêneros, a tabela bridge_movie_genre é obrigatória."
        )
        self.assertEqual(len(data.tables), 3)
        self.assertIn("bridge_movie_genre", data.tables)
        self.assertEqual(len(data.columns), 2)
        self.assertTrue(len(data.reasoning) > 0)

    def test_system_prompt_contains_10_tables_and_bridge_rules(self):
        """Validates that system prompt lists all 10 dimensional tables and bridge relationship instructions."""
        expected_tables = [
            "dim_movies",
            "fact_movies_performance",
            "dim_genres",
            "dim_people",
            "dim_companies",
            "dim_reviews",
            "movie_reviews",
            "bridge_movie_genre",
            "bridge_movie_person",
            "bridge_movie_company"
        ]
        for table in expected_tables:
            self.assertIn(table, SCHEMA_LINKER_SYSTEM_PROMPT)

        # Mandatory bridge relationship rules
        self.assertIn("bridge_movie_genre", SCHEMA_LINKER_SYSTEM_PROMPT)
        self.assertIn("bridge_movie_person", SCHEMA_LINKER_SYSTEM_PROMPT)
        self.assertIn("bridge_movie_company", SCHEMA_LINKER_SYSTEM_PROMPT)
        self.assertIn("INSTRUÇÃO RÍGIDA DE SEGURANÇA", SCHEMA_LINKER_SYSTEM_PROMPT)


def run_live_test():
    """Runs a single live call against OpenRouter API to validate end-to-end integration."""
    print("\n--- Running Live OpenRouter API Test for Schema Linker Agent ---")
    question = "Qual é o orçamento total e a receita dos filmes do gênero Ação?"
    print(f"User Query: {question}")
    
    try:
        result = schema_linker_agent.run_sync(question)
        schema_data: SchemaLink = result.output
        
        print("\n--- Agent Response Received ---")
        print(f"Tables selected: {schema_data.tables}")
        print(f"Columns selected: {schema_data.columns}")
        print(f"Reasoning: {schema_data.reasoning}")
        
        # Check basic expectations
        assert any("dim_movies" in t for t in schema_data.tables), "Should include dim_movies"
        assert any("dim_genres" in t for t in schema_data.tables), "Should include dim_genres"
        assert any("bridge_movie_genre" in t for t in schema_data.tables), "Should include bridge_movie_genre"
        print("\nLive Integration Test: PASSED! [OK]")
    except Exception as e:
        print(f"\nLive Integration Test FAILED [ERROR]: {e}")


if __name__ == "__main__":
    if "--live" in sys.argv:
        run_live_test()
    else:
        unittest.main()
