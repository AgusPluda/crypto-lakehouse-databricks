# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 2: Silver — Precios tipados
# MAGIC
# MAGIC `bronze.prices_raw` → `silver.crypto_prices`. Tabla de hechos: una fila por (asset_id, snapshot_ts).
# MAGIC Carga incremental: procesa sólo los snapshots que todavía no están en Silver.

# COMMAND ----------

from pyspark.sql import functions as F

BRONZE_TABLE = "crypto_lakehouse.bronze.prices_raw"
SILVER_TABLE = "crypto_lakehouse.silver.crypto_prices"

# COMMAND ----------

bronze = spark.table(BRONZE_TABLE)

if spark.catalog.tableExists(SILVER_TABLE):
    ya_procesados = spark.table(SILVER_TABLE).select("snapshot_ts").distinct()
    nuevos = bronze.join(ya_procesados, on="snapshot_ts", how="left_anti")
else:
    nuevos = bronze

n_snapshots = nuevos.select("snapshot_ts").distinct().count()
print(f"snapshots nuevos a procesar: {n_snapshots} | filas: {nuevos.count()}")

# COMMAND ----------

# Renombrar
nuevos = nuevos.withColumnsRenamed({"id": "asset_id", 
                                   "market_cap_rank": "rank_at_snapshot",
                                   "_ingested_at": "_bronze_ingested_at",
                                   "last_updated": "exchange_last_updated"})

# Tipar Fechas
nuevos = nuevos.withColumns({"atl_date": F.to_timestamp("atl_date"),
                            "ath_date": F.to_timestamp("ath_date"),
                            "exchange_last_updated": F.to_timestamp("exchange_last_updated")})

# Agregar ts de procesado
nuevos = nuevos.withColumn(("_silver_processed_at"), F.current_timestamp())

# Deduplicado
nuevos = nuevos.dropDuplicates(["asset_id", "snapshot_ts"])

# Select Final (drop de symbol, name, image, _payload, _source, los primeros 3 se pondran en dim_asset, los demas se descartan)
nuevos = nuevos.select("asset_id", 
                       "snapshot_ts", 
                       "rank_at_snapshot", 
                       "current_price", 
                       "market_cap", 
                       "fully_diluted_valuation", 
                       "total_volume", 
                       "high_24h", 
                       "low_24h", 
                       "price_change_24h", 
                       "price_change_percentage_24h", 
                       "market_cap_change_24h", 
                       "market_cap_change_percentage_24h", 
                       "circulating_supply", 
                       "total_supply", 
                       "max_supply", 
                       "ath", 
                       "ath_change_percentage", 
                       "ath_date", 
                       "atl", 
                       "atl_change_percentage", 
                       "atl_date", 
                       "exchange_last_updated", 
                       "_bronze_ingested_at", 
                       "_silver_processed_at")

# Silver Dataframe
df_silver = nuevos
df_silver.printSchema()

# COMMAND ----------

df_silver.write.mode("append").saveAsTable(SILVER_TABLE)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     snapshot_ts, 
# MAGIC     min(rank_at_snapshot), 
# MAGIC     max(rank_at_snapshot)
# MAGIC FROM crypto_lakehouse.silver.crypto_prices
# MAGIC GROUP BY snapshot_ts
# MAGIC ORDER BY snapshot_ts

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*),
# MAGIC     COUNT(ath_date)
# MAGIC FROM crypto_lakehouse.silver.crypto_prices

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     SUM(CASE WHEN current_price IS NULL THEN 1 END) AS cant_nulls
# MAGIC FROM crypto_lakehouse.silver.crypto_prices

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE crypto_lakehouse.silver.crypto_prices IS
# MAGIC 'Tabla de hechos: una fila por (asset_id, snapshot_ts), de bronze.prices_raw a silver.crypto_prices con carga incremental';