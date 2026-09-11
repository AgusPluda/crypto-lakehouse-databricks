# Crypto Lakehouse en Databricks

![Databricks](https://img.shields.io/badge/Databricks-Free%20Edition-FF3621?logo=databricks&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta%20Lake-Medallion-00ADD8?logo=delta&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-3.5-E25A1C?logo=apachespark&logoColor=white)
![Unity Catalog](https://img.shields.io/badge/Unity%20Catalog-gobernanza-1B3139)
![MLflow](https://img.shields.io/badge/MLflow-tracking%20%2B%20registry-0194E2?logo=mlflow&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-En%20desarrollo-yellow)

## Descripción del proyecto

Lakehouse de punta a punta sobre **Databricks Free Edition**: ingesta recurrente desde una API real
(precios de criptomonedas de **CoinGecko** + noticias vía **RSS**), arquitectura **medallion**
(Bronze → Silver → Gold) construida con **PySpark** y **Delta Lake**, y sobre los marts Gold tres
consumidores gobernados dentro del **mismo Unity Catalog**: un **dashboard AI/BI**, un **modelo de
ML** reentrenado periódicamente con **MLflow**, y un **agente de IA** con RAG (Vector Search sobre un
corpus de noticias) servido a una **app Streamlit**.

Es el proyecto demostrativo con el que cierro el learning path oficial de Databricks Academy. El
objetivo explícito es ejercitar la mayor superficie posible de la plataforma —no un pipeline chico—
y mostrar lo que más me interesó de Databricks: **Unity Catalog como sustrato de gobernanza
unificado**, donde tablas, features, índices de vector search, modelos y agentes tienen todos el
mismo lineage y el mismo modelo de permisos.

## Arquitectura

```
CoinGecko  /coins/markets   top 25 por market cap, DINÁMICO   (job cada ~30-60 min)
RSS        CoinDesk · Cointelegraph · Decrypt                 (job 1x/día)
      │  notebooks de ingesta (PySpark)
      ▼
BRONZE   bronze.prices_raw · bronze.news_raw      append · payload crudo + metadata de ingesta
      │  PySpark + Delta
      ▼
SILVER   silver.crypto_prices    hechos tipados por snapshot (precio, market_cap, rank_at_snapshot)
         silver.dim_asset        SCD Type 2 de membership top-25  —  MERGE manual + AUTO CDC declarativo
         silver.crypto_news      dedup por URL · scraping del artículo completo · limpieza HTML
      │
      ▼
GOLD     marts agregados para el dashboard y las features del ML     (Fase 3 — a diseñar)
      │
      ├──▶  AI/BI Dashboard nativo  (+ Genie Space)
      ├──▶  ML   · schema mlops · modelo tabular + MLflow, reentrenado por Job, alias `champion` en UC
      └──▶  RAG  · schema genai · Vector Search sobre noticias → chain LangChain → Agente (tools SQL + retrieval)
                        │
                        ▼
              Databricks App (Streamlit)   +   espejo en Streamlit Community Cloud
```

Todo el lineage —de la tabla Bronze al agente servido— vive dentro de un único catalog de Unity
Catalog (`crypto_lakehouse`).

## Modelo de datos: catalog y schemas

Catalog **`crypto_lakehouse`**, con 5 schemas separados (no un schema único con prefijos) para poder
mostrar permisos distintos por capa:

| schema  | contenido |
|---------|-----------|
| `bronze` | payloads crudos de CoinGecko y RSS + metadata de ingesta |
| `silver` | hechos tipados, `dim_asset` (SCD2), noticias limpias y scrapeadas |
| `gold`   | marts agregados para el dashboard y las features del ML |
| `mlops`  | feature tables + modelos registrados en el Model Registry de UC |
| `genai`  | chunks de noticias + índice de vector search + chain/agente registrados |

## Roadmap de fases

- [x] **Fase 0 — Fundacional.** Catalog `crypto_lakehouse` + 5 schemas. Repo sincronizado con Databricks Repos.
- [x] **Fase 1 — Ingesta Bronze.** Precios de CoinGecko (`/coins/markets`, top 25 dinámico) y noticias RSS.
- [ ] **Fase 2 — Silver.** Tipado y limpieza, `dim_asset` SCD Type 2 (versión manual `MERGE` + versión declarativa `AUTO CDC`), scraping de artículos completos para el corpus del RAG.
- [ ] **Fase 3 — Gold.** Marts agregados (diseño en detalle pendiente).
- [ ] **Fase 4 — Visualización.** AI/BI Dashboard nativo + Genie Space, más una Databricks App (Streamlit).
- [ ] **Fase 5 — ML + MLflow.** Modelo tabular sobre el dominio, reentrenado por Job, registrado en UC con alias `champion`.
- [ ] **Fase 6 — RAG.** Índice de Vector Search sobre las noticias, chain con LangChain, registrada en UC.
- [ ] **Fase 7 — Agente de IA.** Tools SQL sobre Gold + retrieval RAG; AI Playground → Agent Framework → Model Serving. La app de la Fase 4 es su chat UI.
- [ ] **Fase 8 — Orquestación + documentación.** Jobs con dependencias entre fases (escalonados por el límite de 5 tareas concurrentes) + lineage completo en Catalog Explorer como pieza central del README.

## Cómo está organizado el repo

```
notebooks/
  00_setup/          Fase 0 — catalog y schemas
  01_bronze/         Fase 1 — ingesta
  02_silver/         Fase 2 — transformación
  03_gold/           Fase 3 — marts
  05_ml/             Fase 5 — entrenamiento y registro
  06_rag/            Fase 6 — vector search + chain
  07_agent/          Fase 7 — agente
  08_orchestration/  Fase 8 — jobs
pipelines/           Lakeflow Declarative Pipeline (dim_asset SCD2 declarativo)
app/                 Databricks App (Streamlit) + espejo en Streamlit Community Cloud
dashboards/          Exports de los AI/BI Dashboards y notas de los Genie Spaces
docs/
  images/            Capturas para el README
```

Los notebooks se escriben y ejecutan en el workspace de Databricks Free Edition y se exportan a este
repo como *Source* (`.py` / `.sql`).

## Estado actual

**Fase 2 casi completa.** Fase 0 + Fase 1 completas. `silver.crypto_prices`, `silver.dim_asset`
(versión manual con `MERGE`) y `silver.crypto_news` (dedup + scraping con `trafilatura`) listos. Falta
sólo `silver.dim_asset` declarativo (`AUTO CDC`, Lakeflow Pipeline aparte, sesión dedicada). La Fase 3
(Gold) sigue pendiente de diseñar en detalle.
