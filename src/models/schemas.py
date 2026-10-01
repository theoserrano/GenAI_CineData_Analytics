"""
Pydantic Schemas for Text-to-SQL Agent Pipeline.
Defines structured output types for Schema Linking and SQL Generation.
"""

from pydantic import BaseModel, Field


class SchemaLink(BaseModel):
    """
    SchemaLink output structure representing the target tables and columns
    selected by the Schema Selector agent for a given user query.
    """
    tables: list[str] = Field(
        description="Lista de nomes de tabelas necessárias para responder à pergunta (ex: ['dim_movies', 'bridge_movie_genre', 'dim_genres'])"
    )
    columns: list[str] = Field(
        description="Lista de colunas necessárias identificadas no formato 'tabela.coluna' ou 'coluna'"
    )
    reasoning: str = Field(
        description="Justificativa lógica da escolha das tabelas e colunas, incluindo o mapeamento dos relacionamentos N:N via tabelas bridge_*"
    )
