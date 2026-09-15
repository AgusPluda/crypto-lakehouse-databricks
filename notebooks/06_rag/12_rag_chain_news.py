# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %pip install -q langchain langchain-core databricks-langchain mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
from mlflow import MlflowClient
mlflow.langchain.autolog()

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")

# Recordatorio: la logica del Modelo RAG esta en "chain_code.py", 
# en este notebook se hace el registro del modelo en MLFLow.

with mlflow.start_run(run_name="rag_chain_news"):
    model_info = mlflow.langchain.log_model(
        lc_model="chain_code.py",
        artifact_path="chain",
        input_example={"question": "¿Qué se dice sobre Bitcoin?"},
        registered_model_name="crypto_lakehouse.genai.news_rag_chain",
    )

# COMMAND ----------

# Prueba de chain_code.py
loaded_chain = mlflow.langchain.load_model(model_info.model_uri)
loaded_chain.invoke({"question": "¿Qué se dice sobre Bitcoin?"})

# COMMAND ----------

client = MlflowClient()
client.set_registered_model_alias(
    name="crypto_lakehouse.genai.news_rag_chain",
    alias="champion",
    version=model_info.registered_model_version,
)