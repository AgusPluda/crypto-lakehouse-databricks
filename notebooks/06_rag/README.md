# Fase 6 — RAG

| paso | qué hace | tabla/artefacto |
|------|----------|-----------------|
| `11_chunk_news` | Trochea `silver.crypto_news` (sólo `scrape_status='ok'`) con `RecursiveCharacterTextSplitter` de LangChain | `genai.news_chunks` (368 chunks de 66 artículos, `delta.enableChangeDataFeed=true`) |
| Índice de Vector Search | `crypto_lakehouse.genai.news_chunks_index`, tipo Hybrid, embeddings con `databricks-gte-large-en`, sync Triggered, sobre el endpoint reusado `vector_search_endpoint` | ✅ sincronizado, `indexed_row_count=368`, `ready=true` |
| `chain_code` | Chain de RAG con LangChain (LCEL): `DatabricksVectorSearch` como retriever (`query_type="HYBRID"`, k=4) + `ChatDatabricks` (`databricks-meta-llama-3-3-70b-instruct`) + prompt con instrucción de citar fuentes. Empaquetada como **Models from Code** (`mlflow.models.set_model`) porque el retriever tiene una conexión viva no picklable | registrada en UC con alias `champion` |
| `12_rag_chain_news` | Driver liviano: loguea `chain_code.py` con `mlflow.langchain.log_model`, registra en UC, carga el modelo registrado para probar, y setea el alias `champion` | `genai.news_rag_chain` (v2 = `champion`) |

## Chain de RAG: registrada y verificada (2026-09-14)

`mlflow.langchain.autolog()` deja traceada cada invocación en la MLflow Trace UI — se pueden ver los 4
pasos de la chain (retriever → format_docs → prompt → llm → parser) con inputs/outputs, latencia y
costo estimado de cada uno. Dos casos de prueba verificados:

- **Pregunta sin cobertura en el corpus** ("¿Qué pasó con Bitcoin Cash en las últimas 24hs?"): la chain
  respondió que el contexto no alcanza, en vez de inventar — el system prompt le pide explícitamente
  avisar cuando no tiene información suficiente.
- **Pregunta con cobertura** ("¿Qué se dice sobre Bitcoin?"): recuperó 3 chunks relevantes de 3
  artículos distintos y respondió citando la URL fuente de cada dato.

Registrada en Unity Catalog como `crypto_lakehouse.genai.news_rag_chain`, alias `champion` en la
versión 2 (la que se probó con éxito vía `mlflow.langchain.load_model(...)` después de loguearla).

## Estado del índice: sincronizado (2026-09-14)

Al crear el índice el 2026-09-13, la sync (que corre internamente como un pipeline) falló 3 veces
seguidas con `RESOURCE_EXHAUSTED: You've hit the limit for serverless compute for free usage` — el
**cupo diario de compute serverless de Free Edition**, no un bug ni un error de config (se verificó que
no había nada corriendo activamente: warehouse `STOPPED`, sin clusters, pipeline de `dim_asset` en
`IDLE`). Al otro día, con el cupo reseteado, se disparó un nuevo update del mismo pipeline
(`databricks pipelines start-update`) sin tocar la configuración y sincronizó a éxito en ~7 minutos
(`WAITING_FOR_RESOURCES` → `INITIALIZING` → `RUNNING` → `COMPLETED`).

Nota al margen: la doc menciona que algunos límites de Free Edition se pueden aumentar verificando
identidad con LinkedIn — no aplica a este caso (el usuario no es elegible), quedó descartado como vía.
