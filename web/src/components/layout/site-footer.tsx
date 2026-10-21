import Link from "next/link";

import { Logo } from "./logo";

export function SiteFooter() {
  return (
    <footer className="mt-24 bg-forest text-forest-foreground">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 md:grid-cols-3">
        <div>
          <Logo light />
          <p className="mt-4 max-w-xs text-sm text-forest-muted">
            Contrastamos lo que declaran los proyectos de carbono forestal con lo que se observa desde el
            satélite.
          </p>
        </div>
        <nav className="flex flex-col gap-2 text-sm" aria-label="Pie de página">
          <Link href="/metodologia" className="hover:underline">
            Metodología
          </Link>
          <Link href="/privacidad" className="hover:underline">
            Privacidad
          </Link>
          <Link href="/acerca" className="hover:underline">
            Acerca del proyecto
          </Link>
          <Link href="/trazas" className="hover:underline">
            Trazas del agente
          </Link>
        </nav>
        <div className="text-sm text-forest-muted">
          <p className="font-semibold text-forest-foreground">Politécnico Colombiano Jaime Isaza Cadavid</p>
          <p>Ingeniería Informática · Proyecto integrador</p>
          <p className="mt-2 inline-block rounded-full bg-lime px-3 py-1 text-xs font-semibold text-lime-foreground">
            ODS 15 · Vida de ecosistemas terrestres
          </p>
        </div>
      </div>
    </footer>
  );
}
