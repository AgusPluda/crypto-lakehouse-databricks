# Databricks notebook source
from operator import itemgetter
from databricks_langchain import DatabricksVectorSearch, ChatDatabricks
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import mlflow

vs = DatabricksVectorSearch(
    endpoint="vector_search_endpoint",
    index_name="crypto_lakehouse.genai.news_chunks_index",
    columns=["chunk_text", "source", "link", "published_at"],
)

retriever = vs.as_retriever(search_kwargs={"query_type": "HYBRID", "k": 4})

def format_docs(docs):
    return "\n\n".join(
        f"[Fuente: {d.metadata.get('source')} | {d.metadata.get('link')}]\n{d.page_content}"
        for d in docs
    )

llm = ChatDatabricks(
    endpoint="databricks-meta-llama-3-3-70b-instruct",
    temperature=0.0
)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Sos un asistente que responde preguntas sobre noticias cripto usando únicamente el contexto que te dan. Si el contexto no alcanza para responder, decilo explícitamente. Citá la fuente (el link) de cada dato que uses."),
    ("human", 
     "Contexto:\n{context}\n\nPregunta: {question}"),
])

chain = (
    {
        "context": itemgetter("question") | retriever | format_docs,
        "question": itemgetter("question"),
    }
    | prompt
    | llm
    | StrOutputParser()
)

mlflow.models.set_model(chain)