"use client";

import { ChevronDown, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

import { Logo } from "./logo";

const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/proyectos", label: "Proyectos" },
  { href: "/whatsapp", label: "Asistente WhatsApp" },
  { href: "/metodologia", label: "Metodología" },
  { href: "/privacidad", label: "Privacidad" },
  { href: "/acerca", label: "Acerca de" },
] as const;

const AUDITOR_NAV = [
  { href: "/chat", label: "Chat del auditor" },
  { href: "/trazas", label: "Trazas del agente" },
] as const;

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteHeader() {
  const pathname = usePathname();
  // Cada menú recuerda en qué página se abrió: al navegar queda cerrado sin necesitar un efecto.
  const [mobileOpenAt, setMobileOpenAt] = useState<string | null>(null);
  const [auditorOpenAt, setAuditorOpenAt] = useState<string | null>(null);
  const mobileOpen = mobileOpenAt === pathname;
  const auditorOpen = auditorOpenAt === pathname;
  const auditorRef = useRef<HTMLDivElement>(null);

  // Cierra el menú de auditor con clic fuera o con Escape.
  useEffect(() => {
    if (!auditorOpen) return;
    const onPointer = (event: PointerEvent) => {
      if (!auditorRef.current?.contains(event.target as Node)) setAuditorOpenAt(null);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setAuditorOpenAt(null);
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [auditorOpen]);

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
        <Link href="/" aria-label="Bosque Vivo, inicio">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Principal">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className={cn(
                "rounded-full px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground",
                isActive(pathname, item.href) && "bg-secondary text-foreground",
              )}
            >
              {item.label}
            </Link>
          ))}
          <div className="relative" ref={auditorRef}>
            <button
              type="button"
              onClick={() => setAuditorOpenAt(auditorOpen ? null : pathname)}
              aria-expanded={auditorOpen}
              aria-haspopup="true"
              className="flex items-center gap-1 rounded-full bg-forest px-3 py-2 text-sm font-semibold text-forest-foreground"
            >
              Auditor <ChevronDown className="h-3.5 w-3.5" aria-hidden />
            </button>
            {auditorOpen && (
              <div className="card-soft absolute right-0 mt-2 w-56 p-2">
                {AUDITOR_NAV.map((item) => (
                  <Link key={item.href} href={item.href} className="block rounded-xl px-3 py-2 text-sm hover:bg-muted">
                    {item.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </nav>

        <button
          type="button"
          className="grid h-11 w-11 place-items-center rounded-full bg-secondary lg:hidden"
          onClick={() => setMobileOpenAt(mobileOpen ? null : pathname)}
          aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={mobileOpen}
          aria-controls="menu-movil"
        >
          {mobileOpen ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
        </button>
      </div>

      {mobileOpen && (
        <nav id="menu-movil" className="border-t border-border px-5 pb-5 lg:hidden" aria-label="Móvil">
          {[...NAV, ...AUDITOR_NAV].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className="block border-b border-border/60 py-3 font-medium"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
