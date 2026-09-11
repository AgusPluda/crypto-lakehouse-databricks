# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 2: Silver — dim_asset (SCD Type 2, versión manual)
# MAGIC
# MAGIC `bronze.prices_raw` → `silver.dim_asset`. Dimensión de membership en el top 25, versionada con MERGE.
# MAGIC Cada corrida compara el snapshot más reciente contra el estado activo de la dimensión.

# COMMAND ----------

from pyspark.sql import functions as F

BRONZE_TABLE = "crypto_lakehouse.bronze.prices_raw"
DIM_TABLE    = "crypto_lakehouse.silver.dim_asset"

# COMMAND ----------

latest_snapshot_ts = spark.table(BRONZE_TABLE).agg(F.max("snapshot_ts")).collect()[0][0]
print(f"snapshot más reciente: {latest_snapshot_ts}")

current_members = (
    spark.table(BRONZE_TABLE)
    .filter(F.col("snapshot_ts") == latest_snapshot_ts)
    .select(F.col("id").alias("asset_id"), "symbol", "name", "image")
    .dropDuplicates(["asset_id"])
)
current_members.createOrReplaceTempView("current_members")

print(f"activos en el snapshot: {current_members.count()}")

# COMMAND ----------

if not spark.catalog.tableExists(DIM_TABLE):
    bootstrap = current_members.withColumns({
        "valid_from": F.lit(latest_snapshot_ts),
        "valid_to": F.lit(None).cast("timestamp"),
        "is_current": F.lit(True)
    })
    bootstrap.write.mode("overwrite").saveAsTable(DIM_TABLE)
    print(f"dim_asset creada con {bootstrap.count()} activos")
else:
    print("dim_asset ya existe — se procesa con MERGE en la próxima celda")

# COMMAND ----------

if spark.catalog.tableExists(DIM_TABLE):
    diff_sql = f"""
    MERGE INTO {DIM_TABLE} AS tgt
    USING (
        -- activos a CERRAR: estaban activos y ya no están en el snapshot nuevo
        SELECT asset_id, NULL AS symbol, NULL AS name, NULL AS image,
               TIMESTAMP'{latest_snapshot_ts}' AS event_ts, 'CLOSE' AS action
        FROM {DIM_TABLE}
        WHERE is_current = true
          AND asset_id NOT IN (SELECT asset_id FROM current_members)

        UNION ALL

        -- activos a INSERTAR: están en el snapshot nuevo y no estaban activos
        SELECT asset_id, symbol, name, image,
               TIMESTAMP'{latest_snapshot_ts}' AS event_ts, 'INSERT' AS action
        FROM current_members
        WHERE asset_id NOT IN (SELECT asset_id FROM {DIM_TABLE} WHERE is_current = true)
    ) AS src
    ON tgt.asset_id = src.asset_id AND tgt.is_current = true AND src.action = 'CLOSE'
    WHEN MATCHED THEN
        UPDATE SET valid_to = src.event_ts, is_current = false
    WHEN NOT MATCHED AND src.action = 'INSERT' THEN
        INSERT (asset_id, symbol, name, image, valid_from, valid_to, is_current)
        VALUES (src.asset_id, src.symbol, src.name, src.image, src.event_ts, NULL, true)
    """
    spark.sql(diff_sql)
    print("MERGE ejecutado")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC     is_current, 
# MAGIC     COUNT(*)
# MAGIC FROM crypto_lakehouse.silver.dim_asset
# MAGIC GROUP BY is_current

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * 
# MAGIC FROM crypto_lakehouse.silver.dim_asset 
# MAGIC ORDER BY asset_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE crypto_lakehouse.silver.dim_asset IS 
# MAGIC 'Dimension de Membership top 25, versionada con MERGE, incremental de bronze.prices_raw a silver.dim_asset'