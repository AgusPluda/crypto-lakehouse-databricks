# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 6: RAG — Chunking de noticias
# MAGIC
# MAGIC silver.crypto_news (sólo scrape_status='ok') → genai.news_chunks. Trochea el texto completo con
# MAGIC RecursiveCharacterTextSplitter de LangChain. Corpus base para el índice de Vector Search.

# COMMAND ----------

# MAGIC %pip install langchain-text-splitters
# MAGIC %restart_python

# COMMAND ----------

from pyspark.sql.functions import col, lit, sha2, struct, current_timestamp
from pyspark.sql.types import *
import pyspark.sql.functions as F

SOURCE_TABLE = "crypto_lakehouse.silver.crypto_news"
CHUNKS_TABLE = "crypto_lakehouse.genai.news_chunks"

source = spark.read.table(SOURCE_TABLE).filter(col("scrape_status") == "ok")

if spark.catalog.tableExists(CHUNKS_TABLE):
    ya_procesados = spark.table(CHUNKS_TABLE).select("link").distinct()
    nuevos = source.join(ya_procesados, on="link", how="left_anti")
else:
    nuevos = source

# COMMAND ----------

from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
)

rows = nuevos.collect()

records = []
for row in rows:
    chunks = splitter.split_text(row["article_text"])
    for i, chunk_text in enumerate(chunks):
        records.append((
            f"{row['link']}::{i}",
            row["link"], row["source"], row["title"], row["published_at"],
            i, chunk_text,
        ))

print(f"artículos nuevos: {len(rows)} | chunks generados: {len(records)}")

# COMMAND ----------

CHUNKS_SCHEMA = StructType([
    StructField("chunk_id", StringType(), False),
    StructField("link", StringType(), True),
    StructField("source", StringType(), True),
    StructField("title", StringType(), True),
    StructField("published_at", TimestampType(), True),
    StructField("chunk_index", LongType(), True),
    StructField("chunk_text", StringType(), True)
])

# COMMAND ----------

df_chunks = spark.createDataFrame(records, schema=CHUNKS_SCHEMA).withColumn(
    "_chunks_processed_at", F.current_timestamp()
)
df_chunks.write.option("delta.enableChangeDataFeed", "true").mode("append").saveAsTable(CHUNKS_TABLE)