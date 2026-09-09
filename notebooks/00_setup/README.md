# Fase 0 — Fundacional

Crea la base sobre la que se apoya todo el proyecto:

- El catalog **`crypto_lakehouse`** en Unity Catalog.
- Los 5 schemas: `bronze`, `silver`, `gold`, `mlops`, `genai`.
- (Opcional) un `MANAGED LOCATION` y los `GRANT` que muestren permisos distintos por capa.

El notebook se escribe y ejecuta en el workspace de Databricks Free Edition y se exporta acá como
*Source* cuando queda funcionando.
