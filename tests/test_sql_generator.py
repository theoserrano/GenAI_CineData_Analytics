"""
Unit and Integration Tests for SQL Generator Agent.
Includes offline Pydantic model validation and optional live API integration test.
"""

import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.models.schemas import SQLResult
from src.agents.sql_generator import sql_generator_agent, SQL_GENERATOR_SYSTEM_PROMPT
from src.tools.executor import execute_query


class TestSQLGenerator(unittest.TestCase):
    def test_sql_result_pydantic_model(self):
        """Offline validation of SQLResult Pydantic model structure."""
        data = SQLResult(
            reasoning="Busquei os valores de gênero 'Action' com get_distinct_values e testei a query com execute_query.",
            sql="SELECT m.titulo, f.lucro_total FROM dim_movies m JOIN fact_movies_performance f ON m.sk_movie_id = f.sk_movie_id LIMIT 5;",
            confidence=0.95
        )
        self.assertEqual(data.confidence, 0.95)
        self.assertIn("SELECT", data.sql)
        self.assertTrue(len(data.reasoning) > 0)

    def test_system_prompt_contains_workflow_and_business_rules(self):
        """Validates that system prompt contains strict workflow steps and business rules."""
        # Workflow tools
        self.assertIn("get_distinct_values", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("get_table_info", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("execute_query", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("Auto-Correção", SQL_GENERATOR_SYSTEM_PROMPT)

        # Business metrics & rules
        self.assertIn("fact_movies_performance", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("receita_total", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("lucro_total", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("COALESCE", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("bridge_movie_genre", SQL_GENERATOR_SYSTEM_PROMPT)
        self.assertIn("bridge_movie_person", SQL_GENERATOR_SYSTEM_PROMPT)

    def test_agent_initialization(self):
        """Validates that sql_generator_agent is properly instantiated."""
        self.assertIsNotNone(sql_generator_agent)


def run_live_test():
    """Runs a single live call against OpenRouter API to validate end-to-end integration and self-correction."""
    print("\n--- Running Live OpenRouter API Test for SQL Generator Agent ---")
    question = "Quais os 5 filmes com maior lucro total no catálogo?"
    print(f"User Query: {question}")
    
    try:
        result = sql_generator_agent.run_sync(question)
        sql_data: SQLResult = result.output
        
        print("\n--- Agent Response Received ---")
        print(f"Reasoning: {sql_data.reasoning}")
        print(f"Generated SQL: {sql_data.sql}")
        print(f"Confidence: {sql_data.confidence}")
        
        # Validate returned SQL execution
        exec_res = execute_query(sql_data.sql)
        print(f"Execution status: {exec_res['status']}")
        print(f"Rows returned: {exec_res.get('row_count')}")
        
        assert exec_res["status"] == "success", f"Generated SQL failed execution: {exec_res.get('error_message')}"
        assert 0.0 <= sql_data.confidence <= 1.0, "Confidence score out of range"
        print("\nLive SQL Generator Integration Test: PASSED! [OK]")
    except Exception as e:
        print(f"\nLive SQL Generator Integration Test FAILED [ERROR]: {e}")


if __name__ == "__main__":
    if "--live" in sys.argv:
        run_live_test()
    else:
        unittest.main()
