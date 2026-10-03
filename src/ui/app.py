"""
Streamlit Web Interface for CineData Analytics Text-to-SQL Pipeline.
Provides a modern chat interface with Hero state, table badges, suggestion cards, 
progress status tracking, dataframe output, and technical SQL execution details.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import streamlit as st
from src.main import run_text_to_sql_pipeline

# -----------------------------------------------------------------------------
# Page Configuration & Modern Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CineData Analytics",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    /* Hide Streamlit header action anchor links */
    .stMarkdown a[href^="#"],
    [data-testid="stHeaderActionElements"],
    a.anchorjs-link {
        display: none !important;
    }

    /* Styling for Hero Header Icon */
    .hero-icon-container {
        display: flex;
        justify-content: center;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .hero-icon {
        background: linear-gradient(135deg, #6C3BAA 0%, #4A237B 100%);
        width: 72px;
        height: 72px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 10px 25px -5px rgba(108, 59, 170, 0.5);
        border: 1px solid rgba(179, 136, 255, 0.3);
        font-size: 36px;
        color: white;
    }
    .hero-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    
    /* Table badges styling */
    .table-badges-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin-bottom: 2rem;
    }
    .table-badge {
        background-color: rgba(108, 59, 170, 0.15);
        color: #D1B3FF;
        border: 1px solid rgba(108, 59, 170, 0.4);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        font-family: monospace;
    }
    
    /* Card buttons styling */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid rgba(108, 59, 170, 0.25);
        padding: 16px;
        text-align: left;
        background-color: #1A1D24;
        color: #FAFAFA;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #6C3BAA;
        background-color: rgba(108, 59, 170, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(108, 59, 170, 0.2);
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Constant Data
# -----------------------------------------------------------------------------
SUGGESTIONS = [
    {
        "title": "Top 10 filmes com maior receita",
        "description": "Quais filmes geraram o maior faturamento total no catálogo?",
        "icon": "📈",
        "query": "Top 10 filmes com maior receita",
    },
    {
        "title": "Lucro médio por gênero",
        "description": "Qual é a rentabilidade média calculada para cada gênero cinematográfico?",
        "icon": "📊",
        "query": "Lucro médio por gênero",
    },
    {
        "title": "Dupla ator-diretor mais frequente",
        "description": "Qual a dupla de ator e diretor que mais colaborou junta em filmes?",
        "icon": "🎬",
        "query": "Dupla ator-diretor que mais trabalhou junta",
    },
    {
        "title": "Top 5 filmes mais populares",
        "description": "Quais são os 5 filmes com os maiores índices de popularidade no catálogo?",
        "icon": "⭐",
        "query": "Top 5 filmes mais populares",
    },
]

AVAILABLE_TABLES = [
    "dim_movies",
    "fact_movies_performance",
    "dim_genres",
    "dim_people",
    "dim_companies",
    "dim_reviews",
]

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar options
with st.sidebar:
    st.title("🎬 CineData Analytics")
    st.caption("Assistente Inteligente Text-to-SQL")
    st.markdown("---")
    st.markdown("**Tabelas Disponíveis:**")
    for tbl in AVAILABLE_TABLES:
        st.markdown(f"- `{tbl}`")
    st.markdown("---")
    if st.button("🗑️ Limpar Histórico de Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------------------------------------------
# Hero / Empty State Screen
# -----------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero-icon-container">
            <div class="hero-icon">🎥</div>
        </div>
        <div style="text-align: center; margin-top: 10px; margin-bottom: 8px;">
            <h1 style="font-size: 2.3rem; font-weight: 700; color: #FFFFFF; margin: 0; padding: 0;">
                Por onde começamos?
            </h1>
        </div>
        <p class="hero-subtitle">Faça perguntas sobre o catálogo em linguagem natural</p>
    """,
        unsafe_allow_html=True,
    )

    # Badges/Tags for database tables
    badges_html = '<div class="table-badges-container">'
    for tbl in AVAILABLE_TABLES:
        badges_html += f'<span class="table-badge">🗂️ {tbl}</span>'
    badges_html += "</div>"
    st.markdown(badges_html, unsafe_allow_html=True)

    # Grid of Quick Suggestion Cards (2x2)
    st.markdown("##### 💡 Sugestões Rápidas de Análise")
    col1, col2 = st.columns(2)

    for idx, s in enumerate(SUGGESTIONS):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            button_label = f"{s['icon']} **{s['title']}**\n\n{s['description']}"
            if st.button(button_label, key=f"card_{idx}", use_container_width=True):
                st.session_state.pending_prompt = s["query"]
                st.rerun()

# -----------------------------------------------------------------------------
# Chat History Display
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and "result" in msg:
            res = msg["result"]
            exec_info = res.get("execution", {})

            # 1. Dataframe or status display
            if exec_info.get("status") == "success":
                data = exec_info.get("data", [])
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhum registro encontrado para esta consulta.")
            elif exec_info.get("status") == "refused":
                # Recusa graciosa por fora de escopo - a mensagem em linguagem natural já foi exibida
                pass
            else:
                err_msg = exec_info.get("error_message", "Erro desconhecido na execução da query.")
                st.error(f"Erro na execução SQL: {err_msg}")

            # 2. Technical details expander
            with st.expander("🔍 Detalhes Técnicos (SQL & Raciocínio)"):
                sql_info = res.get("sql_result", {})
                schema_info = res.get("schema_link", {})

                confidence = sql_info.get("confidence", 0)
                st.markdown(f"**Score de Confiança:** `{confidence * 100:.1f}%`")

                sql_code = sql_info.get("sql", "").strip()
                if not sql_code:
                    sql_code = "-- Consulta não gerada (Pergunta fora de escopo do catálogo)"
                st.markdown("**Consulta SQL Final Executada:**")
                st.code(sql_code, language="sql")

                st.markdown("**Raciocínio - Schema Linking:**")
                st.info(schema_info.get("reasoning", "Sem raciocínio disponível."))

                st.markdown("**Raciocínio - Geração & Auto-Correção SQL:**")
                st.info(sql_info.get("reasoning", "Sem raciocínio disponível."))

# -----------------------------------------------------------------------------
# Chat Input & Processing Flow
# -----------------------------------------------------------------------------
user_input = st.chat_input("Faça perguntas sobre o catálogo em linguagem natural...")

# Handle pending prompt from card clicks
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt
else:
    prompt = user_input

if prompt:
    # 1. Add user query to history and render
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant execution with st.status tracking
    with st.chat_message("assistant"):
        with st.status("🔍 Processando sua pergunta...", expanded=True) as status:
            st.write("Identificando tabelas (Schema Linking)...")
            st.write("Gerando e testando SQL (Auto-Correção)...")
            
            pipeline_result = run_text_to_sql_pipeline(prompt)
            
            status.update(
                label="✅ Processamento concluído!",
                state="complete",
                expanded=False,
            )

        exec_info = pipeline_result.get("execution", {})
        row_count = exec_info.get("row_count", 0)

        if exec_info.get("status") == "refused":
            response_text = exec_info.get(
                "message",
                "Olá! Sou o assistente da CineData Analytics focado em métricas e inteligência do catálogo cinematográfico (bilheteria, elenco, produtoras e avaliações). Não consigo responder a perguntas fora desse domínio. Experimente perguntar sobre os filmes mais lucrativos ou diretores mais bem avaliados!"
            )
        elif exec_info.get("status") == "success":
            response_text = f"Aqui estão os resultados para a pergunta **\"{prompt}\"** ({row_count} registros encontrados):"
        else:
            response_text = f"Não foi possível concluir a consulta para **\"{prompt}\"**."

        st.markdown(response_text)

        # Render dataframe if success
        if exec_info.get("status") == "success":
            data = exec_info.get("data", [])
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhum registro encontrado para esta consulta.")
        elif exec_info.get("status") == "error":
            st.error(f"Erro: {exec_info.get('error_message')}")

        # Render technical expander (showing agent reasoning for refusal if out of scope)
        with st.expander("🔍 Detalhes Técnicos (SQL & Raciocínio)"):
            sql_info = pipeline_result.get("sql_result", {})
            schema_info = pipeline_result.get("schema_link", {})

            confidence = sql_info.get("confidence", 0)
            st.markdown(f"**Score de Confiança:** `{confidence * 100:.1f}%`")

            sql_code = sql_info.get("sql", "").strip()
            if not sql_code:
                sql_code = "-- Consulta não gerada (Pergunta fora de escopo do catálogo)"
            st.markdown("**Consulta SQL Final Executada:**")
            st.code(sql_code, language="sql")

            st.markdown("**Raciocínio - Schema Linking:**")
            st.info(schema_info.get("reasoning", "Sem raciocínio disponível."))

            st.markdown("**Raciocínio - Geração & Auto-Correção SQL:**")
            st.info(sql_info.get("reasoning", "Sem raciocínio disponível."))

        # Save assistant message to history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_text,
                "result": pipeline_result,
            }
        )

        st.rerun()
