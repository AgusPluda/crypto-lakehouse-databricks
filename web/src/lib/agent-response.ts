interface AgentMessage {
  type?: string;
  role?: string;
  name?: string | null;
  content?: unknown;
}

interface AgentResponse {
  messages?: AgentMessage[];
  choices?: { message?: { content?: string } }[];
}

function contentToText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) => (typeof part === "string" ? part : ((part as { text?: string })?.text ?? "")))
      .join("");
  }
  return "";
}

// La respuesta final es el último mensaje 'ai' con texto: los 'ai' que solo llaman tools vienen con content vacío.
export function extractAnswer(data: unknown): string | null {
  const resp = data as AgentResponse;
  const final = [...(resp?.messages ?? [])]
    .reverse()
    .find((m) => (m.type === "ai" || m.role === "assistant") && contentToText(m.content).trim());
  if (final) return contentToText(final.content);
  return resp?.choices?.[0]?.message?.content ?? null;
}

// Tools invocadas en el turno actual: los mensajes 'tool' posteriores al último mensaje del usuario.
export function extractTools(data: unknown): string[] {
  const msgs = (data as AgentResponse)?.messages ?? [];
  let lastUser = -1;
  msgs.forEach((m, i) => {
    if (m.type === "human" || m.role === "user") lastUser = i;
  });
  const names = msgs
    .slice(lastUser + 1)
    .filter((m) => m.type === "tool" && m.name)
    .map((m) => (m.name as string).split("__").pop() as string);
  return [...new Set(names)];
}
