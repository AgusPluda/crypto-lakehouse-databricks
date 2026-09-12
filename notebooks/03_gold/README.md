# Fase 3 — Gold

Marts de negocio, listos para consumir sin joins ni lógica extra. Full rebuild (`CREATE OR REPLACE
TABLE ... AS SELECT`) en cada corrida — a esta escala es más simple que una carga incremental y el
resultado siempre es consistente con el estado actual de Silver.

| notebook | fuente | tabla | qué es |
|----------|--------|-------|--------|
| `06_gold_asset_daily_summary` | `silver.crypto_prices` + `silver.dim_asset` | `gold.asset_daily_summary` | resumen diario tipo OHLC por activo (open/close/min/max, % de cambio, rank de cierre) — el backbone para el dashboard y las features de ML |
| `07_gold_dim_asset_current` | `silver.dim_asset` + `silver.crypto_prices` | `gold.dim_asset_current` | estado actual del top 25, desnormalizado — un solo `SELECT` sin tener que entender SCD2 |
| `08_gold_news_pipeline_health` | `silver.crypto_news` | `gold.news_pipeline_health` | mart operacional: % de artículos scrapeados con éxito por fuente — documenta el bloqueo de CoinDesk con números |

Consumidores: AI/BI Dashboard + Genie Space (Fase 4), features del modelo de ML (Fase 5), tools SQL
del agente (Fase 7).
