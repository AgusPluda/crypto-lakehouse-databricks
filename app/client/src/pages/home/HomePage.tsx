import { NavLink } from 'react-router';
import { Badge, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@databricks/appkit-ui/react';
import { ArrowRight, Bot, LayoutDashboard, TrendingUp } from 'lucide-react';
import { PALETTE, REPO_URL } from '../../palette';

const STACK = ['Delta Lake', 'Unity Catalog', 'Databricks Jobs', 'MLflow', 'Vector Search', 'LangGraph', 'Model Serving', 'AppKit'];

function Chip({ color, title, subtitle }: { color: string; title: string; subtitle: string }) {
  return (
    <div className="rounded-lg px-4 py-3 text-center min-w-28 shadow-sm" style={{ background: color, color: '#111' }}>
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
  to,
  cta,
  soon,
}: {
  icon: React.ReactNode;
  accent: string;
  title: string;
  description: string;
  to?: string;
  cta?: string;
  soon?: boolean;
}) {
  const body = (
    <Card className={`h-full transition-shadow ${to ? 'hover:shadow-lg' : 'opacity-80'}`} style={{ borderTop: `3px solid ${accent}` }}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div style={{ color: accent }}>{icon}</div>
          {soon && <Badge variant="secondary">Próximamente</Badge>}
        </div>
        <CardTitle className="mt-2">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      {cta && (
        <CardContent>
          <span className="text-sm font-medium inline-flex items-center gap-1" style={{ color: accent }}>
            {cta} <ArrowRight className="h-4 w-4" />
          </span>
        </CardContent>
      )}
    </Card>
  );
  return to ? (
    <NavLink to={to} className="block h-full">
      {body}
    </NavLink>
  ) : (
    body
  );
}

export function HomePage() {
  return (
    <div className="max-w-5xl mx-auto space-y-12 pt-6 pb-10">
      <section className="text-center space-y-4">
        <Badge variant="outline">Databricks Free Edition · Unity Catalog</Badge>
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">Crypto Lakehouse</h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Pipeline de datos end-to-end sobre el mercado cripto: ingesta desde CoinGecko y RSS, arquitectura medallion,
          ML, RAG y un agente de IA que responde con datos reales.
        </p>
      </section>

      <section className="rounded-xl border bg-card p-6 md:p-8">
        <h3 className="text-sm font-medium text-muted-foreground text-center mb-5">Del dato crudo al agente</h3>
        <PipelineStrip />
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <FeatureCard
          icon={<LayoutDashboard className="h-6 w-6" />}
          accent={PALETTE.dash}
          title="Dashboard"
          description="KPIs del mercado, leaderboard de los top 25, movers del día y salud del pipeline de noticias."
          to="/dashboard"
          cta="Ver dashboard"
        />
        <FeatureCard
          icon={<Bot className="h-6 w-6" />}
          accent={PALETTE.agent}
          title="Agente IA"
          description="Un agente LangGraph que consulta precios con UC Functions sobre Gold y noticias con RAG, y cita sus fuentes."
          to="/agent"
          cta="Hablar con el agente"
        />
        <FeatureCard
          icon={<TrendingUp className="h-6 w-6" />}
          accent={PALETTE.ml}
          title="Forecast"
          description="Predicción de retorno diario por activo. Se habilita cuando un modelo supere a su baseline."
          soon
        />
      </section>

      <footer className="space-y-3 text-center">
        <div className="flex flex-wrap justify-center gap-2">
          {STACK.map((s) => (
            <Badge key={s} variant="secondary">
              {s}
            </Badge>
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
  );
}
