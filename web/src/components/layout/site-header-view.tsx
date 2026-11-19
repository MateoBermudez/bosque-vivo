"use client";

import { LogOut, Menu, ShieldCheck, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { logout } from "@/app/acceso/actions";
import { cn } from "@/lib/utils";

import { Logo } from "./logo";

/** Menú del sitio público: lo que ve cualquier persona. */
const PUBLIC_NAV = [
  { href: "/", label: "Inicio" },
  { href: "/proyectos", label: "Proyectos" },
  { href: "/asistente", label: "Asistente" },
  { href: "/metodologia", label: "Metodología" },
  { href: "/privacidad", label: "Privacidad" },
  { href: "/acerca", label: "Acerca de" },
] as const;

/** Menú del modo auditor: sin el asistente comunitario, que es para el público. */
const AUDITOR_NAV = [
  { href: "/chat", label: "Chat del auditor" },
  { href: "/trazas", label: "Trazas del agente" },
  { href: "/proyectos", label: "Proyectos" },
  { href: "/metodologia", label: "Metodología" },
] as const;

/** Páginas que solo existen para auditores. */
const AUDITOR_PATHS = ["/chat", "/trazas"] as const;

export interface AuditorInfo {
  /** Correo con el que inició sesión, o «auditor» si entró con código. */
  who: string;
}

interface Props {
  /** Sesión de auditor activa (null si es una visita pública). */
  auditor: AuditorInfo | null;
  /** Desarrollo sin SESSION_SECRET: el área de auditores está abierta y no hay sesión. */
  openMode: boolean;
}

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function LogoutButton({ className }: { className?: string }) {
  return (
    <form action={logout}>
      <button type="submit" className={className}>
        <LogOut className="h-4 w-4" aria-hidden /> Cerrar sesión
      </button>
    </form>
  );
}

export function SiteHeaderView({ auditor, openMode }: Props) {
  const pathname = usePathname();
  // El menú recuerda en qué página se abrió: al navegar queda cerrado sin necesitar un efecto.
  const [mobileOpenAt, setMobileOpenAt] = useState<string | null>(null);
  const mobileOpen = mobileOpenAt === pathname;

  // Sin sesión real (desarrollo abierto) se considera «modo auditor» mientras se esté en sus páginas,
  // para poder ver esta interfaz y salir de ella.
  const inAuditorMode =
    auditor !== null || (openMode && AUDITOR_PATHS.some((path) => isActive(pathname, path)));

  if (inAuditorMode) {
    return (
      <header className="sticky top-0 z-40 border-b border-forest-2 bg-forest text-forest-foreground">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
          <Link href="/chat" aria-label="Bosque Vivo, modo auditor">
            <Logo light />
          </Link>

          <nav className="hidden items-center gap-1 lg:flex" aria-label="Auditor">
            {AUDITOR_NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive(pathname, item.href) ? "page" : undefined}
                className={cn(
                  "rounded-full px-3 py-2 text-sm font-medium text-forest-muted hover:text-forest-foreground",
                  isActive(pathname, item.href) && "bg-forest-2 text-forest-foreground",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="hidden items-center gap-3 lg:flex">
            <span className="flex items-center gap-1.5 rounded-full bg-lime px-3 py-1 text-xs font-semibold text-lime-foreground">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden /> Modo auditor
            </span>
            {auditor && auditor.who !== "auditor" && (
              <span className="max-w-[14rem] truncate text-sm text-forest-muted" title={auditor.who}>
                {auditor.who}
              </span>
            )}
            <LogoutButton className="flex items-center gap-1.5 rounded-full border border-forest-muted/50 px-3 py-2 text-sm font-semibold hover:bg-forest-2" />
          </div>

          <button
            type="button"
            className="grid h-11 w-11 place-items-center rounded-full bg-forest-2 lg:hidden"
            onClick={() => setMobileOpenAt(mobileOpen ? null : pathname)}
            aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={mobileOpen}
            aria-controls="menu-movil"
          >
            {mobileOpen ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
          </button>
        </div>

        {mobileOpen && (
          <nav id="menu-movil" className="border-t border-forest-2 px-5 pb-5 lg:hidden" aria-label="Móvil">
            <p className="flex items-center gap-1.5 py-3 text-xs font-semibold text-lime">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden /> Modo auditor
              {auditor && auditor.who !== "auditor" ? ` · ${auditor.who}` : ""}
            </p>
            {AUDITOR_NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive(pathname, item.href) ? "page" : undefined}
                className="block border-b border-forest-2 py-3 font-medium"
              >
                {item.label}
              </Link>
            ))}
            <LogoutButton className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-full border border-forest-muted/50 px-3 py-3 font-semibold" />
          </nav>
        )}
      </header>
    );
  }

  // En desarrollo abierto no hay pantalla de acceso: se entra directo al chat del auditor.
  const auditorEntry = openMode ? "/chat" : "/acceso";

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
        <Link href="/" aria-label="Bosque Vivo, inicio">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Principal">
          {PUBLIC_NAV.map((item) => (
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
          <Link
            href={auditorEntry}
            className="flex items-center gap-1.5 rounded-full bg-forest px-3 py-2 text-sm font-semibold text-forest-foreground"
          >
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden /> Acceso de auditores
          </Link>
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
          {PUBLIC_NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className="block border-b border-border/60 py-3 font-medium"
            >
              {item.label}
            </Link>
          ))}
          <Link href={auditorEntry} className="block py-3 font-semibold">
            Acceso de auditores
          </Link>
        </nav>
      )}
    </header>
  );
}
