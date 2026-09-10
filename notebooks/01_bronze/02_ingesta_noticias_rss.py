# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 1: Bronze — Ingesta de noticias (RSS)
# MAGIC
# MAGIC 3 feeds (CoinDesk, Cointelegraph, Decrypt) → append a `crypto_lakehouse.bronze.news_raw`.
# MAGIC Una fila por entry por corrida. Sin deduplicar: eso es Silver.

# COMMAND ----------

# MAGIC %pip install feedparser
# MAGIC %restart_python

# COMMAND ----------

import json
import requests
import feedparser
from datetime import datetime, timezone
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
}
BRONZE_TABLE = "crypto_lakehouse.bronze.news_raw"
USER_AGENT = "crypto-lakehouse-databricks (portfolio project)"

# COMMAND ----------

def fetch_feed(source: str, url: str) -> list[dict]:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    if parsed.bozo:
        print(f"Warning! {source}: feed malformado — {parsed.bozo_exception}")
    print(f"  {source}: {len(parsed.entries)} entries")
    return parsed.entries

# print(json.dumps(entries[0], default=str, indent=2)[:1200])

# COMMAND ----------

NEWS_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("guid", StringType(), True),
    StructField("title", StringType(), True),
    StructField("link", StringType(), True),
    StructField("summary", StringType(), True),
    StructField("author", StringType(), True),
    StructField("tags", StringType(), True),
    StructField("published_raw", StringType(), True),
    
    StructField("_payload", StringType(), True) # JSON crudo de la noticia
])

# COMMAND ----------

ingest_run_ts = datetime.now(timezone.utc)

def to_row(source, entry: dict) -> tuple:
    row = {
        "source": source,
        "guid": entry.get("id"),
        "title": entry.get("title"),
        "link": entry.get("link"),
        "summary": entry.get("summary") or None,
        "author": entry.get("author"),
        "tags": json.dumps(entry.get("tags"), default=str) if entry.get("tags") else None,
        "published_raw": entry.get("published"),
    }
    row["_payload"] = json.dumps(entry, separators=(",", ":"), default=str)
    return tuple(row[f.name] for f in NEWS_SCHEMA.fields)

records = []

for source, url in FEEDS.items():
    for entry in fetch_feed(source, url):
        records.append(to_row(source, entry)) # una fila -> to_row(source, entry)

df = (
    spark.createDataFrame(records, schema=NEWS_SCHEMA)
    .withColumn("ingest_run_ts", F.lit(ingest_run_ts))
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source", F.lit("rss"))
)

df.printSchema()
# display(df.select("source", "title", "published_raw", "_payload"))

# COMMAND ----------

df.write.mode("append").saveAsTable(BRONZE_TABLE)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC     source,
# MAGIC     COUNT(*) AS filas,
# MAGIC     COUNT(DISTINCT link) AS links_unicos,
# MAGIC     SUM(CASE WHEN summary IS NULL THEN 1 ELSE 0 END) AS sin_summary
# MAGIC FROM crypto_lakehouse.bronze.news_raw
# MAGIC GROUP BY source;

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE crypto_lakehouse.bronze.news_raw IS
# MAGIC 'Entries crudas de 3 feeds RSS (CoinDesk, Cointelegraph, Decrypt). Una fila por entry por corrida; append-only, con duplicados entre corridas — la dedup es Silver.';