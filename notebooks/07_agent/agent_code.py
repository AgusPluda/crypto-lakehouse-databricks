# Databricks notebook source
from databricks_langchain import (
    UCFunctionToolkit,
    VectorSearchRetrieverTool,
    ChatDatabricks,
)
from langgraph.prebuilt import create_react_agent
import mlflow

llm = ChatDatabricks(
    endpoint="databricks-meta-llama-3-3-70b-instruct",
    temperature=0.0,
)

uc_tool_names = [
    "crypto_lakehouse.genai.get_asset_price",
    "crypto_lakehouse.genai.get_top_gainers",
    "crypto_lakehouse.genai.get_top_losers",
    "crypto_lakehouse.genai.news_pipeline_health",
]
uc_toolkit = UCFunctionToolkit(function_names=uc_tool_names)

vs_tool = VectorSearchRetrieverTool(
    index_name="crypto_lakehouse.genai.news_chunks_index",
    num_results=4,
    query_type="HYBRID",
    tool_name="search_crypto_news",
    tool_description="Busca en el corpus de noticias cripto (artículos scrapeados de Cointelegraph y Decrypt) fragmentos de texto relevantes a una pregunta o tema.",
    columns=["chunk_text", "source", "link", "published_at"],
)

tools = uc_toolkit.tools + [vs_tool]

SYSTEM_PROMPT = """Sos un asistente experto en el mercado de criptomonedas. Tenés acceso a datos en tiempo real de precios (vía tools SQL) y a un corpus de noticias cripto (vía búsqueda semántica). Usá SIEMPRE las tools disponibles para responder con datos reales en vez de tu conocimiento general -- nunca inventes precios ni cifras. Si la pregunta es sobre noticias, citá la fuente (link) de cada dato que uses. Cuando cites una noticia, incluí el link completo entre paréntesis, no solo el nombre de la fuente. Si no tenés información suficiente con las tools, decilo explícitamente."""

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)

mlflow.models.set_model(agent)