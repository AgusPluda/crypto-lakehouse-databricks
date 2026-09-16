-- Databricks notebook source
-- Consulta precio/variación de un activo por símbolo

CREATE OR REPLACE FUNCTION crypto_lakehouse.genai.get_asset_price(
  asset_symbol STRING COMMENT 'Símbolo de la criptomoneda en mayúsculas, ej. BTC, ETH, BCH'
)
RETURNS TABLE (
  symbol STRING,
  name STRING,
  current_price DOUBLE,
  price_change_percentage_24h DOUBLE,
  market_cap DOUBLE,
  rank_at_snapshot INT
)
COMMENT 'Devuelve el precio actual, la variación de 24hs y el market cap de una criptomoneda específica, buscándola por su símbolo (ej. BTC para Bitcoin).'
RETURN
  SELECT 
    symbol, 
    name, 
    current_price,
    price_change_percentage_24h, 
    market_cap, 
    rank_at_snapshot
  FROM crypto_lakehouse.gold.dim_asset_current
  WHERE UPPER(symbol) = UPPER(asset_symbol);

-- COMMAND ----------

-- Top N activos por price_change_pct descendente (gainers)

CREATE OR REPLACE FUNCTION crypto_lakehouse.genai.get_top_gainers(
    n_results INT COMMENT 'Número de activos a mostrar'
)
RETURNS TABLE (
    symbol STRING,
    name STRING,
    price_change_pct DOUBLE
)
COMMENT 'Devuelve los N activos con mayor variación de precio en los últimos 24hs, orden decendente (gainers).'
RETURN
  WITH ranked AS (
    SELECT 
        symbol,
        name, 
        price_change_pct,
        ROW_NUMBER() OVER (ORDER BY price_change_pct DESC) AS rn
    FROM crypto_lakehouse.gold.asset_daily_summary
  )
  SELECT 
    symbol,
    name, 
    price_change_pct
  FROM ranked
  WHERE rn <= n_results

-- COMMAND ----------

-- Top N activos por price_change_pct ascendente (losers)

CREATE OR REPLACE FUNCTION crypto_lakehouse.genai.get_top_losers(
    n_results INT COMMENT 'Número de activos a mostrar'
)
RETURNS TABLE (
    symbol STRING,
    name STRING,
    price_change_pct DOUBLE
)
COMMENT 'Devuelve los N activos con mayor variación de precio en los últimos 24hs, orden ascendente (losers).'
RETURN
    WITH ranked AS (
        SELECT 
            symbol,
            name, 
            price_change_pct,
            ROW_NUMBER() OVER (ORDER BY price_change_pct ASC) AS rn
        FROM crypto_lakehouse.gold.asset_daily_summary
    )
  SELECT 
    symbol,
    name, 
    price_change_pct
  FROM ranked
  WHERE rn <= n_results

-- COMMAND ----------

-- Estado de scraping de noticias por source (fuente)

CREATE OR REPLACE FUNCTION crypto_lakehouse.genai.news_pipeline_health()
RETURNS TABLE (
    source STRING,
    n_ok BIGINT,
    n_bloqueado BIGINT,
    n_error BIGINT,
    n_sin_contenido BIGINT
)
COMMENT 'Devuelve la cantidad de artículos de noticias por fuente según su resultado de scraping (exitoso, bloqueado, con error, o sin contenido extraído). Útil para evaluar qué tan confiable es cada fuente de noticias.'
RETURN
    SELECT source, n_ok, n_bloqueado, n_error, n_sin_contenido
    FROM crypto_lakehouse.gold.news_pipeline_health;