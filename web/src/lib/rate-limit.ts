// Límite en memoria, por instancia. Es un freno razonable para una demo, no una garantía: en serverless
// cada instancia tiene su propio contador. El tope real lo pone el cupo del Service Principal en Databricks.

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

const PER_IP_PER_HOUR = 20;
const GLOBAL_PER_DAY = 400;

const hits = new Map<string, number[]>();
let globalHits: number[] = [];

function prune(list: number[], windowMs: number, now: number): number[] {
  return list.filter((t) => now - t < windowMs);
}

export function checkLimit(ip: string): { ok: true } | { ok: false; retryAfterSeconds: number } {
  const now = Date.now();
  globalHits = prune(globalHits, DAY, now);
  if (globalHits.length >= GLOBAL_PER_DAY) {
    return { ok: false, retryAfterSeconds: Math.ceil((DAY - (now - globalHits[0])) / 1000) };
  }
  const mine = prune(hits.get(ip) ?? [], HOUR, now);
  hits.set(ip, mine);
  if (mine.length >= PER_IP_PER_HOUR) {
    return { ok: false, retryAfterSeconds: Math.ceil((HOUR - (now - mine[0])) / 1000) };
  }
  return { ok: true };
}

export function recordHit(ip: string): void {
  const now = Date.now();
  globalHits.push(now);
  const mine = hits.get(ip) ?? [];
  mine.push(now);
  hits.set(ip, mine);
}
