"use client";

import { Layers } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { REPO_URL } from "@/lib/site";

const LINKS = [
  { href: "/", label: "Inicio" },
  { href: "/agente", label: "Agente" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border px-4 md:px-6 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 md:gap-8">
        <Link href="/" className="flex items-center gap-3">
          <div
            className="h-9 w-9 rounded-lg flex items-center justify-center text-white shadow-sm"
            style={{ background: "linear-gradient(135deg, #9775fa, #ff6b6b)" }}
          >
            <Layers className="h-5 w-5" />
          </div>
          <div className="leading-tight hidden sm:block">
            <p className="text-base font-semibold">Crypto Lakehouse</p>
            <p className="text-xs text-muted-foreground">Databricks · Unity Catalog</p>
          </div>
        </Link>

        <nav className="flex items-center gap-1">
          {LINKS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                  active ? "bg-muted font-medium text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </div>

      <a
        href={REPO_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
      >
        GitHub
      </a>
    </header>
  );
}
