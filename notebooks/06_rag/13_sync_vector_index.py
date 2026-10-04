# Databricks notebook source
# MAGIC %md
# MAGIC # Fase 8: Orquestación — Sync del índice de Vector Search
# MAGIC
# MAGIC Task final de `crypto_news_pipeline`. Sincroniza `genai.news_chunks_index` con los chunks nuevos de
# MAGIC `genai.news_chunks`. Corre sólo si `check_new_chunks` (`new_chunks_count > 0`) da `True`; si no hay
# MAGIC chunks nuevos la task queda Excluded y el índice no se toca.
# MAGIC
# MAGIC Usa `WorkspaceClient` (preinstalado en todo compute) en vez de `VectorSearchClient`, que obligaría a
# MAGIC hacer `%pip install` + `restartPython()` en cada corrida.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

INDEX_NAME = "crypto_lakehouse.genai.news_chunks_index"

w = WorkspaceClient()
w.vector_search_indexes.sync_index(index_name=INDEX_NAME)
print(f"Sync disparado para {INDEX_NAME}")

# COMMAND ----------

# El sync es asíncrono (índice Triggered): se informa el estado actual sin esperar a que termine.
index = w.vector_search_indexes.get_index(index_name=INDEX_NAME)
print(f"ready={index.status.ready} | indexed_row_count={index.status.indexed_row_count}")
