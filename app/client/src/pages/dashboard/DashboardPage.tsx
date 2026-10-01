import { Skeleton } from '@databricks/appkit-ui/react';
import { ExternalLink } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useState } from 'react';

const WORKSPACE_URL = 'https://dbc-80cab894-0807.cloud.databricks.com';
const WORKSPACE_ID = '7474660523287528';
const DASHBOARD_ID = '01f1aeef719516ab8a9002d44b950519';

const EMBED_URL = `${WORKSPACE_URL}/embed/dashboardsv3/${DASHBOARD_ID}?o=${WORKSPACE_ID}`;
const DASHBOARD_URL = `${WORKSPACE_URL}/dashboardsv3/${DASHBOARD_ID}/published?o=${WORKSPACE_ID}`;

export function DashboardPage() {
  const [loaded, setLoaded] = useState(false);
  // El embed de AI/BI siempre se muestra en modo claro. En el tema oscuro se invierte con un filtro y se rota el
  // tono 180° para que los colores de los gráficos conserven su matiz.
  const { resolvedTheme } = useTheme();
  const darkFilter = resolvedTheme === 'dark' ? 'invert(0.92) hue-rotate(180deg)' : undefined;

  return (
    <div className="space-y-4 w-full">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
          <p className="text-sm text-muted-foreground mt-1">
            AI/BI Dashboard sobre las tablas Gold, actualizadas a diario por los Jobs de orquestación.
          </p>
        </div>
        <a
          href={DASHBOARD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm text-primary underline underline-offset-4 hover:opacity-80 whitespace-nowrap"
        >
          Abrir en Databricks
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      <div className="relative rounded-xl border bg-card overflow-hidden shadow-sm h-[calc(100vh-12rem)] min-h-[600px]">
        {!loaded && (
          <div className="absolute inset-0 p-6 space-y-4 bg-card">
            <Skeleton className="h-8 w-1/3" />
            <div className="grid grid-cols-4 gap-4">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
            <Skeleton className="h-64 w-full" />
          </div>
        )}
        <iframe
          title="Crypto Lakehouse - Overview"
          src={EMBED_URL}
          onLoad={() => setLoaded(true)}
          style={{ filter: darkFilter }}
          className="w-full h-full"
        />
      </div>
    </div>
  );
}
