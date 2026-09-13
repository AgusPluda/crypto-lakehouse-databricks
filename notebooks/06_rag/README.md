# Fase 6 — RAG

| paso | qué hace | tabla/artefacto |
|------|----------|-----------------|
| `11_chunk_news` | Trochea `silver.crypto_news` (sólo `scrape_status='ok'`) con `RecursiveCharacterTextSplitter` de LangChain | `genai.news_chunks` (368 chunks de 66 artículos, `delta.enableChangeDataFeed=true`) |
| Índice de Vector Search | `crypto_lakehouse.genai.news_chunks_index`, tipo Hybrid, embeddings con `databricks-gte-large-en`, sync Triggered, sobre el endpoint reusado `vector_search_endpoint` | en progreso — ver estado abajo |
| _pendiente_ | Chain de RAG con LangChain (`DatabricksVectorSearch` + `ChatDatabricks`), registrada en UC con alias `champion` | `genai.news_rag_chain` |

## Estado del índice (2026-09-13): sync fallando por cupo diario de Free Edition, no por config

Al crear el índice, la sync (que corre internamente como un pipeline) falló 3 veces seguidas con:

```
RESOURCE_EXHAUSTED: You've hit the limit for serverless compute for free usage.
Stop or delete existing serverless compute to free up capacity.
```

Se verificó que no había nada corriendo activamente (warehouse `STOPPED`, sin clusters, pipeline de
`dim_asset` en `IDLE`) — no es "algo quedó prendido", es el **cupo diario de compute serverless de la
cuenta** (Free Edition es serverless-only con cupos por cuenta; al excederlos, el compute queda
indisponible por el resto del día, según la [doc de límites de Free
Edition](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)). Se agotó entre
el notebook de chunking, el `ALTER TABLE` de retención, y los intentos de sync del índice, todos en la
misma sesión.

**No es un bug** (a diferencia de "Arclight" en Fase 2) — es un límite de uso esperable en un tier
gratis. Se resuelve solo al otro día cuando resetea el cupo. Pendiente: reintentar el sync del índice
(botón de sync/retry en la página del índice, o "Diagnose with Genie" → reintentar) sin tocar nada más
de la configuración, que ya está bien.

Nota al margen: la doc menciona que algunos límites de Free Edition se pueden aumentar verificando
identidad con LinkedIn — no evaluado, queda como opción si esto se repite seguido.
