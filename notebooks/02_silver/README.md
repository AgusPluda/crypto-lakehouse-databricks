# Fase 2 — Silver

Datos tipados, limpios y modelados. De esta capa para abajo todo se junta por `asset_id`.

| notebook | fuente | tabla | notas |
|----------|--------|-------|-------|
| `03_silver_crypto_prices` | `bronze.prices_raw` | `silver.crypto_prices` | tabla de hechos, 1 fila por (`asset_id`, `snapshot_ts`); carga incremental por anti-join sobre `snapshot_ts` |
| `04_silver_dim_asset_merge` | `bronze.prices_raw` | `silver.dim_asset` | dimensión SCD Type 2 de membership en el top 25, **versión manual**: compara el snapshot más reciente contra el estado activo con un `MERGE` de cerrar+insertar en un solo statement |
| _pendiente_ | `bronze.prices_raw` | `silver.dim_asset` | misma dimensión, **versión declarativa**: `AUTO CDC ... STORED AS SCD TYPE 2` como Lakeflow Declarative Pipeline (recurso aparte de un notebook) |
| _pendiente_ | `bronze.news_raw` | `silver.crypto_news` | dedup por `link`, limpieza de HTML, parseo de fechas, y scraping del artículo completo para el corpus del RAG |
