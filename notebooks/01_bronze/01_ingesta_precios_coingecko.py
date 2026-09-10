# Databricks notebook source
# MAGIC %md
# MAGIC # Fase 1: Bronze — Ingesta de precios (CoinGecko)
# MAGIC
# MAGIC `GET /coins/markets` → top 25 por market cap (dinámico) → append a `crypto_lakehouse.bronze.prices_raw`.
# MAGIC Una fila por moneda por snapshot. Bronze inmutable: sólo append.

# COMMAND ----------

import json
import requests
from datetime import datetime, timezone
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

API_KEY = dbutils.secrets.get(scope="crypto_lakehouse", key="coingecko_demo_key")
BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"
BRONZE_TABLE = "crypto_lakehouse.bronze.prices_raw"

# COMMAND ----------

params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 25,
    "page": 1,
    "price_change_percentage": "24h",
}
headers = {"x-cg-demo-api-key": API_KEY}

resp = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
resp.raise_for_status()
payload = resp.json()

print(f"{len(payload)} monedas | #1: {payload[0]['id']} ({payload[0]['symbol']}) — ${payload[0]['current_price']:,}")
assert len(payload) == 25, f"Esperaba 25 monedas, llegaron {len(payload)}"

# COMMAND ----------

PRICE_SCHEMA = StructType([
    StructField("id", StringType(), True),
    StructField("symbol", StringType(), True),
    StructField("name", StringType(), True),
    StructField("image", StringType(), True),
    StructField("current_price", DoubleType(), True),
    StructField("market_cap", DoubleType(), True),
    StructField("market_cap_rank", LongType(), True),
    StructField("fully_diluted_valuation", DoubleType(), True),
    StructField("total_volume", DoubleType(), True),
    StructField("high_24h", DoubleType(), True),
    StructField("low_24h", DoubleType(), True),
    StructField("price_change_24h", DoubleType(), True),
    StructField("price_change_percentage_24h", DoubleType(), True),
    StructField("market_cap_change_24h", DoubleType(), True),
    StructField("market_cap_change_percentage_24h", DoubleType(), True),
    StructField("circulating_supply", DoubleType(), True),
    StructField("total_supply", DoubleType(), True),
    StructField("max_supply", DoubleType(), True),
    StructField("ath", DoubleType(), True),
    StructField("ath_change_percentage", DoubleType(), True),
    StructField("ath_date", StringType(), True),
    StructField("atl", DoubleType(), True),
    StructField("atl_change_percentage", DoubleType(), True),
    StructField("atl_date", StringType(), True),
    StructField("last_updated", StringType(), True),

    StructField("_payload", StringType(), True) # JSON crudo de la moneda
])

# COMMAND ----------

snapshot_ts = datetime.now(timezone.utc)

def to_row(d: dict) -> tuple:
    row = {f.name: d.get(f.name) for f in PRICE_SCHEMA.fields}
    row["_payload"] = json.dumps(d, separators=(",", ":"))
    return tuple(row[f.name] for f in PRICE_SCHEMA.fields)

records = [to_row(d) for d in payload]

df = (
    spark.createDataFrame(records, schema=PRICE_SCHEMA)
    .withColumn("snapshot_ts", F.lit(snapshot_ts))
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source", F.lit("coingecko/coins/markets"))
)

# df.printSchema()
display(df.select("market_cap_rank", "id", "symbol", "current_price", "market_cap", "snapshot_ts"))

# COMMAND ----------

df.write.mode("append").saveAsTable(BRONZE_TABLE)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT snapshot_ts, COUNT(*), MIN(market_cap_rank), MAX(market_cap_rank)
# MAGIC FROM crypto_lakehouse.bronze.prices_raw
# MAGIC GROUP BY snapshot_ts

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE crypto_lakehouse.bronze.prices_raw IS
# MAGIC 'Snapshots crudos del top 25 de CoinGecko /coins/markets, una fila por moneda por snapshot y append-only sin limpieza';