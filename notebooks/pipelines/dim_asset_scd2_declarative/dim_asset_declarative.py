# Databricks notebook source
from pyspark import pipelines as dp
from pyspark.sql import functions as F

BRONZE_TABLE = "crypto_lakehouse.bronze.prices_raw"
TARGET_TABLE = "dim_asset_scd2"

def next_snapshot_and_version(latest_snapshot_version):
    # Find the next snapshot version without using collect()
    if latest_snapshot_version is None:
        next_version_df = (
            spark.table(BRONZE_TABLE)
            .select("snapshot_ts")
            .distinct()
            .orderBy("snapshot_ts")
            .limit(1)
        )
    else:
        next_version_df = (
            spark.table(BRONZE_TABLE)
            .select("snapshot_ts")
            .distinct()
            .filter(F.col("snapshot_ts") > latest_snapshot_version)
            .orderBy("snapshot_ts")
            .limit(1)
        )
    
    # Collect only the single next version
    next_version_rows = next_version_df.collect()
    if not next_version_rows:
        return None
    
    next_version = next_version_rows[0]["snapshot_ts"]
    
    # Get the snapshot data for this version
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