# Fase 8 — Orquestación

La orquestación vive enteramente en **Databricks Workflows (Jobs)**, no en notebooks — esta carpeta
solo documenta el diseño. No hay código nuevo: cada task de cada Job apunta a un notebook ya
existente de las fases anteriores (`01_bronze/`, `02_silver/`, `03_gold/`, `06_rag/`).

## Los 3 Jobs

| Job | Tasks (en orden) | Trigger |
|-----|-------------------|---------|
| `crypto_prices_pipeline` | `ingest_prices` → (`transform_crypto_prices` + `transform_dim_asset`, en paralelo) → `gold_dim_asset_current` | cron, cada 30 min |
| `crypto_news_pipeline` | `ingest_news` → `transform_crypto_news` → `gold_news_pipeline_health` → `chunk_news` → `check_new_chunks` → `sync_vector_index` (condicional) | cron, `0 10 3,15 * * ?` (3:10 AM y 15:10 PM) |
| `crypto_gold_daily_trigger` | `asset_daily_summary` → `build_price_features` | cron, `0 15 0 * * ?` (00:15 AM) |

Todas las tasks usan **Source: Workspace** (ruta `/Repos/<usuario>/crypto-lakehouse-databricks/notebooks/...`),
no Git provider: el warning de Databricks sobre "Local repository" al usar Git source llevó a
usar Workspace en todos los Jobs.

## Decisión de diseño: tasks encadenadas dentro de un Job, no Jobs separados

Se evaluaron dos formas de encadenar fases:

- **Opción A (elegida):** agregar cada fase como una task nueva dentro del mismo Job, con
  **Depends on** apuntando a la task anterior. Nativo, sin indirección — Databricks solo corre una
  task si la que depende de ella terminó bien.
- **Opción B (descartada):** un Job por fase, encadenados entre sí con una task tipo **Run Job**
  que dispara el Job siguiente. Mantiene cada fase como una entidad separada en la lista de Jobs
  (mejor para verlos sueltos), pero agrega un nivel de indirección innecesario para este proyecto.

Se priorizó simplicidad (Opción A) sobre separación visual — el gráfico de dependencias dentro de
un mismo Job ya deja clara la estructura bronze→silver→gold→genai.

**Gold se separó por frecuencia, no por origen de datos.** `dim_asset_current` depende de datos de
precios (frecuentes) y se ejecuta encadenado dentro de `crypto_prices_pipeline`. En cambio
`asset_daily_summary` es conceptualmente un agregado diario — aunque también toma datos de precios,
recalcularlo cada 30 min sería redundante — por eso vive en su propio Job (`crypto_gold_daily_trigger`)
con cron propio en vez de encadenado a la cadencia de Bronze.

**Features de ML encadenadas al track diario.** `build_price_features`
(`05_ml/09_features_price_daily`) depende de `asset_daily_summary`: lee la tabla Gold ya reconstruida
y actualiza `mlops.features_price_daily`. Sin esta task la feature table quedaba congelada en la
última corrida manual (los notebooks de entrenamiento veían 2 días de historia cuando Gold tenía 8).
El Job conserva el nombre porque sigue siendo el track diario que arranca en Gold.

`asset_daily_summary` solo incluye **días cerrados** (`WHERE to_date(snapshot_ts) < current_date()`,
en UTC): el rebuild de las 00:15 no mete el día en curso, que tendría solo unos pocos snapshots.

## Ingesta de noticias: doble turno diario

`bronze_news` pasó de 1x/día a **2x/día** (3:10 AM y 15:10 PM) para noticias más frescas, sin costo
de cómputo relevante — la ingesta es liviana (~1 min por corrida) y correrla el doble sigue siendo
marginal frente al resto del sistema. Un solo trigger cron con múltiples horas
(`0 10 3,15 * * ?`, sintaxis Quartz) cubre ambos horarios sin necesitar dos triggers separados
(Databricks Jobs solo admite un trigger de schedule por Job).

## Sync condicional del índice de Vector Search

El índice `genai.news_chunks_index` es `pipeline_type=TRIGGERED` — no se sincroniza solo, necesita
un llamado explícito. Correrlo sin noticias nuevas no rompe nada, pero es innecesario. Se armó un
corte condicional con dos piezas:

1. **`11_chunk_news`** ya filtraba de forma incremental (`left_anti` join contra `genai.news_chunks`
   por `link`), así que nunca reprocesa ni duplica — pero además ahora expone la cantidad de chunks
   nuevos generados vía **Task Values**:
   ```python
   dbutils.jobs.taskValues.set(key="new_chunks_count", value=len(records))
   ```
   (no `dbutils.notebook.exit()` — ese valor solo lo puede leer otro notebook llamado con
   `dbutils.notebook.run()`, no una condición de Job).
2. **`check_new_chunks`**, una task de tipo **Condition**, evalúa
   `{{tasks.chunk_news.values.new_chunks_count}} > 0`. `sync_vector_index` depende de la rama
   `True` de esa condición — si no hay chunks nuevos, la task queda **Excluded** y el índice no se
   toca.

Verificado en producción: una corrida sin noticias nuevas excluyó correctamente `sync_vector_index`
(mensaje de la UI: *"Excluded because its conditional dependency on check_new_chunks was not met"*).

## `sync_vector_index`: WorkspaceClient en vez de VectorSearchClient

`13_sync_vector_index` usa `databricks.sdk.WorkspaceClient` (preinstalado en todo compute, sin
`%pip install`) en vez de `databricks.vector_search.client.VectorSearchClient` (paquete separado
`databricks-vectorsearch`, no preinstalado). Para una task dentro de un Job que corre 2x/día,
evitar el `%pip install` + `restartPython()` en cada corrida ahorra tiempo de cómputo:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.vector_search_indexes.sync_index(index_name="crypto_lakehouse.genai.news_chunks_index")
```

## Cupo de cómputo diario

Referencia real medida en este proyecto:

- `crypto_prices_pipeline`: ~1 min por corrida × 48 corridas/día ≈ 48 min/día.
- `crypto_news_pipeline`: ~3 min por corrida × 2 corridas/día ≈ 6 min/día (menos aún cuando
  `sync_vector_index` se excluye por la condición).
- `crypto_gold_daily_trigger`: ~19 seg × 1 corrida/día antes de sumar `build_price_features`,
  despreciable. Un run de prueba con la task nueva tardó ~7 min, casi todo espera de cómputo en
  cola (Free Edition), no procesamiento.

Total holgadamente por debajo del cupo diario de compute serverless de Free Edition, incluso sumando
el resto del sistema (dashboard en modo live, agente ya deployado sin necesitar redeploy periódico).

## Lineage

Catalog Explorer → cualquier tabla Gold o el índice `genai.news_chunks_index` → pestaña **Lineage**
muestra el grafo completo bronze→silver→gold→genai, capturado automáticamente a partir de las
corridas de estos Jobs — sin necesitar documentarlo a mano.
