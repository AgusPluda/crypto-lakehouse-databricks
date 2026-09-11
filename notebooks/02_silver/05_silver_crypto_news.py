# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 2: Silver — crypto_news (dedup + scraping)
# MAGIC
# MAGIC `bronze.news_raw` → `silver.crypto_news`. Una fila por artículo único (dedup por link, "primero visto").
# MAGIC Trae el texto completo del artículo vía scraping — el corpus real para el RAG de Fase 6.

# COMMAND ----------

# MAGIC %pip install trafilatura
# MAGIC %restart_python

# COMMAND ----------

import re
import html
import time
from email.utils import parsedate_to_datetime

import requests
import trafilatura
from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

BRONZE_TABLE = "crypto_lakehouse.bronze.news_raw"
SILVER_TABLE = "crypto_lakehouse.silver.crypto_news"
USER_AGENT   = "crypto-lakehouse-databricks (portfolio project)"

# COMMAND ----------

bronze = spark.table(BRONZE_TABLE)

if spark.catalog.tableExists(SILVER_TABLE):
    ya_procesados = spark.table(SILVER_TABLE).select("link").distinct()
    bronze_nuevo = bronze.join(ya_procesados, on="link", how="left_anti")
else:
    bronze_nuevo = bronze

w = Window.partitionBy("link").orderBy("ingest_run_ts")
primero_visto = (
    bronze_nuevo
    .withColumn("rn", F.row_number().over(w))
    .filter(F.col("rn") == 1)
    .drop("rn")
)

nuevos_articulos = primero_visto.collect()
print(f"artículos nuevos a scrapear: {len(nuevos_articulos)}")

# COMMAND ----------

def clean_html(raw: str | None) -> str | None:
    if not raw:
        return None
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip() or None

import urllib.parse

BLOCKED_DOMAINS = {"www.coindesk.com"}  # bloquea scraping de forma sostenida, no vale la pena reintentar

def scrape_article(link: str, max_retries: int = 2) -> tuple:
    domain = urllib.parse.urlparse(link).netloc
    if domain in BLOCKED_DOMAINS:
        return None, "bloqueado", f"dominio conocido por bloquear scraping ({domain})"

    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(link, headers={"User-Agent": USER_AGENT}, timeout=20)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 5 * (attempt + 1)))
                print(f"  429 en {link[:60]}... espero {wait}s (intento {attempt + 1})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
            if not text:
                return None, "sin_contenido", "trafilatura no pudo extraer texto"
            return text, "ok", None
        except requests.exceptions.RequestException as e:
            return None, "error", str(e)[:300]
    return None, "error", "429 persistente tras los reintentos"

records = []
for row in nuevos_articulos:
    article_text, status, error = scrape_article(row["link"])

    published_at = None
    if row["published_raw"]:
        try:
            published_at = parsedate_to_datetime(row["published_raw"])
        except Exception:
            pass

    records.append((
        row["link"], row["source"], row["guid"], row["title"],
        clean_html(row["summary"]), row["author"], row["tags"],
        published_at, article_text, status, error,
        row["ingest_run_ts"],
    ))

    time.sleep(1)  # scraping respetuoso, no golpear los mismos 3 dominios sin pausa

print(f"scrapeados: {len(records)} | ok: {sum(1 for r in records if r[9] == 'ok')}")

# COMMAND ----------

NEWS_SILVER_SCHEMA = StructType([
    StructField("link", StringType(), True),
    StructField("source", StringType(), True),
    StructField("guid", StringType(), True),
    StructField("title", StringType(), True),
    StructField("summary_clean", StringType(), True),
    StructField("author", StringType(), True),
    StructField("tags", StringType(), True),
    StructField("published_at", TimestampType(), True),
    StructField("article_text", StringType(), True),
    StructField("scrape_status", StringType(), True),
    StructField("scrape_error", StringType(), True),
    StructField("first_ingested_at", TimestampType(), True)
])

# COMMAND ----------

df_silver = spark.createDataFrame(records, schema=NEWS_SILVER_SCHEMA).withColumn(
    "_silver_processed_at", F.current_timestamp()
)
df_silver.write.mode("append").saveAsTable(SILVER_TABLE)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(source),
# MAGIC     COUNT(scrape_status)
# MAGIC FROM crypto_lakehouse.silver.crypto_news

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE crypto_lakehouse.silver.crypto_news IS 
# MAGIC 'Articulos scrapeados de noticias de criptomonedas, 1 fila unica por articulo y el corpus del RAG de la fase 6'