# `dim_asset` — versión declarativa (en progreso, bloqueada por un problema de ejecución sin resolver)

Segunda implementación de la dimensión SCD Type 2 de membership del top 25, pensada para compararse
con la versión manual (`notebooks/02_silver/04_silver_dim_asset_merge.py`, `MERGE INTO`).

## Qué hace el código

Usa **`AUTO CDC FROM SNAPSHOT`** (API sólo disponible en Python, `pyspark.pipelines`), no `AUTO CDC` a
secas: nuestra fuente (`bronze.prices_raw`) son fotos completas periódicas del top 25, sin marcadores
explícitos de insert/update/delete — el caso exacto para el que existe esta variante.
`next_snapshot_and_version` le entrega al motor, una corrida a la vez, la próxima foto no procesada
(usando `snapshot_ts` como número de versión, ya creciente), y el motor infiere solo qué activos
entraron y salieron del top 25, manteniendo el historial con `stored_as_scd_type="2"` — sin una línea
de `MERGE` ni lógica de cerrar+insertar escrita a mano.

## Historial de troubleshooting (2026-09-12)

**Primer síntoma:** al crear el Lakeflow Pipeline y correrlo, la inicialización del cluster (antes de
ejecutar código propio) tiraba `PERMISSION_DENIED: Can not move tables across arclight catalogs` /
`UNITY_CATALOG_INITIALIZATION_FAILED`. Se llegó a sospechar un bug irresoluble de Free Edition
(confirmado como error conocido en el [foro oficial de Databricks](https://community.databricks.com/t5/databricks-free-edition-help/unity-catalog-error-permission-denied-can-not-move-tables-across/td-p/149229)),
después de descartar varios workarounds (nombres fully-qualified, otros pipelines compitiendo por el
cupo, tabla a medio crear, recrear el pipeline de cero).

**Causa real, encontrada con Genie Code:** el pipeline se había creado inicialmente con
catalog=`workspace`/schema=`default` (el default de Databricks), y en ese momento se creó ahí una
tabla interna de **event log** del pipeline. Al corregir el catalog/schema a `crypto_lakehouse.silver`,
el pipeline intentaba mover esa tabla de event log entre catalogs al arrancar — justamente la operación
que Unity Catalog prohíbe, y el origen real del mensaje "Arclight". Se borró la tabla de event log
vieja (`workspace.default.event_log_f501dc8d...`, sólo historial de corridas fallidas, sin dato de
proyecto) y el pipeline recreó una nueva en el lugar correcto. **El error de catalog se resolvió de
verdad** — no era un bug irresoluble de la plataforma, era configuración + un artefacto interno
huérfano.

**Segundo síntoma, sin resolver todavía:** con el catalog ya bien configurado, el pipeline arranca y el
flow queda en estado `RUNNING`, pero **no progresa** — el log de eventos sólo muestra heartbeats
`Flow 'crypto_lakehouse.silver.dim_asset_scd2' is RUNNING` cada pocos segundos, sin un solo evento de
progreso real (filas procesadas, snapshot completado) después de 20+ minutos, para un dataset de sólo
75 filas / 3 snapshots. Se canceló manualmente. Causa todavía sin diagnosticar — candidatos a revisar
en la próxima sesión:
- Algo en el loop interno de `AUTO CDC FROM SNAPSHOT` con nuestra función `next_snapshot_and_version`
  (revisada dos veces, la lógica se ve correcta, pero vale la pena instrumentarla con prints/logging
  para confirmar que efectivamente devuelve `None` y corta).
- Compute serverless de pipelines en Free Edition con algún problema de performance/cuota.
- Revisar el Spark UI del cluster del pipeline (no sólo el event log de alto nivel) para ver en qué
  estado quedó realmente la ejecución interna.

## Estado

Código funcionalmente razonable (sigue la sintaxis oficial de `create_auto_cdc_from_snapshot_flow`),
pero **todavía no corrió a éxito**. A diferencia de la primera conclusión de la sesión, esto **no** es
un bug irresoluble de plataforma — hay una segunda causa distinta pendiente de diagnosticar. Pendiente
para la próxima sesión de Lakeflow Pipelines.
