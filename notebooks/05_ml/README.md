# Fase 5 — ML + MLflow

| notebook | qué hace | tabla/artefacto |
|----------|----------|-----------------|
| `09_features_price_daily` | Feature engineering: `LAG` de 1 día por activo sobre `gold.asset_daily_summary`, registrado con `FeatureEngineeringClient` | `mlops.features_price_daily` (feature table con primary key en UC) |
| `10_train_price_direction_model` | Clasificación binaria (sube/baja el precio a 1 día), split temporal, MLflow tracking, registro en UC con alias `champion` | `mlops.price_direction_model` |

**Limitación de datos conocida (2026-09-12):** la feature table requiere ≥2 días consecutivos de
`gold.asset_daily_summary` por activo (usa `LAG`). Hoy sólo hay 1 día de historia acumulada, así que
la tabla existe con el schema correcto pero **0 filas** — es el resultado esperado, no un bug.

El notebook de entrenamiento tiene una **guarda explícita** (`MIN_ROWS = 20`): si no hay suficientes
filas, imprime un mensaje claro y no intenta entrenar — verificado, hoy corta ahí con `filas
disponibles: 0`. **La rama de entrenamiento real (split temporal, MLflow, registro con alias
`champion`) todavía no se ejecutó ni se validó** — el código sigue el patrón correcto (Unity Catalog
Model Registry, split por fecha no aleatorio) pero queda pendiente de confirmar en la práctica cuando
la Fase 8 (orquestación) acumule suficiente historia real.
