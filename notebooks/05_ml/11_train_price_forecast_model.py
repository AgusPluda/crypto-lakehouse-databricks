# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Fase 5: ML — Entrenamiento: forecast de retorno diario (regresión)
# MAGIC
# MAGIC `mlops.features_price_daily` → `Pipeline(StandardScaler, Ridge)` + MLflow + registro en UC.
# MAGIC
# MAGIC **Se predice el retorno, no el precio.** El target es `target_price_change_pct` (retorno open→close del día,
# MAGIC como fracción). Predecir el nivel de precio directo devuelve casi el precio de ayer y no aprende nada.
# MAGIC El precio pronosticado se deriva afuera del modelo: `price_close_ultimo * (1 + retorno_predicho)`.
# MAGIC
# MAGIC - **Ridge** en vez de regresión lineal simple: con pocos días de historia regulariza y es más estable.
# MAGIC - **Baseline:** predecir siempre el retorno medio del train. El modelo tiene que ganarle en MAE.
# MAGIC - El alias `champion` solo se mueve si el modelo **supera al baseline** en test.

# COMMAND ----------

FEATURE_TABLE = "crypto_lakehouse.mlops.features_price_daily"
MODEL_NAME = "crypto_lakehouse.mlops.price_forecast_model"
MIN_DATES = 8  # >=6 días de train y >=2 de test con el split 80/20

df = spark.table(FEATURE_TABLE)
n_rows = df.count()
n_dates = df.select("trade_date").distinct().count()
ready = n_dates >= MIN_DATES

print(f"filas: {n_rows} | días distintos: {n_dates}")
if not ready:
    print(f"No hay suficiente historia para entrenar (mínimo {MIN_DATES} días, hay {n_dates}). "
          f"Se acumula sola con los Jobs de Fase 8.")

# COMMAND ----------

if ready:
    import numpy as np
    import mlflow
    import mlflow.sklearn
    from mlflow import MlflowClient
    from mlflow.models import infer_signature
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    mlflow.set_registry_uri("databricks-uc")

    FEATURE_COLS = [
        "feature_price_close", "feature_rank_close", "feature_avg_market_cap",
        "feature_avg_total_volume", "feature_price_change_pct",
    ]
    TARGET_COL = "target_price_change_pct"

    pdf = df.toPandas().sort_values("trade_date")
    pdf[FEATURE_COLS + [TARGET_COL]] = pdf[FEATURE_COLS + [TARGET_COL]].astype(float)

    dates = sorted(pdf["trade_date"].unique())
    n_test_dates = max(1, int(len(dates) * 0.2))
    cutoff = dates[-n_test_dates]
    train_pdf = pdf[pdf["trade_date"] < cutoff]
    test_pdf = pdf[pdf["trade_date"] >= cutoff]

    X_train, y_train = train_pdf[FEATURE_COLS], train_pdf[TARGET_COL]
    X_test, y_test = test_pdf[FEATURE_COLS], test_pdf[TARGET_COL]

    baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
    baseline_mae = mean_absolute_error(y_test, baseline.predict(X_test))

    with mlflow.start_run(run_name="price_forecast_ridge") as run:
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", Ridge(alpha=1.0)),
        ])
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        directional_acc = float((np.sign(preds) == np.sign(y_test)).mean())
        beats_baseline = mae < baseline_mae

        mlflow.log_param("model_type", "Pipeline(StandardScaler, Ridge)")
        mlflow.log_param("alpha", 1.0)
        mlflow.log_param("n_train", len(X_train))
        mlflow.log_param("n_test", len(X_test))
        mlflow.log_param("n_train_dates", train_pdf["trade_date"].nunique())
        mlflow.log_param("n_test_dates", test_pdf["trade_date"].nunique())
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("directional_accuracy", directional_acc)
        mlflow.log_metric("baseline_mae", baseline_mae)
        mlflow.log_metric("beats_baseline", int(beats_baseline))

        model_info = mlflow.sklearn.log_model(
            model, artifact_path="model",
            signature=infer_signature(X_train, model.predict(X_train)),
            registered_model_name=MODEL_NAME,
        )
        print(f"mae={mae:.5f} rmse={rmse:.5f} baseline_mae={baseline_mae:.5f} "
              f"directional_acc={directional_acc:.3f} run_id={run.info.run_id}")

    version = model_info.registered_model_version
    if beats_baseline:
        MlflowClient().set_registered_model_alias(MODEL_NAME, "champion", version)
        print(f"alias 'champion' -> versión {version}")
    else:
        print(f"versión {version} registrada, pero NO supera al baseline: no se mueve 'champion'.")
