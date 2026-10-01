// Diagnóstico de credenciales: node --env-file=.env.local scripts/check-auth.mjs
// Imprime códigos HTTP y el error de Databricks. Nunca imprime el secret ni el token.

const host = (process.env.DATABRICKS_HOST ?? "").replace(/\/$/, "");
const id = process.env.DATABRICKS_CLIENT_ID ?? "";
const secret = process.env.DATABRICKS_CLIENT_SECRET ?? "";
const endpoint = process.env.DATABRICKS_SERVING_ENDPOINT ?? "";
const configuredScope = process.env.DATABRICKS_OAUTH_SCOPE;

console.log("DATABRICKS_HOST:", host || "(vacío)");
console.log("DATABRICKS_CLIENT_ID:", id ? `${id.slice(0, 8)}… (${id.length} caracteres)` : "(vacío)");
console.log("DATABRICKS_CLIENT_SECRET:", secret ? `definido (${secret.length} caracteres)` : "(vacío)");
console.log("DATABRICKS_SERVING_ENDPOINT:", endpoint || "(vacío)");
console.log("DATABRICKS_OAUTH_SCOPE:", configuredScope ?? "(no definido, se usa all-apis)");
console.log();

if (!host || !id || !secret || !endpoint) {
  console.log("Faltan variables: revisá que .env.local esté en la carpeta web/.");
  process.exit(1);
}

const credentials = Buffer.from(`${id}:${secret}`).toString("base64");
// null = pedir el token sin indicar scope (Databricks usa los scopes asignados al secret)
const scopes = [
  ...new Set([
    configuredScope,
    "model-serving",
    "serving-endpoints",
    "serving.serving-endpoints",
    "serving",
    "ai-gateway",
    "ai-functions",
    "all-apis",
  ]),
].filter(Boolean);

let token = null;
for (const scope of scopes) {
  const params = { grant_type: "client_credentials" };
  if (scope) params.scope = scope;
  const res = await fetch(`${host}/oidc/v1/token`, {
    method: "POST",
    headers: { Authorization: `Basic ${credentials}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(params),
  });
  const body = await res.text();
  const label = scope ? `scope "${scope}"` : "sin scope";
  if (res.ok) {
    const parsed = JSON.parse(body);
    token = parsed.access_token;
    console.log(`Token ${label}: OK (${res.status}); scope concedido: ${parsed.scope ?? "(no informado)"}`);
    break;
  }
  console.log(`Token ${label}: ERROR ${res.status} -> ${body.slice(0, 300)}`);
}

if (!token) process.exit(1);

const res = await fetch(`${host}/serving-endpoints/${endpoint}/invocations`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  body: JSON.stringify({ messages: [{ role: "user", content: "hola" }] }),
  signal: AbortSignal.timeout(55_000),
}).catch((e) => ({ failed: e.name }));

if (res.failed) {
  console.log("Invocación: sin respuesta a tiempo (", res.failed, ") -> probablemente el endpoint está despertando.");
} else {
  const body = await res.text();
  console.log(`Invocación: ${res.status} -> ${body.slice(0, 200).replace(/\s+/g, " ")}`);
}
