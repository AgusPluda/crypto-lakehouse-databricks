# Fase 7 — Agente de IA

| paso | qué hace | artefacto |
|------|----------|-----------|
| `13_register_uc_tools.sql` | Registra 4 UC Functions como tools SQL sobre Gold | `genai.get_asset_price`, `genai.get_top_gainers`, `genai.get_top_losers`, `genai.news_pipeline_health` |
| `agent_code.py` | Agente LangGraph (ReAct) con las 4 UC Functions + un `VectorSearchRetrieverTool` sobre el índice de noticias de Fase 6. Empaquetado como **Models from Code** | registrado en UC con alias `champion` (v11) |
| `14_build_agent.py` | Driver: instala deps, arma un `pip_requirements`/`resources` curados, loguea `agent_code.py`, registra en UC, prueba, y setea el alias `champion` | `genai.crypto_agent` |
| Model Serving endpoint | **Desplegado y verificado (2026-09-20)** | `crypto_agent_endpoint` |

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

`agent_code.py`: `UCFunctionToolkit(client=uc_client, function_names=[...])` (descubre las 4 UC
Functions y las expone como tools) + `VectorSearchRetrieverTool` (wrapper específico para
tool-calling, distinto del `DatabricksVectorSearch` usado en la chain de Fase 6 — tiene
`tool_name`/`tool_description` propios) + `ChatDatabricks` + `create_react_agent` de
`langgraph.prebuilt` (loop ReAct completo).

**Decisión de diseño confirmada:** el agente usa el índice de Vector Search directo como tool, no
llama a la chain de RAG ya registrada de Fase 6 — un solo LLM razonando con todas las tools parejo,
sin anidar un LLM llamando a otro ni depender de un segundo endpoint servido.

Verificado en producción (Model Serving, no solo en la notebook) con las dos preguntas de siempre:
- Pregunta de precios ("¿Cuáles son los 3 activos que más subieron hoy?") → llamó
  `get_top_gainers(n_results=3)` correctamente inferido del lenguaje natural, devolvió Litecoin,
  USDS y Tether con sus `price_change_pct` reales.
- Pregunta de noticias ("¿Qué se dice sobre Bitcoin en las noticias?") → llamó
  `search_crypto_news`, citó 4 URLs reales de Cointelegraph/Decrypt entre paréntesis (el system
  prompt tuvo que reforzarse explícitamente para pedir el link completo — la v1 solo mencionaba el
  nombre de la fuente, no el link).

Registrado en UC (`crypto_lakehouse.genai.crypto_agent`), alias `champion` en **v11**.

## Model Serving endpoint: saga completa del deploy (2026-09-16 a 2026-09-20)

Le llevó 11 versiones del modelo y cinco causas de fallo distintas llegar a un deploy exitoso.
Documentado en detalle porque cada una fue un problema real, no ruido:

1. **`ResolutionTooDeep` de pip (v1/v2).** `%pip install ... --upgrade langgraph langgraph-prebuilt
   mlflow` trajo versiones sueltas sin pines compatibles entre `openai`/`openai-agents`/`mcp`/
   `langsmith`/`opentelemetry-sdk`/`starlette`, congeladas en el `conda.yaml` que `log_model`
   capturó. pip nunca convergía (200000 rounds de backtracking). Sacar el `--upgrade` **no alcanzó**
   — el diagnóstico quedó incompleto hasta el punto 3.
2. **`Build could not start due to an internal error` (v3), infraestructura de Free Edition.** Con
   v3 el build ni arrancaba. Se descartó la causa "GPU" que sugiere la doc oficial (el workload es
   `CPU` explícito). Era el mismo patrón que el cupo agotado de Vector Search de Fase 6: se
   resolvió solo reintentando otro día — el cupo diario de compute serverless de la cuenta se
   había agotado, primero por los reintentos de deploy en sí, y también compitiendo con toda la
   experimentación (`%pip install`/restarts) de la misma sesión.
3. **Conflicto real `langchain` vs `langgraph` vs `langgraph-prebuilt` (v3→v5).** Cuando el build
   por fin avanzó lo suficiente como para llegar a `conda-env-create`, volvió a fallar con
   `ResolutionTooDeep` — reveló que `langchain==1.2.10` exige `langgraph<1.1.0`, pero una línea
   suelta nunca limpiada (`%pip install "langgraph>=1.2.0" "langgraph-prebuilt>=1.0.13"`) forzaba lo
   contrario. Peor: `langgraph-prebuilt>=1.0.9` importa `ExecutionInfo`/`ServerInfo` de
   `langgraph.runtime`, API que sólo existe desde `langgraph>=1.1.5` — bug conocido, ver
   [issue #7404 de langchain-ai/langgraph](https://github.com/langchain-ai/langgraph/issues/7404).
   **Fix:** `langgraph==1.0.10` + `langgraph-prebuilt==1.0.8` (versiones compatibles entre sí y con
   `langchain<1.1.0`), fijadas también como `extra_pip_requirements` en `log_model` — porque el
   `requirements.txt` autoinferido por `mlflow` no capturaba estos dos paquetes, dejando el build
   del container libre de volver a resolver la versión rota.
4. **`ResolutionImpossible` real entre `openai` y `openai-agents` (v6→v9).** `extra_pip_requirements`
   sólo agrega, no reemplaza — el `requirements.txt` inferido seguía arrastrando basura del kernel
   (`databricks-connect`, IPython/Jupyter, validadores de JSON Schema) ajena al agente. Se reemplazó
   por `pip_requirements=filtered`, una lista curada a partir de `pip freeze` filtrando paquetes de
   sistema/IDE/no relevantes (ver función `keep()` en `14_build_agent.py`). Eso expuso un conflicto
   real: `langchain-openai==1.1.6` exige `openai<3.0.0`, pero `openai-agents==0.22.2` (dependencia
   transitiva de `databricks-openai`, no usada por nuestro agente) exige `openai>=3.0.0` —
   imposible que coexistan. **Fix:** pinnear `openai==2.7.1` + `openai-agents==0.5.0` (versión vieja
   de `openai-agents` que sí acepta `openai<3`, y que `databricks-openai==0.17.1` permite sin techo).
5. **`system_cred_injection_suspected` en `mlflow_parse` (v10).** Con las deps por fin resueltas, el
   build container terminó bien pero el modelo no cargaba: `UCFunctionToolkit` sin cliente explícito
   funciona en una notebook interactiva (hay un cliente ambiente implícito) pero no dentro del
   container aislado del endpoint. **Fix 1:** pasar `client=DatabricksFunctionClient()` explícito al
   crear el `UCFunctionToolkit` en `agent_code.py`. **Fix 2 (la causa real del error de
   credenciales):** declarar los recursos Databricks-managed del agente (las 4 UC Functions, el
   índice de Vector Search, y el serving endpoint del LLM) en el parámetro `resources=[...]` de
   `log_model()` (`mlflow.models.resources.DatabricksFunction/DatabricksVectorSearchIndex/
   DatabricksServingEndpoint`) — es el mecanismo documentado de "automatic authentication
   passthrough": sin declararlos, Model Serving no sabe qué credenciales inyectarle al container
   para esos recursos específicos.

**v11: deploy exitoso.** Verificado en el AI Playground contra el endpoint real (no solo en la
notebook) con las dos preguntas de siempre — tools SQL y RAG ambas funcionando con datos reales.

**Lección general para este tipo de agentes:** nunca confiar en que `mlflow.langchain.log_model`
infiera correctamente todo el árbol de dependencias transitivas relevantes — para un stack con
tantos paquetes en movimiento rápido (LangChain/LangGraph/Databricks), hay que curar `pip_requirements`
a mano a partir de un `pip freeze` real y verificado, y declarar `resources` explícitamente para
cualquier recurso Databricks-managed que el agente use en tiempo de serving.
