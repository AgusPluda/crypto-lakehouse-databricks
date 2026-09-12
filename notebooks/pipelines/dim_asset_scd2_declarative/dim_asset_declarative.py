# Databricks notebook source
from pyspark import pipelines as dp
from pyspark.sql import functions as F

BRONZE_TABLE = "crypto_lakehouse.bronze.prices_raw"
TARGET_TABLE = "crypto_lakehouse.silver.dim_asset_declarative"

def next_snapshot_and_version(latest_snapshot_version):
    all_versions = [
        r["snapshot_ts"]
        for r in spark.table(BRONZE_TABLE).select("snapshot_ts").distinct().orderBy("snapshot_ts").collect()
    ]

    candidatos = all_versions if latest_snapshot_version is None else [v for v in all_versions if v > latest_snapshot_version]
    if not candidatos:
        return None

    next_version = min(candidatos)
    snapshot_df = (
        spark.table(BRONZE_TABLE)
        .filter(F.col("snapshot_ts") == next_version)
        .select(F.col("id").alias("asset_id"), "symbol", "name", "image")
        .dropDuplicates(["asset_id"])
    )
    return (snapshot_df, next_version)

dp.create_streaming_table(
    name=TARGET_TABLE,
    comment="dim_asset via AUTO CDC FROM SNAPSHOT: version declarativa del SCD Type 2 de membership, para comparar con silver.dim_asset (version manual con MERGE)."
)

dp.create_auto_cdc_from_snapshot_flow(
    target=TARGET_TABLE,
    source=next_snapshot_and_version,
    keys=["asset_id"],
    stored_as_scd_type="2",
)