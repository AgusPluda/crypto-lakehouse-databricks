import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dl import D, PAL, LIGHT, MUTED

OUT = os.path.dirname(HERE)


def portada():
    d = D()
    d.label(100, 110, 1400, "Crypto Lakehouse", size=76, color="#f4f4fa")
    d.label(100, 215, 1700, "Pipeline de datos end-to-end en Databricks Free Edition", size=38, color="#b8b8cc")
    d.label(100, 275, 1700, "Medallion (Bronze · Silver · Gold)  →  ML  →  RAG  →  Agente de IA  →  Databricks App + web pública", size=27, color=MUTED)
    d.label(100, 325, 1500, "Agustín Pluda", size=24, color=MUTED)

    y = 470
    d.box("raw", 100, y, 200, 90, "Raw data\nCoinGecko API\nRSS feeds", "raw", 16)
    d.box("bronze", 350, y, 200, 90, "Bronze\ningesta cruda", "bronze", 16)
    d.box("silver", 600, y, 200, 90, "Silver\nlimpieza · SCD2\ndedup", "silver", 16)
    d.box("gold", 850, y, 200, 90, "Gold\nagregados\npara consumo", "gold", 16)
    d.box("ml", 1150, 380, 270, 80, "ML\nforecast + dirección", "ml", 16)
    d.box("dash", 1150, 480, 270, 80, "Dashboard\nAI/BI + Genie", "dash", 16)
    d.box("agent", 1150, 580, 270, 80, "Agente IA\nLangGraph + RAG", "agent", 16)
    d.box("app", 1500, 520, 230, 80, "Databricks App\ninicio · dashboard · agente", "app", 15)
    d.box("web", 1500, 640, 230, 80, "Espejo web público\nNext.js · Vercel", "app", 15)
    d.link("raw", "r", "bronze", "l")
    d.link("bronze", "r", "silver", "l")
    d.link("silver", "r", "gold", "l")
    d.link("gold", "r", "ml", "l")
    d.link("gold", "r", "dash", "l")
    d.link("gold", "r", "agent", "l")
    d.link("dash", "r", "app", "l")
    d.link("agent", "r", "app", "b", via=[(1615, 620)])
    d.link("ml", "r", "app", "t", via=[(1615, 420)], dashed=True, color=PAL["ml"][0])
    d.link("agent", "b", "web", "l", via=[(1285, 680)])

    d.label(100, 790, 400, "Stack", size=16, color=MUTED)
    stack = ["Delta Lake", "Unity Catalog", "Databricks Jobs", "MLflow", "Vector Search",
             "LangGraph", "Model Serving", "AppKit", "Next.js"]
    x = 100
    for i, s in enumerate(stack):
        d.box(f"s{i}", x, 820, 165, 46, s, "neutral", 15)
        x += 185
    d.save(os.path.join(OUT, "portada.excalidraw"))


def system_overview():
    d = D()
    d.label(40, 8, 1200, "Crypto Lakehouse — Arquitectura del sistema", size=28, color="#f4f4fa")

    # column geometry
    C0, C1, C2, C3, C4, C5, C6 = 50, 290, 540, 820, 1110, 1410, 1680
    heads = [("Raw data", C0, 190, "raw"), ("Bronze", C1, 200, "bronze"), ("Silver", C2, 230, "silver"),
             ("Gold", C3, 240, "gold"), ("Agente", C5, 220, "agent"), ("App", C6, 220, "app")]
    for name, x, w, kind in heads:
        d.label(x, 52, w, name, size=17, color=PAL[kind][0], align="center")
    d.label(C4 + 30, 52, 50, "ML", size=17, color=PAL["ml"][0])
    d.label(C4 + 75, 52, 100, "Dashboard", size=17, color=PAL["dash"][0])
    d.label(C4 + 190, 52, 50, "RAG", size=17, color=PAL["agent"][0])

    d.container(30, 80, 1900, 240, "crypto_gold_daily_trigger · 00:15 AM")
    d.container(30, 340, 1900, 300, "crypto_prices_pipeline · cada 30 min")
    d.container(30, 660, 1900, 300, "crypto_news_pipeline · 03:10 y 15:10")

    # band 1: daily (top)
    d.box("daily", C3, 140, 240, 70, "gold.asset_daily_summary\n(asset_daily_summary)", "gold")
    d.box("features", C4, 140, 250, 70, "mlops.features_price_daily\n(build_price_features)", "ml")
    d.box("models", C5, 130, 220, 90, "price_direction_model\nprice_forecast_model\nchampion (UC Registry)", "ml", 13)

    # band 2: prices (middle)
    d.box("coingecko", C0, 410, 190, 80, "CoinGecko API\n/coins/markets\ntop 25 dinámico", "raw")
    d.box("prices_raw", C1, 410, 200, 80, "bronze.prices_raw\n(ingest_prices)", "bronze")
    d.box("crypto_prices", C2, 380, 230, 70, "silver.crypto_prices\n(transform_crypto_prices)", "silver")
    d.box("dim_asset", C2, 500, 230, 70, "silver.dim_asset · SCD2\n(transform_dim_asset)", "silver")
    d.box("dim_current", C3, 430, 240, 70, "gold.dim_asset_current\n(gold_dim_asset_current)", "gold")
    d.box("dashboard", C4, 390, 250, 70, "AI/BI Dashboard\n+ Genie Space", "dash")
    d.box("uc", C4, 550, 250, 70, "4 UC Functions\ncrypto_lakehouse.genai", "agent")
    d.box("agent", C5, 445, 220, 110, "Agente IA\nLangGraph ReAct\n4 UC Functions + RAG\nModel Serving endpoint", "agent", 13)
    d.box("app", C6, 460, 220, 80, "Databricks App\ninicio · dashboard · agente\n(AppKit)", "app", 13)
    d.box("web", C6, 560, 220, 70, "Espejo web público\nNext.js · Vercel", "app", 13)

    # band 3: news
    d.box("rss", C0, 740, 190, 80, "RSS feeds\nCointelegraph · Decrypt\nCoinDesk", "raw")
    d.box("news_raw", C1, 740, 200, 80, "bronze.news_raw\n(ingest_news)", "bronze")
    d.box("crypto_news", C2, 730, 230, 100, "silver.crypto_news\n(transform_crypto_news)\ndedup + scraping", "silver")
    d.box("news_health", C3, 700, 240, 70, "gold.news_pipeline_health\n(gold_news_pipeline_health)", "gold")
    d.box("chunks", C3, 830, 240, 70, "genai.news_chunks\n(chunk_news)", "agent")
    d.box("index", C4, 810, 250, 100, "genai.news_chunks_index\nVector Search\n(check_new_chunks → sync)", "agent")

    # flows
    d.link("coingecko", "r", "prices_raw", "l")
    d.link("prices_raw", "r", "crypto_prices", "l")
    d.link("prices_raw", "r", "dim_asset", "l")
    d.link("crypto_prices", "r", "dim_current", "l")
    d.link("dim_asset", "r", "dim_current", "l")
    d.link("crypto_prices", "r", "daily", "l")
    d.link("daily", "r", "features", "l")
    d.link("features", "r", "models", "l", label="train manual", label_at=(1340, 216))
    d.link("rss", "r", "news_raw", "l")
    d.link("news_raw", "r", "crypto_news", "l")
    d.link("crypto_news", "r", "news_health", "l")
    d.link("crypto_news", "r", "chunks", "l")
    d.link("chunks", "r", "index", "l")

    g_dash = PAL["dash"][0]
    d.link("dim_current", "r", "dashboard", "l", color=g_dash)
    d.link("daily", "r", "dashboard", "l", via=[(1080, 175), (1080, 425)], color=g_dash)
    d.link("news_health", "r", "dashboard", "l", via=[(1090, 735), (1090, 425)], color=g_dash)

    purple = PAL["agent"][0]
    d.link("dim_current", "r", "uc", "l", color=purple)
    d.link("daily", "r", "uc", "l", via=[(1100, 175), (1100, 585)], color=purple)
    d.link("uc", "r", "agent", "l", color=purple)
    d.link("index", "r", "agent", "l", via=[(1385, 860), (1385, 500)], color=purple)
    d.link("agent", "r", "app", "l", color=purple)

    # planned (dashed)
    d.link("dashboard", "r", "app", "l", via=[(1655, 425), (1655, 500)], color=g_dash, label="embebido", label_at=(1572, 395))
    d.link("models", "r", "app", "l", via=[(1655, 175), (1655, 500)], dashed=True, color=PAL["ml"][0])

    d.link("agent", "b", "web", "l", via=[(1520, 595)], color=purple, label="OAuth M2M", label_at=(1535, 568))
    d.legend(40, 990, extra="línea punteada = planeado (pestaña Forecast en la App)")
    d.save(os.path.join(OUT, "system_overview.excalidraw"))


def agent_flow():
    d = D()
    d.label(40, 8, 1500, "Agente IA — recorrido de una consulta", size=28, color="#f4f4fa")

    d.box("user", 40, 290, 190, 80, "Usuario\n\"¿Qué se dice sobre\nBitcoin en las noticias?\"", "neutral", 13)
    d.box("app", 270, 290, 190, 80, "Databricks App\no web en Vercel", "app", 14)
    d.box("endpoint", 500, 290, 200, 80, "Model Serving\ncrypto_agent_endpoint", "agent", 14)

    d.container(740, 110, 330, 520, None, stroke=PAL["agent"][1])
    d.label(756, 122, 300, "Agente LangGraph ReAct\ncrypto_agent · champion", size=15, color=PAL["agent"][0])
    d.box("prompt", 770, 190, 270, 80, "System prompt\nsiempre usar tools\ncitar link completo", "agent", 14)
    d.box("llm", 770, 285, 270, 90, "LLM · Llama 3.3 70B\ntemperature 0.0\nrazona y elige tool", "agent", 14)
    d.box("loop", 770, 470, 270, 90, "create_react_agent\nloop: pensar → tool →\nobservar → responder", "agent", 14)

    d.label(1150, 95, 300, "4 UC Functions · genai.*", size=14, color=MUTED)
    d.box("t1", 1150, 130, 250, 56, "get_asset_price(symbol)", "agent", 14)
    d.box("t2", 1150, 212, 250, 56, "get_top_gainers(n_results)", "agent", 14)
    d.box("t3", 1150, 294, 250, 56, "get_top_losers(n_results)", "agent", 14)
    d.box("t4", 1150, 376, 250, 56, "news_pipeline_health()", "agent", 14)
    d.label(1150, 468, 300, "RAG · VectorSearchRetrieverTool", size=14, color=MUTED)
    d.box("t5", 1150, 500, 250, 70, "search_crypto_news\nHYBRID · top 4 chunks", "agent", 14)

    d.box("gold_prices", 1470, 180, 270, 120, "Tablas Gold\ngold.dim_asset_current\ngold.asset_daily_summary", "gold", 14)
    d.box("gold_health", 1470, 376, 270, 56, "gold.news_pipeline_health", "gold", 14)
    d.box("index", 1470, 490, 270, 90, "genai.news_chunks_index\nVector Search\nCointelegraph · Decrypt", "agent", 14)

    d.link("user", "r", "app", "l", both=True)
    d.link("app", "r", "endpoint", "l", both=True)
    d.poly([(700, 330), (740, 330)], both=True)
    d.link("prompt", "b", "llm", "t")
    for k in ("t1", "t2", "t3", "t4", "t5"):
        d.link("llm", "r", k, "l", both=True)
    d.link("t1", "r", "gold_prices", "l")
    d.link("t2", "r", "gold_prices", "l")
    d.link("t3", "r", "gold_prices", "l")
    d.link("t4", "r", "gold_health", "l")
    d.link("t5", "r", "index", "l")

    d.label(40, 660, 800, "Recorrido", size=22, color="#f4f4fa")
    steps = (
        "1. El usuario escribe en el chat (Databricks App o web pública).\n"
        "2. El cliente invoca crypto_agent_endpoint (Model Serving).\n"
        "3. El LLM lee el system prompt y decide qué tool necesita para responder.\n"
        "4. Llama a una UC Function (datos de precios, Gold) o a search_crypto_news (RAG sobre noticias).\n"
        "5. La tool devuelve datos reales; el LLM puede encadenar otra tool o responder.\n"
        "6. Responde citando los links completos y la respuesta vuelve al chat."
    )
    d.label(40, 700, 1300, steps, size=17, color=LIGHT)
    d.label(40, 850, 1500,
            "Ej. precios: \"top 3 que más subieron\" → get_top_gainers(n_results=3)     ·     "
            "Ej. noticias: \"qué se dice de Bitcoin\" → search_crypto_news → cita 4 URLs",
            size=15, color=MUTED)
    d.legend(40, 900)
    d.save(os.path.join(OUT, "agent_architecture.excalidraw"))


def jobs_dag():
    d = D()
    d.label(40, 8, 1500, "Databricks Jobs — dependencias entre tasks", size=28, color="#f4f4fa")
    W = 1830

    d.container(30, 70, W, 240, "crypto_prices_pipeline · cron cada 30 min")
    d.container(30, 330, W, 250, "crypto_news_pipeline · cron 03:10 y 15:10")
    d.container(30, 600, W, 200, "crypto_gold_daily_trigger · cron 00:15 AM")

    # lane 1: prices
    d.box("p_trig", 60, 160, 150, 60, "Trigger\ncada 30 min", "neutral")
    d.box("ingest_prices", 250, 160, 190, 60, "ingest_prices\n→ bronze", "bronze")
    d.box("t_prices", 490, 110, 250, 60, "transform_crypto_prices\n→ silver", "silver")
    d.box("t_dim", 490, 210, 250, 60, "transform_dim_asset\n→ silver SCD2", "silver")
    d.box("g_dim", 790, 160, 260, 60, "gold_dim_asset_current\n→ gold", "gold")
    d.link("p_trig", "r", "ingest_prices", "l")
    d.link("ingest_prices", "r", "t_prices", "l")
    d.link("ingest_prices", "r", "t_dim", "l")
    d.link("t_prices", "r", "g_dim", "l")
    d.link("t_dim", "r", "g_dim", "l")
    d.label(1090, 175, 300, "las dos transform corren en paralelo", size=14, color=MUTED)

    # lane 2: news
    d.box("n_trig", 60, 430, 150, 60, "Trigger\n03:10 y 15:10", "neutral")
    d.box("ingest_news", 250, 430, 190, 60, "ingest_news\n→ bronze", "bronze")
    d.box("t_news", 490, 430, 250, 60, "transform_crypto_news\n→ silver", "silver")
    d.box("g_health", 790, 430, 260, 60, "gold_news_pipeline_health\n→ gold", "gold")
    d.box("chunk", 1100, 430, 170, 60, "chunk_news\n→ genai", "agent")
    d.box("check", 1330, 420, 230, 80, "check_new_chunks\nCondition:\nnew_chunks_count > 0", "neutral")
    d.box("sync", 1620, 430, 210, 60, "sync_vector_index\n→ índice Vector Search", "agent")
    d.link("n_trig", "r", "ingest_news", "l")
    d.link("ingest_news", "r", "t_news", "l")
    d.link("t_news", "r", "g_health", "l")
    d.link("g_health", "r", "chunk", "l")
    d.link("chunk", "r", "check", "l")
    d.link("check", "r", "sync", "l", label="True", label_at=(1572, 435))
    d.label(1100, 380, 400, "chunk_news publica el Task Value new_chunks_count", size=14, color=MUTED)
    d.label(1330, 520, 500, "si es 0, sync_vector_index queda Excluded\ny el índice no se toca", size=14, color=MUTED)

    # lane 3: daily
    d.box("d_trig", 60, 680, 150, 60, "Trigger\n00:15 AM", "neutral")
    d.box("daily", 250, 680, 300, 60, "asset_daily_summary\n→ gold (solo días cerrados)", "gold")
    d.box("feat", 610, 680, 310, 60, "build_price_features\n→ mlops.features_price_daily", "ml")
    manual = d.box("manual", 990, 665, 300, 90, "Entrenamiento manual\n10_train_price_direction\n11_train_price_forecast", "ml", 13)
    manual["strokeStyle"] = "dashed"
    d.link("d_trig", "r", "daily", "l")
    d.link("daily", "r", "feat", "l")
    d.link("feat", "r", "manual", "l", dashed=True)
    d.label(1320, 700, 400, "fuera del Job: se corre cuando\nhay suficiente historia", size=14, color=MUTED)

    d.legend(40, 830, extra="Condition y Trigger en gris · punteado = manual")
    d.save(os.path.join(OUT, "jobs_dag.excalidraw"))


portada()
system_overview()
agent_flow()
jobs_dag()
