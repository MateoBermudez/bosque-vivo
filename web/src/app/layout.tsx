import type { Metadata, Viewport } from "next";
import { Manrope } from "next/font/google";
import { Suspense } from "react";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteHeaderFallback } from "@/components/layout/site-header-fallback";

import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? "http://localhost:3000"),
  title: {
    default: "Bosque Vivo · Lo declarado frente a lo observado",
    template: "%s · Bosque Vivo",
  },
  description:
    "Contrastamos lo que declaran los proyectos de carbono forestal con lo que se observa desde el satélite, explicado en lenguaje sencillo.",
  openGraph: { type: "website", locale: "es_CO", siteName: "Bosque Vivo" },
};

export const viewport: Viewport = {
  themeColor: "#1f3a28",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es-CO" className={manrope.variable}>
      <body>
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-lime focus:px-4 focus:py-2 focus:font-semibold focus:text-lime-foreground"
        >
          Saltar al contenido
        </a>
        <Suspense fallback={<SiteHeaderFallback />}>
          <SiteHeader />
        </Suspense>
        <main id="contenido">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
