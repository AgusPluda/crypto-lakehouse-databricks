# Fase 5 — ML + MLflow

| notebook | qué hace | tabla/artefacto |
|----------|----------|-----------------|
| `09_features_price_daily` | Feature engineering: `LAG` de 1 día por activo sobre `gold.asset_daily_summary`, registrado con `FeatureEngineeringClient` | `mlops.features_price_daily` (feature table con primary key en UC) |
| _pendiente_ | Entrenamiento + tracking con MLflow + registro en UC con alias `champion` | modelo de clasificación (sube/baja el precio a 1 día) |

**Limitación de datos conocida (2026-09-12):** la feature table requiere ≥2 días consecutivos de
`gold.asset_daily_summary` por activo (usa `LAG`). Hoy sólo hay 1 día de historia acumulada, así que
la tabla existe con el schema correcto pero **0 filas** — es el resultado esperado, no un bug. Se
resuelve solo cuando la Fase 8 (orquestación) empiece a correr la ingesta con scheduling real y se
acumulen varios días. El notebook de entrenamiento debe manejar este caso con una guarda explícita
(no intentar entrenar con 0 filas), no asumir que siempre hay datos suficientes.
