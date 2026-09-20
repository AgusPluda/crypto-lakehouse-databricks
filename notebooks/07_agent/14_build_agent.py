# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %pip install -q databricks-langchain langgraph "langgraph-prebuilt<1.0.9" mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import subprocess

freeze = subprocess.run(["pip", "freeze"], capture_output=True, text=True).stdout.splitlines()

EXCLUDE_EXACT = {"pyspark", "delta-spark", "databricks-connect", "openai", "openai-agents"}
EXCLUDE_PREFIXES = (
    "ipykernel", "ipython", "ipyflow", "ipywidgets", "jupyter", "notebook",
    "nbclient", "nbconvert", "nbformat", "terminado", "debugpy",
    "python-lsp", "pyright", "rope", "pyflakes", "mccabe", "black", "yapf",
    "pytoolconfig", "tokenize-rt", "whatthepatch", "mypy-extensions", "jedi",
    "parso", "matplotlib-inline", "prompt-toolkit", "stack-data", "pure-eval",
    "executing", "comm", "traitlets", "pyzmq", "widgetsnbextension",
    "send2trash", "json5", "prometheus", "argon2", "bleach", "tinycss2",
    "mistune", "defusedxml", "fastjsonschema", "pandocfilters", "python-json-logger",
    "matplotlib", "seaborn", "scipy", "scikit-learn", "plotly", "patsy",
    "contourpy", "cycler", "fonttools", "kiwisolver", "pillow", "skops",
    "joblib", "threadpoolctl", "cython", "griffelib", "facets-overview",
    "pytest", "iniconfig", "pluggy", "tomli", "docstring-to-markdown",
    "virtualenv", "nodeenv", "filelock", "platformdirs", "distlib",
    "python-apt", "dbus-python", "pygobject", "ubuntu-pro-client",
    "unattended-upgrades", "ssh-import-id", "distro-info", "wadllib",
    "launchpadlib", "lazr", "httplib2", "azure-", "google-cloud-storage",
    "google-cloud-core", "google-resumable-media", "google-crc32c",
    "boto3", "botocore", "s3transfer", "jmespath", "deltalake", "arro3",
    "pyiceberg", "mmh3", "zstandard", "psycopg2", "pyodbc", "huey",
    "whenever", "astunparse", "pyroaring",
)

def keep(pkg_line):
    name = pkg_line.split("==")[0].lower()
    return name not in EXCLUDE_EXACT and not name.startswith(EXCLUDE_PREFIXES)

filtered = [line for line in freeze if keep(line)]
filtered += ["openai==2.7.1", "openai-agents==0.5.0"]
print(f"Total: {len(filtered)} paquetes\n")
print("\n".join(filtered))

# COMMAND ----------

import mlflow
from mlflow.models.resources import (
    DatabricksServingEndpoint,
    DatabricksFunction,
    DatabricksVectorSearchIndex,
)

mlflow.langchain.autolog()
mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment("/Users/agustinpluda24@gmail.com/crypto_agent_experiment")

resources = [
    DatabricksServingEndpoint(endpoint_name="databricks-meta-llama-3-3-70b-instruct"),
    DatabricksFunction(function_name="crypto_lakehouse.genai.get_asset_price"),
    DatabricksFunction(function_name="crypto_lakehouse.genai.get_top_gainers"),
    DatabricksFunction(function_name="crypto_lakehouse.genai.get_top_losers"),
    DatabricksFunction(function_name="crypto_lakehouse.genai.news_pipeline_health"),
    DatabricksVectorSearchIndex(index_name="crypto_lakehouse.genai.news_chunks_index"),
]

with mlflow.start_run(run_name="crypto_agent"):
    model_info = mlflow.langchain.log_model(
        lc_model="agent_code.py",
        artifact_path="agent",
        input_example={"messages": [{"role": "user", "content": "¿Cuáles son los 3 activos que más subieron hoy?"}]},
        registered_model_name="crypto_lakehouse.genai.crypto_agent",
        pip_requirements=filtered,
        resources=resources,
    )

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