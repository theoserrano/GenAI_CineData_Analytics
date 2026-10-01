"""
CineData Analytics Text-to-SQL End-to-End Pipeline & CLI.
Orchestrates Schema Linking, Focused Context Assembly, SQL Generation with Self-Correction, and Execution.
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.agents.schema_linker import schema_linker_agent
from src.agents.sql_generator import sql_generator_agent
from src.models.schemas import SchemaLink, SQLResult
from src.tools.executor import execute_query

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


def run_text_to_sql_pipeline(user_query: str) -> Dict[str, Any]:
    """
    Executes the multi-step SOTA Text-to-SQL Pipeline:
    
    Etapa 1: Run Schema Linker Agent to map question -> SchemaLink (tables & columns).
    Etapa 2: Assemble focused context with selected tables and columns.
    Etapa 3: Run SQL Generator Agent to generate SQLResult, testing via execute_query with self-correction.
    Etapa 4: Consolidate & execute final query result.
    
    Args:
        user_query: User question in natural language.
        
    Returns:
        Consolidated dictionary with query, schema link info, SQL result, and query execution data.
    """
    # Etapa 1: Schema Linking
    linker_run = schema_linker_agent.run_sync(user_query)
    schema_link: SchemaLink = linker_run.output

    # Etapa 2: Focused Context Assembly
    focused_context = (
        f"PERGUNTA DO USUÁRIO: {user_query}\n\n"
        f"SCHEMA SELECIONADO PELO SCHEMA LINKER:\n"
        f"- Tabelas necessárias: {', '.join(schema_link.tables)}\n"
        f"- Colunas relevantes: {', '.join(schema_link.columns)}\n"
        f"- Raciocínio do Schema Linker: {schema_link.reasoning}\n\n"
        f"INSTRUÇÃO: Utilize o schema selecionado e suas pontes N:N (bridge_*) para construir a consulta SQL final no dialeto SQLite. "
        f"Lembre-se de verificar os valores exatos de texto com get_distinct_values e testar obrigatoriamente a query com execute_query."
    )

    # Etapa 3: Geração de SQL & Auto-Correção
    generator_run = sql_generator_agent.run_sync(focused_context)
    sql_result: SQLResult = generator_run.output

    # Etapa 4: Execução Final & Consolidação
    execution_data = execute_query(sql_result.sql)

    return {
        "query": user_query,
        "schema_link": {
            "tables": schema_link.tables,
            "columns": schema_link.columns,
            "reasoning": schema_link.reasoning,
        },
        "sql_result": {
            "sql": sql_result.sql,
            "reasoning": sql_result.reasoning,
            "confidence": sql_result.confidence,
        },
        "execution": execution_data,
    }


def format_table_output(data: list[dict[str, Any]], columns: list[str]) -> str:
    """Formats query results into a readable tabular ASCII layout."""
    if not data:
        return "[Nenhum registro encontrado]"
        
    if HAS_TABULATE:
        rows = [[row.get(col) for col in columns] for row in data]
        return tabulate(rows, headers=columns, tablefmt="psql")
    else:
        # Fallback simple table formatter
        lines = [" | ".join(columns), "-" * (len(" | ".join(columns)) + 4)]
        for row in data:
            lines.append(" | ".join(str(row.get(col, "")) for col in columns))
        return "\n".join(lines)


def print_pipeline_report(result: Dict[str, Any]) -> None:
    """Prints a friendly, structured report of the pipeline execution in CLI."""
    print("\n" + "=" * 70)
    print(" 🎬 CINEDATA ANALYTICS - RELATÓRIO TEXT-TO-SQL")
    print("=" * 70)
    print(f"\n❓ Pergunta: {result['query']}\n")

    # Schema Linker Report
    schema_info = result["schema_link"]
    print("🔍 ETAPA 1: SCHEMA LINKING")
    print(f"  • Tabelas Selecionadas: {', '.join(schema_info['tables'])}")
    print(f"  • Colunas: {', '.join(schema_info['columns'])}")
    print(f"  • Raciocínio: {schema_info['reasoning']}\n")

    # SQL Generator Report
    sql_info = result["sql_result"]
    print("⚙️  ETAPA 2: GERAÇÃO DE SQL & AUTO-CORREÇÃO")
    print(f"  • Score de Confiança: {sql_info['confidence'] * 100:.1f}%")
    print(f"  • Raciocínio: {sql_info['reasoning']}")
    print("\n💻 CONSULTA SQL EXECUTADA:")
    print("   " + sql_info['sql'].replace("\n", "\n   "))

    # Execution Data Report
    exec_info = result["execution"]
    print("\n📊 ETAPA 3: RESULTADOS DA CONSULTA")
    print(f"  • Status de Execução: {exec_info['status'].upper()}")

    if exec_info["status"] == "success":
        print(f"  • Total de Registros Obtidos: {exec_info['row_count']}")
        print("\n" + format_table_output(exec_info["data"], exec_info["columns"]))
    else:
        print(f"  • Erro de Execução: {exec_info.get('error_message')}")

    print("\n" + "=" * 70 + "\n")


def cli_main():
    """Interactive Command Line Interface for CineData Text-to-SQL Pipeline."""
    print("=========================================================")
    print(" 🚀 CineData Analytics Text-to-SQL Agent (Antigravity)")
    print("=========================================================")
    print(" Digite sua pergunta sobre filmes, bilheterias, diretores ou gêneros.")
    print(" Digite 'sair' ou 'exit' para encerrar.\n")

    while True:
        try:
            user_input = input("CineData SQL > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("sair", "exit", "quit"):
                print("Encerrando CineData Text-to-SQL. Até logo!")
                break

            print("\n⏳ Processando consulta com Agentes Inteligentes (OpenRouter PydanticAI)...")
            result = run_text_to_sql_pipeline(user_input)
            print_pipeline_report(result)

        except KeyboardInterrupt:
            print("\nOperação interrompida pelo usuário.")
            break
        except Exception as e:
            print(f"\n❌ Erro durante o processamento do pipeline: {e}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--cli":
        query = " ".join(sys.argv[1:])
        res = run_text_to_sql_pipeline(query)
        print_pipeline_report(res)
    else:
        cli_main()
