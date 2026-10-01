import { NextResponse } from "next/server";
import { extractAnswer, extractTools } from "@/lib/agent-response";
import { invokeAgent, UpstreamError, type ChatTurn } from "@/lib/databricks";
import { checkLimit, recordHit } from "@/lib/rate-limit";

export const runtime = "nodejs";
// El agente puede tardar ~40 s por respuesta, y más si el endpoint estaba dormido (scale-to-zero).
export const maxDuration = 300;

const MAX_MESSAGE_CHARS = 600;
const MAX_TURNS = 12;
const MAX_TOTAL_CHARS = 4000;
const UPSTREAM_TIMEOUT_MS = 270_000;
const KEEPALIVE_MS = 10_000;

function parseMessages(body: unknown): ChatTurn[] | null {
  const raw = (body as { messages?: unknown })?.messages;
  if (!Array.isArray(raw) || raw.length === 0 || raw.length > MAX_TURNS) return null;

  const turns: ChatTurn[] = [];
  let total = 0;
  for (const item of raw) {
    const { role, content } = (item ?? {}) as { role?: unknown; content?: unknown };
    if ((role !== "user" && role !== "assistant") || typeof content !== "string") return null;
    const text = content.trim();
    if (!text || text.length > MAX_MESSAGE_CHARS) return null;
    total += text.length;
    turns.push({ role, content: text });
  }
  if (total > MAX_TOTAL_CHARS || turns[turns.length - 1].role !== "user") return null;
  return turns;
}

function clientIp(req: Request): string {
  return req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
}

export async function POST(req: Request) {
  const ip = clientIp(req);

  const limit = checkLimit(ip);
  if (!limit.ok) {
    return NextResponse.json(
      { error: "rate_limited", retryAfterSeconds: limit.retryAfterSeconds },
      { status: 429, headers: { "Retry-After": String(limit.retryAfterSeconds) } },
    );
  }

  const body = await req.json().catch(() => null);
  const messages = parseMessages(body);
  if (!messages) {
    return NextResponse.json({ error: "invalid_request" }, { status: 400 });
  }

  // La respuesta se transmite con espacios de keepalive mientras el agente trabaja: JSON admite espacios
  // iniciales, y así ningún proxy corta la conexión por inactividad. Como el status se manda antes de
  // conocer el resultado, el éxito o el error viajan dentro del JSON.
  const encoder = new TextEncoder();
  let ping: ReturnType<typeof setInterval> | undefined;

  const stream = new ReadableStream({
    async start(controller) {
      ping = setInterval(() => controller.enqueue(encoder.encode(" ")), KEEPALIVE_MS);
      const finish = (payload: unknown) => {
        clearInterval(ping);
        controller.enqueue(encoder.encode(JSON.stringify(payload)));
        controller.close();
      };

      try {
        const data = await invokeAgent(messages, UPSTREAM_TIMEOUT_MS);
        const answer = extractAnswer(data);
        if (!answer) return finish({ error: "empty_answer" });
        recordHit(ip);
        return finish({ answer, tools: extractTools(data) });
      } catch (e) {
        if (e instanceof UpstreamError) {
          if (e.kind === "warming") return finish({ error: "warming" });
          if (e.kind === "busy") return finish({ error: "busy" });
          console.error("[chat] upstream error:", e.kind, e.message);
        } else {
          console.error("[chat] unexpected error:", e);
        }
        return finish({ error: "upstream" });
      }
    },
    cancel() {
      clearInterval(ping);
    },
  });

  return new Response(stream, {
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}
