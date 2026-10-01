# Bitácora de desarrollo — Crypto Lakehouse

> Este es el README original del proyecto, conservado como registro de cómo se fue construyendo (fases,
> decisiones y estado en cada momento). La presentación del proyecto está en el [README principal](../README.md).

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
Search) servido en una **Databricks App** (AppKit, React) junto al dashboard embebido, y espejado
en **Next.js/Vercel** para la demo pública: https://crypto-lakehouse-databricks.vercel.app/

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
              Databricks App (inicio + dashboard + agente)   +   espejo en Next.js/Vercel (demo pública)
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
- [x] **Fase 2 — Silver.** Tipado y limpieza, `dim_asset` SCD Type 2 (`MERGE INTO` manual), scraping de artículos completos para el corpus del RAG. Se evaluó también una versión declarativa con `AUTO CDC FROM SNAPSHOT` (Lakeflow Declarative Pipelines) pero se descartó tras un troubleshooting largo y repetitivo — ver [`notebooks/02_silver/README.md`](../notebooks/02_silver/README.md).
- [x] **Fase 3 — Gold.** Marts agregados: `asset_daily_summary`, `dim_asset_current`, `news_pipeline_health`.
- [x] **Fase 4 — Visualización.** AI/BI Dashboard nativo (`dashboards/crypto_lakehouse_overview.lvdash.json`) + Genie Space ("Cryptocurrency Market Overview") listos. La Databricks App (Gradio) se arma cuando exista el agente de la Fase 7.
- [x] **Fase 5 — ML + MLflow.** Pipeline completo: feature table (`mlops.features_price_daily`, actualizada por `crypto_gold_daily_trigger`) + dos notebooks de entrenamiento (clasificador de dirección y regresor de retorno) con baseline y alias `champion` condicionado a superarlo. Primera corrida real con 8 días de historia: ningún modelo le ganó al baseline, así que no hay `champion` todavía. Se retoma con más historia y features estacionarias (ver [`notebooks/05_ml/README.md`](../notebooks/05_ml/README.md)).
- [x] **Fase 6 — RAG.** Chunking del corpus (`genai.news_chunks`), índice de Vector Search (`genai.news_chunks_index`) sincronizado, y chain de RAG con LangChain (`DatabricksVectorSearch` + `ChatDatabricks`) registrada en UC con alias `champion` (ver [`notebooks/06_rag/README.md`](../notebooks/06_rag/README.md)).
- [x] **Fase 7 — Agente de IA.** 4 UC Functions (tools SQL sobre Gold) + retrieval RAG (Vector Search) armadas con LangGraph, registradas en UC con alias `champion`, y **desplegadas en un Model Serving endpoint verificado** (`crypto_agent_endpoint`) — ver [`notebooks/07_agent/README.md`](../notebooks/07_agent/README.md) para la saga completa del deploy (5 causas de fallo distintas, desde cupo de compute hasta conflictos reales de dependencias entre `langchain`/`langgraph`/`openai-agents`).
- [x] **Fase 8 — Orquestación + documentación.** 3 Jobs de Databricks Workflows (`crypto_prices_pipeline` cada 30 min, `crypto_news_pipeline` 2x/día con sync condicional del índice RAG, `gold_daily_trigger` 1x/día) con tasks encadenadas por dependencias, horarios escalonados, y lineage bronze→silver→gold→genai verificado en Catalog Explorer — ver [`notebooks/08_orchestration/README.md`](../notebooks/08_orchestration/README.md).

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
app/                 Databricks App (AppKit: inicio, dashboard embebido, agente)
web/                 Espejo público en Next.js para Vercel (inicio + chat del agente)
dashboards/          Exports de los AI/BI Dashboards y notas de los Genie Spaces
docs/
  images/            Capturas para el README
```

Los notebooks se escriben y ejecutan en el workspace de Databricks Free Edition y se exportan a este
repo como *Source* (`.py` / `.sql`).

## Estado actual

**Fases 0 a 8 completas. En la Fase 5 el pipeline de ML está armado y corre, pero los modelos
todavía no superan a su baseline con la historia disponible.**
`silver.crypto_prices`, `silver.dim_asset` (SCD Type 2 con `MERGE INTO` manual) y `silver.crypto_news`
(dedup + scraping con `trafilatura`) listos. Se evaluó también una versión declarativa de `dim_asset`
con `AUTO CDC FROM SNAPSHOT` (Lakeflow Declarative Pipelines), pero se descartó: quedaba bloqueada
repetidamente por el cupo diario de compute serverless de Free Edition antes de poder cerrar el
troubleshooting, y era una segunda implementación redundante de algo que la versión manual ya
resuelve — no aporta nada nuevo al objetivo del proyecto. Los 3 marts de Gold, el AI/BI Dashboard y
el Genie Space están armados y verificados. La Fase 5 (ML) tiene la feature table
(`mlops.features_price_daily`, con `FeatureEngineeringClient`, actualizada a diario por Fase 8) y dos
notebooks de entrenamiento con baseline. En la primera corrida real (8 días de historia) ni el
clasificador de dirección ni el regresor de retorno superaron a su baseline, por lo que el alias
`champion` no se movió: el guard funcionó como se diseñó. Se retoma con más historia. La Fase 6 (RAG) está completa: chunking (`genai.news_chunks`,
368 chunks), índice de Vector Search (`genai.news_chunks_index`) sincronizado, y una chain de
LangChain (empaquetada como Models from Code) registrada en UC con alias `champion`, verificada
citando fuentes reales del corpus. La Fase 7 (Agente) está completa: 4 UC Functions + retrieval RAG
armadas con LangGraph, registradas en UC con alias `champion`, y **desplegadas y verificadas en un
Model Serving endpoint real** (`crypto_agent_endpoint`) — respondió correctamente tanto a preguntas
de precios (tool SQL) como de noticias (RAG con citas de fuentes reales). El deploy llevó 11
versiones del modelo y cinco causas de fallo distintas (cupo de compute, conflictos reales de
dependencias entre `langchain`/`langgraph`/`langgraph-prebuilt`/`openai-agents`, y falta de
credenciales declaradas para los recursos del agente) — historia completa en
[`notebooks/07_agent/README.md`](../notebooks/07_agent/README.md). Ya hay una Databricks App
(`crypto-agent-chat`, armada desde el template Node.js "AppKit - Serving") desplegada y respondiendo
con datos reales del agente; tiene tres pestañas (inicio, dashboard AI/BI embebido y agente con
markdown y tools consultadas) y tema oscuro/claro. Además hay un espejo público en Next.js
(`web/`, desplegado en Vercel) con inicio y chat: llama al endpoint con OAuth M2M de un Service
Principal con permiso de solo consulta, con keepalive en streaming y rate limiting. Una lección
del camino: recrear una UC Function con `CREATE OR REPLACE` invalida las credenciales que el
endpoint resolvió al desplegar, y el endpoint deja de cargar hasta redeployarlo. La Fase 8 (Orquestación) está completa:
3 Jobs de Databricks Workflows cubren todo el pipeline con dependencias encadenadas, horarios
escalonados, sync condicional del índice RAG, y lineage bronze→silver→gold→genai verificado en
Catalog Explorer — historia completa en
[`notebooks/08_orchestration/README.md`](../notebooks/08_orchestration/README.md). Próximo: retomar los
modelos de Fase 5 en 2-3 semanas con features estacionarias y validación walk-forward, y sumar una
pestaña de Forecast a la App cuando exista un `champion`.

## Trabajo futuro

- **Forecast:** retomar los modelos de la Fase 5 con más historia, features estacionarias y validación
  walk-forward, y servir el `champion` en el último endpoint disponible de Free Edition. Sumar entonces
  una pestaña de Forecast a la App.
- **Datos reales en el Home público:** un task del Job diario que genere un `kpis.json` (KPIs del
  mercado, movers del día, leaderboard top 25, salud del scraping y sparklines) y lo entregue a la web
  de Vercel, sin darle al Service Principal permisos sobre tablas ni un SQL warehouse. Se mostraría
  como foto del último día cerrado.
- **Rate limiting compartido:** hoy el límite de la demo pública es en memoria, por instancia; moverlo
  a un almacenamiento compartido (por ejemplo Upstash) si hiciera falta.
