import type { Metadata } from "next";
import { Chat } from "@/components/Chat";

export const metadata: Metadata = { title: "Agente — Crypto Lakehouse" };

export default function AgentPage() {
  return (
    <main className="flex-1 px-4 md:px-6 py-6 md:py-8">
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="space-y-1">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Agente IA</h1>
          <p className="text-sm text-muted-foreground">
            Consulta precios con UC Functions sobre Gold y noticias con RAG, y cita sus fuentes. Es una demo sobre
            Databricks Free Edition: el agente se duerme si no se usa, así que la primera consulta puede tardar un par de
            minutos. Las variaciones de precio corresponden al último día cerrado.
          </p>
        </div>
        <Chat />
      </div>
    </main>
  );
}
