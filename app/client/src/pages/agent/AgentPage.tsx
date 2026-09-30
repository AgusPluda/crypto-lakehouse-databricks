import { Badge, Button, Textarea, useServingInvoke } from '@databricks/appkit-ui/react';
import { Bot, Eraser, Send, Sparkles, User, Wrench } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SUGGESTIONS = [
  '¿Cuáles son los 3 activos que más subieron hoy?',
  '¿Y los 3 que más bajaron?',
  '¿Qué se dice sobre Bitcoin en las noticias?',
  '¿Cómo está la salud del scraping de noticias?',
];

interface ChatChoice {
  message?: { content?: string };
}

interface AgentMessage {
  type?: string;
  role?: string;
  name?: string;
  content?: unknown;
}

interface ChatResponse {
  choices?: ChatChoice[];
  messages?: AgentMessage[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools?: string[];
}

function contentToText(content: unknown): string {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .map((part) => (typeof part === 'string' ? part : ((part as { text?: string })?.text ?? '')))
      .join('');
  }
  return '';
}

function extractContent(data: unknown): string {
  const resp = data as ChatResponse;

  // Agente LangGraph: la respuesta final es el último mensaje 'ai' con texto
  // (los mensajes 'ai' que solo llaman tools vienen con content vacío).
  const finalAnswer = [...(resp?.messages ?? [])]
    .reverse()
    .find((m) => (m.type === 'ai' || m.role === 'assistant') && contentToText(m.content).trim());
  if (finalAnswer) return contentToText(finalAnswer.content);

  return resp?.choices?.[0]?.message?.content ?? JSON.stringify(data);
}

// Tools invocadas en el turno actual (los mensajes 'tool' posteriores al último mensaje del usuario).
function extractTools(data: unknown): string[] {
  const msgs = (data as ChatResponse)?.messages ?? [];
  let lastUser = -1;
  msgs.forEach((m, i) => {
    if (m.type === 'human' || m.role === 'user') lastUser = i;
  });
  const names = msgs
    .slice(lastUser + 1)
    .filter((m) => m.type === 'tool' && m.name)
    .map((m) => (m.name as string).split('__').pop() as string);
  return [...new Set(names)];
}

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
  code: ({ node, ...props }) => <code {...props} className="rounded bg-background/60 px-1 py-0.5 text-[0.85em]" />,
};

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
            El agente puede estar despertando tras un rato inactivo. El primer mensaje puede tardar hasta un par de
            minutos.
          </p>
        )}
      </div>
    </div>
  );
}

function Avatar({ role }: { role: 'user' | 'assistant' }) {
  return role === 'assistant' ? (
    <div
      className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center text-white"
      style={{ background: 'linear-gradient(135deg, #9775fa, #7048e8)' }}
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
  if (msg.role === 'user') {
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
              <Badge key={t} variant="outline" className="gap-1 font-mono text-[11px]">
                <Wrench className="h-3 w-3" />
                {t}
              </Badge>
            ))}
          </div>
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
        style={{ background: 'linear-gradient(135deg, #9775fa, #7048e8)' }}
      >
        <Sparkles className="h-7 w-7" />
      </div>
      <div className="space-y-1">
        <h3 className="text-xl font-semibold text-foreground">Preguntale al agente</h3>
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
            className="rounded-full border bg-card px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

export function AgentPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [slow, setSlow] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const { invoke, loading, error } = useServingInvoke({ messages: [] });

  useEffect(() => {
    if (!loading) {
      setSlow(false);
      return;
    }
    const timer = setTimeout(() => setSlow(true), 8000);
    return () => clearTimeout(timer);
  }, [loading]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  function send(text: string) {
    const content = text.trim();
    if (!content || loading) return;

    const userMessage: Message = { id: crypto.randomUUID(), role: 'user', content };
    const fullMessages = [
      ...messages.map(({ role, content: c }) => ({ role, content: c })),
      { role: 'user' as const, content },
    ];

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    void invoke({ messages: fullMessages }).then((result) => {
      if (result) {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: extractContent(result),
            tools: extractTools(result),
          },
        ]);
      }
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    send(input);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Agente IA</h2>
          <p className="text-sm text-muted-foreground mt-1">
            LangGraph + 4 UC Functions sobre Gold + RAG sobre noticias, servido en Model Serving.
          </p>
        </div>
        {messages.length > 0 && (
          <Button variant="outline" size="sm" onClick={() => setMessages([])} disabled={loading}>
            <Eraser className="h-4 w-4" />
            Nueva conversación
          </Button>
        )}
      </div>

      <div className="rounded-xl border bg-card flex flex-col h-[calc(100vh-13rem)] min-h-[480px] shadow-sm">
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
                <div className="text-destructive text-sm p-3 bg-destructive/10 rounded-lg">
                  No se pudo consultar al agente: {error}
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="border-t p-3 md:p-4 flex items-end gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribí tu pregunta… (Enter para enviar, Shift+Enter para salto de línea)"
            rows={1}
            className="min-h-11 max-h-40 resize-none"
            disabled={loading}
          />
          <Button type="submit" size="icon" className="h-11 w-11 shrink-0" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
            <span className="sr-only">Enviar</span>
          </Button>
        </form>
      </div>
    </div>
  );
}
