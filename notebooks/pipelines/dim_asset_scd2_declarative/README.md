# `dim_asset` — versión declarativa (bloqueada por un bug de Free Edition)

Segunda implementación de la dimensión SCD Type 2 de membership del top 25, pensada para compararse
con la versión manual (`notebooks/02_silver/04_silver_dim_asset_merge.py`, `MERGE INTO`) — ver la
decisión original en el scoping del proyecto.

## Qué hace el código

Usa **`AUTO CDC FROM SNAPSHOT`** (API sólo disponible en Python, `pyspark.pipelines`), no `AUTO CDC` a
secas: nuestra fuente (`bronze.prices_raw`) son fotos completas periódicas del top 25, sin marcadores
explícitos de insert/update/delete — el caso exacto para el que existe esta variante. La función
`next_snapshot_and_version` le entrega al motor, una corrida a la vez, la próxima foto no procesada
(usando `snapshot_ts` como número de versión, porque ya es creciente), y el motor infiere solo qué
activos entraron y cuáles salieron del top 25, manteniendo el historial con `stored_as_scd_type="2"`.
Ni una línea de `MERGE`, ni lógica de "cerrar + insertar" escrita a mano — esa es la comparación con la
versión manual.

## Estado: no se pudo correr — bug conocido de Databricks Free Edition

Al crear el Lakeflow Pipeline y correrlo, la inicialización del cluster (antes de ejecutar una sola
línea de nuestro código) tira:

```
PERMISSION_DENIED: Can not move tables across arclight catalogs
UNITY_CATALOG_INITIALIZATION_FAILED
```

"Arclight" es el nombre interno de la infraestructura de Unity Catalog gestionada de Free Edition. Un
empleado de Databricks confirma el error en el foro oficial y da una lista de workarounds — [ver el
hilo](https://community.databricks.com/t5/databricks-free-edition-help/unity-catalog-error-permission-denied-can-not-move-tables-across/td-p/149229).
Se probaron todos los aplicables a este caso, sin éxito:

- [x] Nombres de tabla fully-qualified en el código (`crypto_lakehouse.silver.dim_asset_declarative`) — ya lo estaba.
- [x] Borrar otros pipelines del workspace que pudieran competir por el cupo de "un pipeline activo por tipo" de Free Edition (había 3 de ejercicios de los cursos de certificación) — sin efecto.
- [x] Verificar que no hubiera una tabla a medio crear de un intento anterior — no existía.
- [x] Borrar el pipeline entero y recrearlo de cero, seteando catalog/schema desde el inicio — mismo error.

Conclusión: es una limitación real de la plataforma en este momento, no un error de configuración de
este proyecto. El hilo del foro no reporta una solución permanente, sólo workarounds — ninguno aplica
acá. Se documenta el código (funcionalmente correcto, sigue la sintaxis oficial de
`create_auto_cdc_from_snapshot_flow`) y se deja pendiente de reintentar cuando Databricks lo resuelva
del lado de Free Edition, o en un workspace pago si surge la oportunidad.
