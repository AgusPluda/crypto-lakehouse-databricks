"use client";

import { Bot, Eraser, Send, Sparkles, User, Wrench } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const MAX_CHARS = 600;
const MAX_WARMING_RETRIES = 1;
const SLOW_HINT_AFTER_MS = 8_000;

const SUGGESTIONS = [
  "¿Cuáles son los 3 activos que más subieron en el último día?",
  "¿Y los 3 que más bajaron?",
  "¿Qué se dice sobre Bitcoin en las noticias?",
  "¿Cómo está la salud del scraping de noticias?",
];

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  tools?: string[];
}

type Status = "idle" | "loading";

// react-markdown pasa el prop `node` a cada componente; se descarta para no reenviarlo al DOM.
/* eslint-disable @typescript-eslint/no-unused-vars */
const markdownComponents: Components = {
  a: ({ node, ...props }) => (
    <a
      {...props}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline underline-offset-4 break-all hover:opacity-80"
    />
  ),
  p: ({ node, ...props }) => <p {...props} className="leading-relaxed [&:not(:first-child)]:mt-3" />,
  ul: ({ node, ...props }) => <ul {...props} className="list-disc pl-5 mt-2 space-y-1" />,
  ol: ({ node, ...props }) => <ol {...props} className="list-decimal pl-5 mt-2 space-y-1" />,
  strong: ({ node, ...props }) => <strong {...props} className="font-semibold" />,
  code: ({ node, ...props }) => (
    <code {...props} className="rounded bg-background/60 px-1 py-0.5 text-[0.85em]" />
  ),
};
/* eslint-enable @typescript-eslint/no-unused-vars */

function Avatar({ role }: { role: "user" | "assistant" }) {
  return role === "assistant" ? (
    <div
      className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center text-white"
      style={{ background: "linear-gradient(135deg, #9775fa, #7048e8)" }}
    >
      <Bot className="h-4 w-4" />
    </div>
  ) : (
    <div className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center bg-muted text-muted-foreground">
      <User className="h-4 w-4" />
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  if (msg.role === "user") {
    return (
      <div className="flex items-start justify-end gap-3">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-2.5 text-sm whitespace-pre-wrap">
          {msg.content}
        </div>
        <Avatar role="user" />
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3">
      <Avatar role="assistant" />
      <div className="max-w-[85%] space-y-2">
        <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-2.5 text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {msg.content}
          </ReactMarkdown>
        </div>
        {msg.tools && msg.tools.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pl-1">
            <span className="text-xs text-muted-foreground">Consultó:</span>
            {msg.tools.map((t) => (
              <span
                key={t}
                className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 font-mono text-[11px]"
              >
                <Wrench className="h-3 w-3" />
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator({ slow }: { slow: boolean }) {
  return (
    <div className="flex items-start gap-3">
      <Avatar role="assistant" />
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3 space-y-2">
        <div className="flex items-center gap-1" aria-label="El agente está escribiendo">
          <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]" />
          <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]" />
          <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
        </div>
        {slow && (
          <p className="text-xs text-muted-foreground max-w-xs">
            El agente consulta datos y noticias en Databricks, y cada respuesta puede tardar cerca de un minuto. Si
            estaba inactivo, la primera puede tardar unos minutos más mientras despierta.
          </p>
        )}
      </div>
    </div>
  );
}

function EmptyState({ onPick, disabled }: { onPick: (q: string) => void; disabled: boolean }) {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center gap-6 px-4">
      <div
        className="h-14 w-14 rounded-2xl flex items-center justify-center text-white shadow-md"
        style={{ background: "linear-gradient(135deg, #9775fa, #7048e8)" }}
      >
        <Sparkles className="h-7 w-7" />
      </div>
      <div className="space-y-1">
        <h3 className="text-xl font-semibold">Preguntale al agente</h3>
        <p className="text-sm text-muted-foreground max-w-md">
          Consulta precios reales del mercado cripto y noticias recientes, y cita sus fuentes. Probá con una de estas:
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            disabled={disabled}
            onClick={() => onPick(q)}
            className="rounded-full border border-border bg-card px-4 py-2 text-sm hover:bg-muted transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function errorText(code: string, retryAfterSeconds?: number): string {
  switch (code) {
    case "rate_limited": {
      const mins = retryAfterSeconds ? Math.max(1, Math.ceil(retryAfterSeconds / 60)) : null;
      return `Llegaste al límite de consultas de la demo. ${mins ? `Probá de nuevo en ${mins} min.` : "Probá más tarde."}`;
    }
    case "busy":
      return "El servicio está ocupado en este momento. Probá de nuevo en unos segundos.";
    case "warming":
      return "El agente tardó demasiado en despertar. Probá de nuevo en un minuto.";
    case "invalid_request":
      return "No pude procesar ese mensaje. Revisá que no sea demasiado largo.";
    default:
      return "No se pudo consultar al agente. Probá de nuevo en un momento.";
  }
}

export function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [slow, setSlow] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const loading = status !== "idle";

  useEffect(() => {
    if (!loading) return;
    const timer = setTimeout(() => setSlow(true), SLOW_HINT_AFTER_MS);
    return () => clearTimeout(timer);
  }, [loading]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, status, slow]);

  async function send(text: string) {
    const content = text.trim();
    if (!content || loading || content.length > MAX_CHARS) return;

    const history = [...messages, { id: crypto.randomUUID(), role: "user" as const, content }];
    setMessages(history);
    setInput("");
    setError(null);
    setStatus("loading");

    const payload = JSON.stringify({
      messages: history.slice(-12).map(({ role, content: c }) => ({ role, content: c })),
    });

    try {
      for (let attempt = 0; attempt <= MAX_WARMING_RETRIES; attempt++) {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: payload,
        });
        const data = await res.json().catch(() => ({}));

        // El servidor transmite la respuesta y puede avisar el error dentro del JSON aunque el status sea 200.
        if (res.ok && !data.error && typeof data.answer === "string") {
          setMessages((prev) => [
            ...prev,
            { id: crypto.randomUUID(), role: "assistant", content: data.answer, tools: data.tools },
          ]);
          return;
        }
        if (data.error === "warming" && attempt < MAX_WARMING_RETRIES) continue;
        setError(errorText(data.error ?? "upstream", data.retryAfterSeconds));
        return;
      }
    } catch {
      setError(errorText("upstream"));
    } finally {
      setStatus("idle");
      setSlow(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card flex flex-col h-[70vh] min-h-[480px] shadow-sm">
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <span className="text-sm font-medium">Agente IA</span>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setMessages([]);
              setError(null);
            }}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs hover:bg-muted transition-colors disabled:opacity-50"
          >
            <Eraser className="h-3.5 w-3.5" />
            Nueva conversación
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        {messages.length === 0 && !loading ? (
          <EmptyState onPick={send} disabled={loading} />
        ) : (
          <div className="space-y-5">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {loading && <TypingIndicator slow={slow} />}
            {error && (
              <div className="text-destructive text-sm p-3 bg-destructive/10 rounded-lg">{error}</div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send(input);
        }}
        className="border-t border-border p-3 md:p-4 flex items-end gap-2"
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, MAX_CHARS))}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send(input);
            }
          }}
          placeholder="Escribí tu pregunta… (Enter para enviar)"
          rows={1}
          disabled={loading}
          className="flex-1 min-h-11 max-h-40 resize-none rounded-md border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-primary disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="h-11 w-11 shrink-0 rounded-md bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-50 hover:opacity-90 transition-opacity"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Enviar</span>
        </button>
      </form>
    </div>
  );
}
