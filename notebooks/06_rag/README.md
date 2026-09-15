# Fase 6 — RAG

| paso | qué hace | tabla/artefacto |
|------|----------|-----------------|
| `11_chunk_news` | Trochea `silver.crypto_news` (sólo `scrape_status='ok'`) con `RecursiveCharacterTextSplitter` de LangChain | `genai.news_chunks` (368 chunks de 66 artículos, `delta.enableChangeDataFeed=true`) |
| Índice de Vector Search | `crypto_lakehouse.genai.news_chunks_index`, tipo Hybrid, embeddings con `databricks-gte-large-en`, sync Triggered, sobre el endpoint reusado `vector_search_endpoint` | ✅ sincronizado, `indexed_row_count=368`, `ready=true` |
| _pendiente_ | Chain de RAG con LangChain (`DatabricksVectorSearch` + `ChatDatabricks`), registrada en UC con alias `champion` | `genai.news_rag_chain` |

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
