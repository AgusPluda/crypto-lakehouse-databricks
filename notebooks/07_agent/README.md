# Fase 7 — Agente de IA

| paso | qué hace | artefacto |
|------|----------|-----------|
| `13_register_uc_tools.sql` | Registra 4 UC Functions como tools SQL sobre Gold | `genai.get_asset_price`, `genai.get_top_gainers`, `genai.get_top_losers`, `genai.news_pipeline_health` |
| `agent_code.py` | Agente LangGraph (ReAct) con las 4 UC Functions + un `VectorSearchRetrieverTool` sobre el índice de noticias de Fase 6. Empaquetado como **Models from Code** | registrado en UC con alias `champion` (v3) |
| `14_build_agent.py` | Driver: instala deps, loguea `agent_code.py`, registra en UC, prueba, y setea el alias `champion` | `genai.crypto_agent` |
| Model Serving endpoint | **Bloqueado, ver estado abajo** | `crypto_agent_endpoint` |

## Tools SQL (UC Functions)

Cuatro funciones en `crypto_lakehouse.genai`, cada una con `COMMENT` en la función y en cada
parámetro — es lo que el Agent Framework usa para decidir cuándo y cómo llamar cada una:

- `get_asset_price(asset_symbol)` — precio/variación/market cap de un activo puntual.
- `get_top_gainers(n_results)` / `get_top_losers(n_results)` — **separadas a propósito** en vez de
  una sola tool con un parámetro `direction`: con tool-calling por LLM, menos parámetros ambiguos
  vale más que menos tools — la elección de tool ya es la respuesta, sin que el modelo tenga que
  acertar además el valor exacto de un string.
- `news_pipeline_health()` — salud del scraping de noticias por fuente.

**Gotcha real de UC Functions:** `LIMIT` no acepta una referencia a un parámetro de la función
(necesita un literal/expresión foldeable). Workaround: `ROW_NUMBER() OVER (ORDER BY ...)` +
`WHERE rn <= n_results` en vez de `LIMIT n_results`.

## Agente (LangGraph)

`agent_code.py`: `UCFunctionToolkit(function_names=[...])` (descubre las 4 UC Functions y las
expone como tools) + `VectorSearchRetrieverTool` (wrapper específico para tool-calling, distinto
del `DatabricksVectorSearch` usado en la chain de Fase 6 — tiene `tool_name`/`tool_description`
propios) + `ChatDatabricks` + `create_react_agent` de `langgraph.prebuilt` (loop ReAct completo).

**Decisión de diseño confirmada:** el agente usa el índice de Vector Search directo como tool, no
llama a la chain de RAG ya registrada de Fase 6 — un solo LLM razonando con todas las tools parejo,
sin anidar un LLM llamando a otro ni depender de un segundo endpoint servido.

Verificado con `mlflow.langchain.autolog()` (trace completo del árbol de LangGraph:
`agent → call_model → tools → agent → ...`):
- Pregunta de precios ("¿Cuáles son los 3 activos que más subieron hoy?") → llamó
  `get_top_gainers(n_results=3)` correctamente inferido del lenguaje natural.
- Pregunta de noticias ("¿Qué se dice sobre Bitcoin en las noticias?") → llamó
  `search_crypto_news`, citó las 4 URLs reales al final de la respuesta (el system prompt tuvo que
  reforzarse explícitamente para pedir el link completo entre paréntesis — la v1 solo mencionaba
  el nombre de la fuente, no el link).

Registrado en UC (`crypto_lakehouse.genai.crypto_agent`), alias `champion` en **v3** (v1 y v2
quedaron con un `conda.yaml` no resoluble, ver abajo).

## Model Serving endpoint: BLOQUEADO (2026-09-16)

Dos problemas distintos, en orden:

1. **`ResolutionTooDeep` de pip, RESUELTO.** El primer intento de deploy (v1/v2) falló el build del
   container con `pip._vendor.resolvelib.resolvers.ResolutionTooDeep: 200000` — pip no podía
   converger a un set de versiones compatible entre `openai`, `openai-agents`, `mcp`, `langsmith`,
   `opentelemetry-sdk`, `starlette`, etc. Causa: la celda de instalación usaba
   `%pip install ... --upgrade langgraph langgraph-prebuilt mlflow`, que trajo versiones sueltas de
   más sin pines compatibles entre sí, congeladas en el `conda.yaml` que `log_model` capturó.
   **Fix:** sacar el `--upgrade`, reinstalar limpio, volver a correr `agent_code.py` +
   `log_model` → generó v3 con dependencias resolubles.
2. **`Build could not start due to an internal error`, SIN RESOLVER, pendiente de reintentar.**
   Con v3 (deps ya resueltas), el build ni arranca. Investigado: el texto exacto aparece en la doc
   oficial de Databricks *solo* bajo "Build failure due to lack of GPU availability" — pero el
   endpoint pide explícitamente `workload_type: CPU` (confirmado en el JSON del endpoint), y Free
   Edition no ofrece GPU en Model Serving de todos modos. Genie sugirió que el modelo podría tener
   deps de GPU — **descartado**, no aplica a un workload CPU. Conclusión: es el mismo texto de error
   genérico que Databricks reusa para varias fallas internas de backend; la doc solo documenta una
   causa (GPU) que no es la nuestra. Probablemente falla transitoria de infraestructura de Free
   Edition. **Mismo patrón que el cupo agotado de Fase 6: se resuelve solo, reintentar más
   tarde/al otro día.**

**Pendiente:** reintentar el deploy del endpoint (misma config: CPU Small, scale-to-zero, tracing)
sin tocar nada más. Si funciona, probar en el Review App automático, y recién ahí seguir con la
Databricks App (Gradio) + espejo en Next.js/Vercel.
