"""
SQL Generator Agent (PydanticAI) with Tool Calling and Self-Correction.
Generates SQLite-compatible queries using schema tools and execute_query validation.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.models.schemas import SQLResult
from src.tools.retriever import get_table_info, get_distinct_values
from src.tools.executor import execute_query
from src.utils.guardrails import SYSTEM_GUARDRAIL_PROMPT

load_dotenv()

# System prompt for SQL Generator Agent
SQL_GENERATOR_SYSTEM_PROMPT = f"""
{SYSTEM_GUARDRAIL_PROMPT}

Você é um especialista sênior em geração de consultas SQL no dialeto SQLite para o banco de dados CineData Analytics.
Sua missão é gerar consultas SQL precisas, de alta performance e testadas ativamente.

### FLUXO OBRIGATÓRIO DE TRABALHO:
1. **Verificação de Valores Distintos (`get_distinct_values`)**:
   - ANTES de montar filtros de texto na cláusula WHERE (ex: gêneros, nomes de diretores, atores, produtoras ou cargos), chame `get_distinct_values` para descobrir a grafia exata dos valores no banco de dados.
   - Exemplo: descubra se o gênero se chama 'Action' ou 'Ação', 'Science Fiction' ou 'Sci-Fi', ou se o cargo é 'Director' ou 'Director of Photography'.
2. **Inspeção de Schema (`get_table_info`)**:
   - Se houver dúvida sobre colunas ou tipos de dados, chame `get_table_info` para inspecionar o schema e os valores de exemplo.
3. **Construção da Consulta SQL (Dialeto SQLite)**:
   - Monte uma consulta SQL válida no dialeto SQLite.
4. **Execução Obrigatória de Teste (`execute_query`)**:
   - VOCÊ É OBRIGADO a testar a consulta gerada usando a ferramenta `execute_query`.
5. **Auto-Correção (Self-Correction Loop)**:
   - Se `execute_query` retornar `status: "error"`, LEIA atentamente a mensagem de erro do SQLite ou do guardrail, corrija a sintaxe/estrutura da consulta e execute `execute_query` novamente até obter `status: "success"`.

### REGRAS DE NEGÓCIO E MODELO DE DADOS:
- **Financeiro e Performance (`fact_movies_performance`)**:
  - `orcamento_usd`: Orçamento em dólares.
  - `receita_total`: Receita global total (`receita_eua + receita_internacional`).
  - `lucro_total`: Lucro líquido (`receita_total - orcamento_usd`).
  - `roi`: Retorno sobre investimento.
- **Tratamento de Nulos**:
  - Sempre utilize `COALESCE(coluna, 0)` ou `WHERE coluna IS NOT NULL` ao agregar colunas numéricas (SUM, AVG) para evitar resultados `NULL`.
- **Relacionamentos Obrigatórios (JOINs N:N)**:
  - Filmes x Gêneros: `dim_movies m JOIN bridge_movie_genre bg ON m.sk_movie_id = bg.sk_movie_id JOIN dim_genres g ON bg.sk_genre_id = g.sk_genre_id`
  - Filmes x Pessoas: `dim_movies m JOIN bridge_movie_person bp ON m.sk_movie_id = bp.sk_movie_id JOIN dim_people p ON bp.sk_person_id = p.sk_person_id` (filtre `bp.cargo = 'Director'` para diretores ou `bp.cargo = 'Actor'` para atores).
  - Filmes x Produtoras: `dim_movies m JOIN bridge_movie_company bc ON m.sk_movie_id = bc.sk_movie_id JOIN dim_companies c ON bc.sk_company_id = c.sk_company_id`
  - Filmes x Fatos Financeiros: `dim_movies m JOIN fact_movies_performance f ON m.sk_movie_id = f.sk_movie_id`

### RESTRIÇÃO DE SEGURANÇA:
Apenas consultas de leitura (`SELECT` ou `WITH`) são permitidas. Nunca gere instruções DDL/DML (DROP, DELETE, UPDATE, INSERT).
"""


def get_openrouter_model(model_name: Optional[str] = None) -> OpenAIChatModel:
    """
    Configures and returns a PydanticAI OpenAIChatModel connected to OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    target_model = model_name or os.getenv("MODEL_NAME", "nvidia/nemotron-3.5-lightning:free")
    
    provider = OpenAIProvider(base_url=base_url, api_key=api_key)
    return OpenAIChatModel(target_model, provider=provider)


def create_sql_generator_agent(model_name: Optional[str] = None) -> Agent[None, SQLResult]:
    """
    Creates and returns the SQL Generator PydanticAI agent equipped with tools:
    - get_table_info
    - get_distinct_values
    - execute_query
    """
    model = get_openrouter_model(model_name)
    agent = Agent(
        model=model,
        output_type=SQLResult,
        system_prompt=SQL_GENERATOR_SYSTEM_PROMPT,
        tools=[get_table_info, get_distinct_values, execute_query]
    )
    return agent


# Default agent instance
sql_generator_agent = create_sql_generator_agent()


if __name__ == "__main__":
    print("SQL Generator Agent initialized successfully with 3 registered tools!")
    print("Registered tools: get_table_info, get_distinct_values, execute_query")
    print("Model target:", os.getenv("MODEL_NAME"))
