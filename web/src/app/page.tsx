import { ArrowRight, Bot, LayoutDashboard, TrendingUp } from "lucide-react";
import Link from "next/link";
import { PALETTE, REPO_URL } from "@/lib/site";

const STACK = [
  "Delta Lake",
  "Unity Catalog",
  "Databricks Jobs",
  "MLflow",
  "Vector Search",
  "LangGraph",
  "Model Serving",
  "AppKit",
];

function Chip({ color, title, subtitle }: { color: string; title: string; subtitle: string }) {
  return (
    <div className="rounded-lg px-4 py-3 text-center min-w-28 shadow-sm" style={{ background: color, color: "#111" }}>
      <div className="text-sm font-semibold">{title}</div>
      <div className="text-xs opacity-80">{subtitle}</div>
    </div>
  );
}

function PipelineStrip() {
  const arrow = <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 hidden sm:block" />;
  return (
    <div className="flex flex-wrap items-center justify-center gap-3">
      <Chip color={PALETTE.raw} title="Raw data" subtitle="CoinGecko · RSS" />
      {arrow}
      <Chip color={PALETTE.bronze} title="Bronze" subtitle="ingesta cruda" />
      {arrow}
      <Chip color={PALETTE.silver} title="Silver" subtitle="limpieza · SCD2" />
      {arrow}
      <Chip color={PALETTE.gold} title="Gold" subtitle="marts" />
      {arrow}
      <div className="flex flex-col gap-2">
        <Chip color={PALETTE.ml} title="ML" subtitle="MLflow" />
        <Chip color={PALETTE.dash} title="Dashboard" subtitle="AI/BI" />
        <Chip color={PALETTE.agent} title="Agente IA" subtitle="LangGraph + RAG" />
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  accent,
  title,
  description,
  href,
  cta,
  note,
}: {
  icon: React.ReactNode;
  accent: string;
  title: string;
  description: string;
  href?: string;
  cta?: string;
  note?: string;
}) {
  const body = (
    <div
      className={`h-full rounded-xl border border-border bg-card p-5 space-y-2 transition-shadow ${
        href ? "hover:shadow-lg" : "opacity-80"
      }`}
      style={{ borderTop: `3px solid ${accent}` }}
    >
      <div className="flex items-center justify-between">
        <div style={{ color: accent }}>{icon}</div>
        {note && <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">{note}</span>}
      </div>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
      {cta && (
        <span className="text-sm font-medium inline-flex items-center gap-1 pt-1" style={{ color: accent }}>
          {cta} <ArrowRight className="h-4 w-4" />
        </span>
      )}
    </div>
  );
  return href ? (
    <Link href={href} className="block h-full">
      {body}
    </Link>
  ) : (
    body
  );
}

export default function Home() {
  return (
    <main className="flex-1 px-4 md:px-6 py-8 md:py-12">
      <div className="max-w-5xl mx-auto space-y-12">
        <section className="text-center space-y-4">
          <span className="inline-block rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
            Databricks Free Edition · Unity Catalog
          </span>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Crypto Lakehouse</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-balance">
            Pipeline de datos end-to-end sobre el mercado cripto: ingesta desde CoinGecko y RSS, arquitectura medallion,
            ML, RAG y un agente de IA que responde con datos reales.
          </p>
          <div className="pt-2">
            <Link
              href="/agente"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity"
            >
              Probar el agente <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card p-6 md:p-8">
          <h2 className="text-sm font-medium text-muted-foreground text-center mb-5">Del dato crudo al agente</h2>
          <PipelineStrip />
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <FeatureCard
            icon={<LayoutDashboard className="h-6 w-6" />}
            accent={PALETTE.dash}
            title="Dashboard"
            description="KPIs del mercado, leaderboard de los top 25, movers del día y salud del pipeline de noticias, con Genie para preguntar sobre los gráficos."
            note="Solo en Databricks"
          />
          <FeatureCard
            icon={<Bot className="h-6 w-6" />}
            accent={PALETTE.agent}
            title="Agente IA"
            description="Un agente LangGraph que consulta precios con UC Functions sobre Gold y noticias con RAG, y cita sus fuentes."
            href="/agente"
            cta="Hablar con el agente"
          />
          <FeatureCard
            icon={<TrendingUp className="h-6 w-6" />}
            accent={PALETTE.ml}
            title="Forecast"
            description="Predicción de retorno diario por activo. Se habilita cuando un modelo supere a su baseline."
            note="Próximamente"
          />
        </section>

        <footer className="space-y-3 text-center">
          <div className="flex flex-wrap justify-center gap-2">
            {STACK.map((s) => (
              <span key={s} className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">
                {s}
              </span>
            ))}
          </div>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
          >
            Código en GitHub
          </a>
        </footer>
      </div>
    </main>
  );
}
