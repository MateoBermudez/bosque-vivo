import Link from "next/link";

import { Logo } from "./logo";

/** Se muestra mientras el encabezado interactivo conoce la ruta actual (misma altura, sin saltos). */
export function SiteHeaderFallback() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/85 backdrop-blur-xl">
      <div className="mx-auto flex h-[3.75rem] max-w-7xl items-center justify-between gap-4 px-5">
        <Link href="/" aria-label="Bosque Vivo, inicio">
          <Logo />
        </Link>
      </div>
    </header>
  );
}
