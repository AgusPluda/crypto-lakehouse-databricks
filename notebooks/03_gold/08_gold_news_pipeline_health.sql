-- Databricks notebook source
CREATE OR REPLACE TABLE crypto_lakehouse.gold.news_pipeline_health
COMMENT 'Reporte de la calidad de los datos scrapeados, agrupado por source'
AS
SELECT
  source,
  COUNT(*) AS total_articulos,
  SUM(CASE WHEN scrape_status = 'ok' THEN 1 ELSE 0 END) AS n_ok,
  SUM(CASE WHEN scrape_status = 'bloqueado' THEN 1 ELSE 0 END) AS n_bloqueado,
  SUM(CASE WHEN scrape_status = 'error' THEN 1 ELSE 0 END) AS n_error,
  SUM(CASE WHEN scrape_status = 'sin_contenido' THEN 1 ELSE 0 END) AS n_sin_contenido,
  ROUND(100.0 * SUM(CASE WHEN scrape_status = 'ok' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_scraped_ok
FROM crypto_lakehouse.silver.crypto_news
GROUP BY source
ORDER BY source;