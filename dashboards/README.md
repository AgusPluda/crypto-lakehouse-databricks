# Fase 4 — AI/BI Dashboard

`crypto_lakehouse_overview.lvdash.json` es la definición exportada del dashboard **Crypto Lakehouse —
Overview**, publicado sobre los 3 marts de Gold. Para volver a importarlo: Databricks → Dashboards →
Create → Import dashboard from file.

## Paneles

| panel | tipo | fuente |
|---|---|---|
| KPIs (market cap total, mayor suba/baja 24h, % de noticias scrapeadas) | 4 Counters | `gold.dim_asset_current` + `gold.news_pipeline_health` (CTEs + `CROSS JOIN` para combinar 4 agregados de 1 fila en una sola) |
| Leaderboard | Tabla | `gold.dim_asset_current`, ordenado por rank |
| Movers del día | Barras | `gold.asset_daily_summary` |
| Salud del pipeline de noticias | Barras apiladas por `source` | `gold.news_pipeline_health` |

## Genie Space

**"Cryptocurrency Market Overview"**, sobre las mismas 3 tablas de `gold`. Verificado con la pregunta
"¿Qué activo tuvo la mayor caída en las últimas 24hs?" — respondió Bitcoin Cash (-11.59%), coincide
exactamente con el KPI del dashboard, y armó su propio gráfico de contexto (top 10 con mayor caída).
