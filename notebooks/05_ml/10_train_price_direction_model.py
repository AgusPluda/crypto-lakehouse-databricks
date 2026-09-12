# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 5: ML — Entrenamiento: dirección de precio a 1 día
# MAGIC
# MAGIC mlops.features_price_daily → modelo de clasificación + MLflow + registro en UC con alias `champion`.
# MAGIC Con guarda explícita: si no hay suficientes filas, no entrena.

# COMMAND ----------

from pyspark.sql import functions as F

FEATURE_TABLE = "crypto_lakehouse.mlops.features_price_daily"
MODEL_NAME = "crypto_lakehouse.mlops.price_direction_model"
MIN_ROWS = 20  # mínimo razonable para que un split train/test tenga sentido

df = spark.table(FEATURE_TABLE)
n = df.count()
print(f"filas disponibles: {n}")

if n < MIN_ROWS:
    print(f"No hay suficientes datos para entrenar (mínimo {MIN_ROWS}, hay {n}). "
          f"Pendiente hasta que Fase 8 acumule más historia con scheduling real.")

# COMMAND ----------

if n >= MIN_ROWS:
    import mlflow
    import mlflow.sklearn
    from mlflow import MlflowClient
    from mlflow.models import infer_signature
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score

    mlflow.set_registry_uri("databricks-uc")

    FEATURE_COLS = [
        "feature_price_close", "feature_rank_close", "feature_avg_market_cap",
        "feature_avg_total_volume", "feature_price_change_pct",
    ]
    TARGET_COL = "target_price_up"

    pdf = df.toPandas().sort_values("trade_date")

    # split TEMPORAL, no aleatorio: entrenamos con fechas viejas, testeamos con las mas nuevas
    dates = sorted(pdf["trade_date"].unique())
    cutoff = dates[int(len(dates) * 0.8)]
    train_pdf = pdf[pdf["trade_date"] < cutoff]
    test_pdf  = pdf[pdf["trade_date"] >= cutoff]

    X_train, y_train = train_pdf[FEATURE_COLS], train_pdf[TARGET_COL]
    X_test,  y_test  = test_pdf[FEATURE_COLS],  test_pdf[TARGET_COL]

    with mlflow.start_run(run_name="price_direction_baseline") as run:
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)

        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.log_param("n_train", len(X_train))
        mlflow.log_param("n_test", len(X_test))
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1", f1)

        signature = infer_signature(X_train, model.predict(X_train))
        mlflow.sklearn.log_model(
            model, artifact_path="model",
            signature=signature,
            registered_model_name=MODEL_NAME,
        )
        print(f"accuracy={acc:.3f} f1={f1:.3f} run_id={run.info.run_id}")

    client = MlflowClient()
    versions = client.search_model_versions(f"name = '{MODEL_NAME}'")
    latest_version = max(int(v.version) for v in versions)
    client.set_registered_model_alias(MODEL_NAME, "champion", latest_version)
    print(f"alias 'champion' -> versión {latest_version}")