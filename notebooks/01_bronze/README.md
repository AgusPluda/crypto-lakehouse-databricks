# Fase 1 — Ingesta Bronze

Landing de los datos crudos, tal como llegan de la fuente, con metadata de ingesta. Sin limpiar ni
tipar de más: eso es Silver. Todo append-only.

| notebook | fuente | tabla | frecuencia |
|----------|--------|-------|------------|
| `01_ingesta_precios_coingecko` | CoinGecko `GET /coins/markets` (top 25 por market cap, dinámico) | `bronze.prices_raw` | cada ~30-60 min (scheduling en Fase 8) |
| `02_ingesta_noticias_rss` | RSS (CoinDesk, Cointelegraph, Decrypt) | `bronze.news_raw` | 1x/día |

Por ahora los notebooks se corren a mano; la orquestación como Jobs se arma en Fase 8.
