export type UpstreamKind = "warming" | "busy" | "auth" | "error";

export class UpstreamError extends Error {
  constructor(
    public kind: UpstreamKind,
    detail?: string,
  ) {
    super(detail ?? kind);
  }
}

function env(name: string): string {
  const value = process.env[name];
  if (!value) throw new UpstreamError("error", `Falta la variable de entorno ${name}`);
  return value;
}

const host = () => env("DATABRICKS_HOST").replace(/\/$/, "");

let cached: { token: string; expiresAt: number } | null = null;

async function getToken(): Promise<string> {
  if (cached && cached.expiresAt - 60_000 > Date.now()) return cached.token;

  const credentials = Buffer.from(
    `${env("DATABRICKS_CLIENT_ID")}:${env("DATABRICKS_CLIENT_SECRET")}`,
  ).toString("base64");

  const res = await fetch(`${host()}/oidc/v1/token`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${credentials}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "client_credentials",
      scope: process.env.DATABRICKS_OAUTH_SCOPE ?? "model-serving",
    }),
    signal: AbortSignal.timeout(15_000),
    cache: "no-store",
  }).catch(() => {
    throw new UpstreamError("error", "No se pudo contactar el servidor de OAuth");
  });

  if (!res.ok) throw new UpstreamError("auth", `OAuth respondió ${res.status}`);

  const data = (await res.json()) as { access_token: string; expires_in: number };
  cached = { token: data.access_token, expiresAt: Date.now() + data.expires_in * 1000 };
  return cached.token;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export async function invokeAgent(messages: ChatTurn[], timeoutMs: number): Promise<unknown> {
  const token = await getToken();
  const endpoint = env("DATABRICKS_SERVING_ENDPOINT");

  let res: Response;
  try {
    res = await fetch(`${host()}/serving-endpoints/${endpoint}/invocations`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
      signal: AbortSignal.timeout(timeoutMs),
      cache: "no-store",
    });
  } catch (e) {
    // El endpoint tiene scale-to-zero: si estaba dormido, el primer pedido no llega a responder a tiempo.
    if (e instanceof Error && (e.name === "TimeoutError" || e.name === "AbortError")) {
      throw new UpstreamError("warming");
    }
    throw new UpstreamError("error", "No se pudo contactar el endpoint");
  }

  if (res.status === 401 || res.status === 403) {
    cached = null;
    throw new UpstreamError("auth", `El endpoint respondió ${res.status}`);
  }
  if (res.status === 429) throw new UpstreamError("busy");
  if (res.status === 502 || res.status === 503 || res.status === 504) throw new UpstreamError("warming");
  if (!res.ok) throw new UpstreamError("error", `El endpoint respondió ${res.status}`);

  return res.json();
}
