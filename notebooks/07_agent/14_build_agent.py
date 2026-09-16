# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %pip install -q databricks-langchain langgraph langgraph-prebuilt mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %pip install -q "langgraph>=1.2.0" "langgraph-prebuilt>=1.0.13"
# MAGIC
# MAGIC import mlflow
# MAGIC mlflow.langchain.autolog()
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC
# MAGIC with mlflow.start_run(run_name="crypto_agent"):
# MAGIC     model_info = mlflow.langchain.log_model(
# MAGIC         lc_model="agent_code.py",
# MAGIC         artifact_path="agent",
# MAGIC         input_example={"messages": [{"role": "user", "content": "¿Cuáles son los 3 activos que más subieron hoy?"}]},
# MAGIC         registered_model_name="crypto_lakehouse.genai.crypto_agent",
# MAGIC     )

# COMMAND ----------

loaded_agent = mlflow.langchain.load_model(model_info.model_uri)
loaded_agent.invoke({"messages": [{"role": "user", "content": "¿Qué se dice sobre Bitcoin en las noticias?"}]})

# COMMAND ----------

from mlflow import MlflowClient

client = MlflowClient()
client.set_registered_model_alias(
    name="crypto_lakehouse.genai.crypto_agent",
    alias="champion",
    version=model_info.registered_model_version,
)