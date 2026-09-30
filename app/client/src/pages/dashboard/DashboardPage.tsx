const WORKSPACE_URL = 'https://dbc-80cab894-0807.cloud.databricks.com';
const WORKSPACE_ID = '7474660523287528';
const DASHBOARD_ID = '01f1aeef719516ab8a9002d44b950519';

const EMBED_URL = `${WORKSPACE_URL}/embed/dashboardsv3/${DASHBOARD_ID}?o=${WORKSPACE_ID}`;
const DASHBOARD_URL = `${WORKSPACE_URL}/dashboardsv3/${DASHBOARD_ID}/published?o=${WORKSPACE_ID}`;

export function DashboardPage() {
  return (
    <div className="space-y-4 w-full max-w-7xl mx-auto">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
          <p className="text-sm text-muted-foreground mt-1">
            AI/BI Dashboard &quot;Crypto Lakehouse - Overview&quot; sobre las tablas Gold.
          </p>
        </div>
        <a
          href={DASHBOARD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary underline underline-offset-4 hover:text-primary/80 whitespace-nowrap"
        >
          Abrir en Databricks →
        </a>
      </div>

      <iframe
        title="Crypto Lakehouse - Overview"
        src={EMBED_URL}
        className="w-full rounded-lg border h-[calc(100vh-11rem)] min-h-[600px]"
      />
    </div>
  );
}
