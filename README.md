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
ML** reentrenado periódicamente con **MLflow**, y un **agente de IA** (tools SQL + RAG sobre Vector
Search) servido en una **Databricks App (Gradio)** y espejado en **Next.js/Vercel** para la demo
pública.

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
         silver.dim_asset        SCD Type 2 de membership top-25  —  MERGE INTO manual
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
              Databricks App (Gradio, chat interno)   +   espejo en Next.js/Vercel (demo pública)
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
- [x] **Fase 2 — Silver.** Tipado y limpieza, `dim_asset` SCD Type 2 (`MERGE INTO` manual), scraping de artículos completos para el corpus del RAG. Se evaluó también una versión declarativa con `AUTO CDC FROM SNAPSHOT` (Lakeflow Declarative Pipelines) pero se descartó: quedaba bloqueada una y otra vez por el cupo diario de compute serverless de Free Edition antes de poder terminar el troubleshooting, y era una segunda implementación redundante de lo mismo que ya resuelve el `MERGE` manual.
- [x] **Fase 3 — Gold.** Marts agregados: `asset_daily_summary`, `dim_asset_current`, `news_pipeline_health`.
- [x] **Fase 4 — Visualización.** AI/BI Dashboard nativo (`dashboards/crypto_lakehouse_overview.lvdash.json`) + Genie Space ("Cryptocurrency Market Overview") listos. La Databricks App (Gradio) se arma cuando exista el agente de la Fase 7.
- [ ] **Fase 5 — ML + MLflow.** Feature table (`mlops.features_price_daily`) ✅. Entrenamiento + registro con alias `champion` — código escrito y con guarda de datos verificada, pendiente de correr a éxito hasta acumular ≥2 días de historia (ver [`notebooks/05_ml/README.md`](notebooks/05_ml/README.md)).
- [x] **Fase 6 — RAG.** Chunking del corpus (`genai.news_chunks`), índice de Vector Search (`genai.news_chunks_index`) sincronizado, y chain de RAG con LangChain (`DatabricksVectorSearch` + `ChatDatabricks`) registrada en UC con alias `champion` (ver [`notebooks/06_rag/README.md`](notebooks/06_rag/README.md)).
- [ ] **Fase 7 — Agente de IA.** 4 UC Functions (tools SQL sobre Gold) + retrieval RAG (Vector Search) armadas con LangGraph, registradas en UC con alias `champion`. Deploy del Model Serving endpoint bloqueado por una falla de infraestructura de Free Edition (no de config, ver [`notebooks/07_agent/README.md`](notebooks/07_agent/README.md)).
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
app/                 Databricks App (Gradio) + espejo en Next.js/Vercel
dashboards/          Exports de los AI/BI Dashboards y notas de los Genie Spaces
docs/
  images/            Capturas para el README
```

Los notebooks se escriben y ejecutan en el workspace de Databricks Free Edition y se exportan a este
repo como *Source* (`.py` / `.sql`).

## Estado actual

**Fases 0, 1, 2, 3, 4 y 6 completas; Fase 7 en curso (agente armado, deploy bloqueado); Fase 5 en
curso, con un paso bloqueado por un factor externo (no por diseño).**
`silver.crypto_prices`, `silver.dim_asset` (SCD Type 2 con `MERGE INTO` manual) y `silver.crypto_news`
(dedup + scraping con `trafilatura`) listos. Se evaluó también una versión declarativa de `dim_asset`
con `AUTO CDC FROM SNAPSHOT` (Lakeflow Declarative Pipelines), pero se descartó: quedaba bloqueada
repetidamente por el cupo diario de compute serverless de Free Edition antes de poder cerrar el
troubleshooting, y era una segunda implementación redundante de algo que la versión manual ya
resuelve — no aporta nada nuevo al objetivo del proyecto. Los 3 marts de Gold, el AI/BI Dashboard y
el Genie Space están armados y verificados. La feature table de Fase 5 (`mlops.features_price_daily`,
con `FeatureEngineeringClient`) funciona; el entrenamiento del modelo está escrito con una guarda de
datos verificada, pero necesita ≥2 días de historia en `gold.asset_daily_summary` que se van a
acumular solos con la Fase 8. La Fase 6 (RAG) está completa: chunking (`genai.news_chunks`, 368
chunks), índice de Vector Search (`genai.news_chunks_index`) sincronizado, y una chain de LangChain
(empaquetada como Models from Code) registrada en UC con alias `champion`, verificada citando
fuentes reales del corpus. La Fase 7 (Agente) tiene 4 UC Functions + retrieval RAG armadas con
LangGraph y registradas en UC con alias `champion`; el Model Serving endpoint está bloqueado por una
falla de infraestructura de Free Edition (`Build could not start due to an internal error` — no es
config, ver [`notebooks/07_agent/README.md`](notebooks/07_agent/README.md)), pendiente de reintentar.
Falta la Databricks App (Gradio) + espejo en Next.js/Vercel, que esperan al endpoint del agente.
Próximo: reintentar el deploy del endpoint del agente, o retomar el pendiente de Fase 5 cuando se
destrabe solo.
