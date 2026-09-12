-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Fase 3: Gold — asset_daily_summary
-- MAGIC
-- MAGIC Downsamplea silver.crypto_prices (snapshots intradía) a un resumen diario tipo OHLC por activo.
-- MAGIC Full rebuild cada corrida — CREATE OR REPLACE TABLE.

-- COMMAND ----------

CREATE OR REPLACE TABLE crypto_lakehouse.gold.asset_daily_summary
COMMENT 'Resumen diario tipo OHLC por activo, downsampleado de silver.crypto_prices. Full rebuild cada corrida.'
AS
WITH windowed AS (
  SELECT
    asset_id,
    to_date(snapshot_ts) AS trade_date,
    current_price,
    market_cap,
    total_volume,
    FIRST_VALUE(current_price) OVER (
      PARTITION BY asset_id, to_date(snapshot_ts) ORDER BY snapshot_ts
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS price_open,
    LAST_VALUE(current_price) OVER (
      PARTITION BY asset_id, to_date(snapshot_ts) ORDER BY snapshot_ts
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS price_close,
    LAST_VALUE(rank_at_snapshot) OVER (
      PARTITION BY asset_id, to_date(snapshot_ts) ORDER BY snapshot_ts
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS rank_close
  FROM crypto_lakehouse.silver.crypto_prices
),
daily AS (
  SELECT
    asset_id,
    trade_date,
    ANY_VALUE(price_open)  AS price_open,
    ANY_VALUE(price_close) AS price_close,
    MIN(current_price)     AS price_min,
    MAX(current_price)     AS price_max,
    AVG(market_cap)         AS avg_market_cap,
    AVG(total_volume)       AS avg_total_volume,
    ANY_VALUE(rank_close)  AS rank_close,
    COUNT(*)                AS n_snapshots
  FROM windowed
  GROUP BY asset_id, trade_date
)
SELECT
  d.asset_id,
  a.symbol,
  a.name,
  d.trade_date,
  d.price_open,
  d.price_close,
  d.price_min,
  d.price_max,
  (d.price_close - d.price_open) / d.price_open AS price_change_pct,
  d.avg_market_cap,
  d.avg_total_volume,
  d.rank_close,
  d.n_snapshots
FROM daily d
LEFT JOIN crypto_lakehouse.silver.dim_asset a
  ON d.asset_id = a.asset_id AND a.is_current = true
ORDER BY d.trade_date, d.rank_close;

-- COMMAND ----------

-- cantidad de filas (debería ser ~25 activos × 1 día, con la data que tenemos hoy)
SELECT COUNT(*), COUNT(DISTINCT asset_id), COUNT(DISTINCT trade_date)
FROM crypto_lakehouse.gold.asset_daily_summary;

-- chequeo puntual: bitcoin
-- SELECT * FROM crypto_lakehouse.gold.asset_daily_summary WHERE asset_id = 'bitcoin';