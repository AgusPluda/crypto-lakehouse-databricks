-- Databricks notebook source
CREATE OR REPLACE TABLE crypto_lakehouse.gold.dim_asset_current
COMMENT 'Resumen del momento actual de los activos, desnormalizado'
AS
SELECT
  a.asset_id, a.symbol, a.name, a.image,
  p.current_price, p.market_cap, p.rank_at_snapshot,
  p.price_change_percentage_24h, p.ath, p.ath_change_percentage,
  p.snapshot_ts AS as_of
FROM crypto_lakehouse.silver.dim_asset a
JOIN crypto_lakehouse.silver.crypto_prices p
  ON a.asset_id = p.asset_id
 AND p.snapshot_ts = ( 
    SELECT MAX(snapshot_ts) 
    FROM crypto_lakehouse.silver.crypto_prices
 )
WHERE a.is_current = true
ORDER BY p.rank_at_snapshot;