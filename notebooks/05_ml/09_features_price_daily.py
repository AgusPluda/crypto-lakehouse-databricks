# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 5: ML — Feature table de dirección de precio
# MAGIC
# MAGIC gold.asset_daily_summary → mlops.features_price_daily. Features del día anterior (LAG) para predecir
# MAGIC si el precio sube o baja el día siguiente. Requiere ≥2 días consecutivos por activo — hoy sólo hay 1,
# MAGIC la tabla queda vacía y es el resultado correcto.

# COMMAND ----------

# MAGIC %pip install databricks-feature-engineering

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import functions as F

fe = FeatureEngineeringClient()

GOLD_TABLE    = "crypto_lakehouse.gold.asset_daily_summary"
FEATURE_TABLE = "crypto_lakehouse.mlops.features_price_daily"

# COMMAND ----------

features_df = spark.sql(f"""
    WITH lagged AS (
        SELECT
            asset_id,
            trade_date,
            price_change_pct,
            LAG(price_close)      OVER (PARTITION BY asset_id ORDER BY trade_date) AS feature_price_close,
            LAG(rank_close)       OVER (PARTITION BY asset_id ORDER BY trade_date) AS feature_rank_close,
            LAG(avg_market_cap)   OVER (PARTITION BY asset_id ORDER BY trade_date) AS feature_avg_market_cap,
            LAG(avg_total_volume) OVER (PARTITION BY asset_id ORDER BY trade_date) AS feature_avg_total_volume,
            LAG(price_change_pct) OVER (PARTITION BY asset_id ORDER BY trade_date) AS feature_price_change_pct
        FROM {GOLD_TABLE}
    )
    SELECT
        asset_id,
        trade_date,
        feature_price_close,
        feature_rank_close,
        feature_avg_market_cap,
        feature_avg_total_volume,
        feature_price_change_pct,
        CASE WHEN price_change_pct > 0 THEN 1 ELSE 0 END AS target_price_up
    FROM lagged
    WHERE feature_price_close IS NOT NULL
""")

print(f"filas: {features_df.count()}")

# COMMAND ----------

if not spark.catalog.tableExists(FEATURE_TABLE):
    fe.create_table(
        name=FEATURE_TABLE,
        primary_keys=["asset_id", "trade_date"],
        df=features_df,
        description="Features con 1 dia de rezago (LAG) por activo + target de direccion del precio. "
                     "Requiere al menos 2 dias consecutivos por activo en gold.asset_daily_summary."
    )
    print("feature table creada")
else:
    fe.write_table(name=FEATURE_TABLE, df=features_df, mode="merge")
    print("feature table actualizada")

# COMMAND ----------

n = spark.table(FEATURE_TABLE).count()
print(f"filas en la feature table: {n}")
if n == 0:
    print("Esperable: sólo hay 1 día de historia en asset_daily_summary. Se resuelve solo cuando "
          "Fase 8 empiece a correr la ingesta con scheduling real y se acumulen días.")