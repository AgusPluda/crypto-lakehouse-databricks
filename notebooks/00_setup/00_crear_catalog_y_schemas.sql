-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Fase 0 — Catalog y schemas
-- MAGIC
-- MAGIC Crea el catalog `crypto_lakehouse` y sus 5 schemas (`bronze`, `silver`, `gold`, `mlops`, `genai`).
-- MAGIC
-- MAGIC Manteniendo la caracteristica de Idempotencia: se puede re-ejecutar sin problemas.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS crypto_lakehouse
  COMMENT 'Lakehouse de mercados cripto: precios de CoinGecko y noticias RSS. Medallion + ML + RAG + agente, gobernado en Unity Catalog.';

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS crypto_lakehouse.bronze
    COMMENT 'Payloads crudos de CoinGecko y RSS + metadata de ingesta';

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS crypto_lakehouse.silver
    COMMENT 'Hechos tipados, dim_asset (SCD2), noticias limpias y scrapeadas';

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS crypto_lakehouse.gold
    COMMENT 'Marts agregados para el dashboard y las features del ML';

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS crypto_lakehouse.mlops
    COMMENT 'Feature tables + Modelos registrados en el Model Registry de UC';

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS crypto_lakehouse.genai
    COMMENT 'Chunks de noticias + Índice de vector search + chain/agente registrados';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Verificación

-- COMMAND ----------

SHOW SCHEMAS IN crypto_lakehouse;

-- COMMAND ----------

DESCRIBE CATALOG EXTENDED crypto_lakehouse;
