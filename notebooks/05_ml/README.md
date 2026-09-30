# Fase 5 — ML + MLflow

| notebook | qué hace | tabla/artefacto |
|----------|----------|-----------------|
| `09_features_price_daily` | Feature engineering: `LAG` de 1 día por activo sobre `gold.asset_daily_summary`, registrado con `FeatureEngineeringClient`. Incluye dos targets: `target_price_up` (binario) y `target_price_change_pct` (retorno) | `mlops.features_price_daily` (feature table con primary key en UC) |
| `10_train_price_direction_model` | Clasificación (sube/baja a 1 día): `Pipeline(StandardScaler, LogisticRegression)` contra un baseline de clase mayoritaria | `mlops.price_direction_model` |
| `11_train_price_forecast_model` | Regresión del retorno diario: `Pipeline(StandardScaler, Ridge)` contra un baseline de retorno medio. Alimentaría el forecast de la App | `mlops.price_forecast_model` |

`09_features_price_daily` corre como última task de `crypto_gold_daily_trigger` (Fase 8), después de
`asset_daily_summary`, así la feature table se mantiene al día sin correr nada a mano. Los dos
notebooks de entrenamiento se corren a mano: no están en ningún Job.

## Decisiones de diseño

- **Features con rezago exacto de 1 día.** `LAG()` devuelve la fila anterior, no el día calendario
  anterior. Se agrega `LAG(trade_date)` y se filtra `DATEDIFF(trade_date, prev_date) = 1`; sin eso, un
  hueco de datos (ej. 2026-09-10 → 2026-09-21) se trataba como si fueran días consecutivos.
- **`gold.asset_daily_summary` solo tiene días cerrados** (`WHERE to_date(snapshot_ts) < current_date()`
  en el mart). Antes, el rebuild de las 00:15 metía el día en curso con unos pocos snapshots como si
  fuera un resumen diario completo. Se arregló en el mart, no en el notebook de features: es un
  contrato de la tabla Gold, no un parche de un consumidor.
- **Guarda por días distintos, no por filas.** Las filas escalan con la cantidad de activos (25 por
  día), así que `MIN_ROWS` no dice nada sobre si se puede hacer un split temporal. `MIN_DATES = 8`
  deja al menos 6 días de train y 2 de test con el split 80/20.
- **Split temporal**, no aleatorio: los últimos ~20% de los días son test.
- **`StandardScaler` en un `Pipeline`.** Features como `market_cap` (~1e12) junto a `rank` (~10)
  rompían la convergencia y los coeficientes de los modelos lineales sin escalar.
- **Baseline logueado junto al modelo** (`DummyClassifier(most_frequent)` / `DummyRegressor(mean)`).
  Una métrica sin baseline no significa nada. El alias `champion` **solo se mueve si el modelo le gana
  al baseline** (accuracy en el clasificador, MAE en el regresor).
- **Regresión sobre el retorno, no sobre el nivel de precio.** Predecir el precio directo devuelve casi
  el precio de ayer y parece un ajuste perfecto sin aprender nada. El precio pronosticado se derivaría
  afuera del modelo: `último_close * (1 + retorno_predicho)`.
- **Ridge** en vez de regresión lineal simple, porque regulariza mejor con poca historia.
- **Métrica de dirección** (`directional_accuracy`) en el regresor: MAE y RMSE no dicen si al menos
  acierta hacia dónde se mueve el precio.

## Primera corrida real (2026-09-30, 8 fechas de historia)

| modelo | métricas | baseline | resultado |
|--------|----------|----------|-----------|
| `price_direction_model` v1 | accuracy 0.615, f1 0.286 | accuracy 0.692 | no supera al baseline, sin `champion` |
| `price_forecast_model` v1 | MAE 0.0162, RMSE 0.0237, directional 0.538 | MAE 0.0131 | no supera al baseline, sin `champion` |

**Ningún modelo superó a su baseline, y el guard se comportó como debía.** Las versiones quedan
registradas en UC (v1) pero sin alias `champion`.

Cómo se lee este resultado:

- **El test es un solo día.** Con 8 fechas, `int(8 * 0.2) = 1` día de test, unas 26 filas. La accuracy
  del clasificador de 0.615 vs 0.692 son 16 vs 18 aciertos sobre 26: la diferencia son 2 predicciones.
  Es ruido, no evidencia.
- **El baseline salió alto porque ese día el mercado se movió casi todo hacia el mismo lado.** Las
  direcciones diarias de las cripto están muy correlacionadas, y ninguna feature actual capta el
  movimiento de mercado.
- **Las features son casi todas niveles** (precio de cierre, market cap, volumen, rank), que informan
  poco sobre el retorno de mañana. Con el escalado, el precio absoluto funciona como identificador del
  activo y el modelo se ajusta a eso con unas 150 filas de train. Solo `feature_price_change_pct`
  (retorno del día anterior) es una señal real.
- **`directional_accuracy` de 0.538** son 14 de 26 aciertos: prácticamente azar.

## Próximos pasos (para retomar en 2-3 semanas, con más historia)

1. **Features estacionarias** en lugar de niveles: retornos rezagados de 1 a 3 días, cambio porcentual
   de volumen y market cap, retorno promedio de todos los activos del día anterior, y volatilidad de
   los últimos días. No es viable con 8 días: un rezago de 3 días deja aún menos filas.
2. **Validación walk-forward** con varios cortes temporales, en lugar del split único.
3. Recién con un modelo que supere al baseline, armar la pestaña de forecast de la Databricks App.
   Hasta entonces, la App tiene que tolerar que `champion` no exista.
