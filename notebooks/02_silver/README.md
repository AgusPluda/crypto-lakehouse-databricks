# Fase 2 — Silver

Datos tipados, limpios y modelados. De esta capa para abajo todo se junta por `asset_id`.

| notebook | fuente | tabla | notas |
|----------|--------|-------|-------|
| `03_silver_crypto_prices` | `bronze.prices_raw` | `silver.crypto_prices` | tabla de hechos, 1 fila por (`asset_id`, `snapshot_ts`); carga incremental por anti-join sobre `snapshot_ts` |
| `04_silver_dim_asset_merge` | `bronze.prices_raw` | `silver.dim_asset` | dimensión SCD Type 2 de membership en el top 25, **versión manual**: compara el snapshot más reciente contra el estado activo con un `MERGE` de cerrar+insertar en un solo statement |
| `05_silver_crypto_news` | `bronze.news_raw` | `silver.crypto_news` | dedup por `link` ("primero visto" con `Window`+`row_number`), limpieza de HTML, parseo de fecha RFC 822, scraping del artículo completo con `trafilatura` (reintentos con backoff en 429; CoinDesk bloquea el scraping de forma sostenida y se saltea a propósito — queda con título/link solamente) |

## `dim_asset`: se descartó la versión declarativa (2026-09-16)

Se evaluó una segunda implementación de `dim_asset` con **Lakeflow Declarative Pipelines**
(`AUTO CDC FROM SNAPSHOT`, la variante correcta para una fuente de fotos completas periódicas sin
marcadores de insert/update/delete) para compararla con la versión manual. Se descartó por completo
después de un troubleshooting largo y repetitivo, documentado acá porque fue real trabajo de
diagnóstico, no un abandono sin más:

1. **`PERMISSION_DENIED: Can not move tables across arclight catalogs` / `UNITY_CATALOG_INITIALIZATION_FAILED`**
   al arrancar el pipeline. Causa real: el pipeline se había creado inicialmente con
   catalog=`workspace`/schema=`default`, y ahí quedó una tabla interna de *event log*; al corregir el
   pipeline a `crypto_lakehouse.silver`, intentaba mover esa tabla de catalog al arrancar — la
   operación que Unity Catalog prohíbe. Se resolvió borrando la tabla de event log huérfana y dejando
   que el pipeline recreara una nueva en el lugar correcto.
2. **El pipeline arrancaba y quedaba en `RUNNING` sin progresar**, solo heartbeats en el event log
   (`Flow '...' is RUNNING` cada pocos segundos) sin un solo evento de filas procesadas, para apenas 75
   filas / 3 snapshots. Cancelado a mano tras 20+ minutos sin diagnóstico posible con las herramientas
   disponibles (event log de alto nivel, sin acceso cómodo al Spark UI del cluster serverless).
3. Se recreó el pipeline de cero (mismo notebook, catalog/schema ya bien configurados) para descartar
   que fuera un estado corrupto del pipeline viejo — el primer intento de correrlo **volvió a fallar**,
   esta vez directamente por **`RESOURCE_EXHAUSTED: You've hit the limit for serverless compute for
   free usage`**, el cupo diario de compute serverless de Databricks Free Edition, antes de poder
   siquiera generar un evento de progreso nuevo.

**Decisión:** cortar acá. Tres intentos, tres bloqueos distintos (dos de configuración/estado interno,
resueltos, y uno de cupo de la plataforma, no resoluble a voluntad), para implementar una **segunda
versión de algo que ya funciona** con el `MERGE INTO` manual — no era un requisito del proyecto, era
un ejercicio comparativo opcional. El costo de seguir insistiendo (tiempo + cupo diario agotable) dejó
de justificarse frente al beneficio (una comparación manual-vs-declarativo que no cambia el resultado
final de la Fase 2). Se borró el pipeline, el notebook (`dim_asset_declarative.py`) y la tabla huérfana
`crypto_lakehouse.silver.dim_asset_scd2`. La Fase 2 queda completa con la versión manual únicamente.
