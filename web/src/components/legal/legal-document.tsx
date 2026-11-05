import Link from "next/link";
import type { ReactNode } from "react";

import { PageHeader } from "@/components/common/page-header";

export type LegalSection = { id: string; title: string; body: ReactNode };

export const LEGAL_UPDATED = "5 de noviembre de 2026";

export const LEGAL_PAGES = [
  { href: "/terminos", label: "Términos y condiciones" },
  { href: "/privacidad", label: "Política de privacidad" },
  { href: "/uso-de-datos", label: "Uso de datos y fuentes" },
] as const;

export const CONTACT_EMAIL = process.env.PRIVACY_CONTACT_EMAIL ?? "";

export function ContactLine() {
  return CONTACT_EMAIL ? (
    <a href={`mailto:${CONTACT_EMAIL}`} className="font-semibold text-foreground underline underline-offset-4">
      {CONTACT_EMAIL}
    </a>
  ) : (
    <span>el canal de contacto que el equipo publique en esta página</span>
  );
}

export function LegalDocument({
  eyebrow,
  title,
  version,
  current,
  intro,
  sections,
}: {
  eyebrow: string;
  title: string;
  version: string;
  current: (typeof LEGAL_PAGES)[number]["href"];
  intro: ReactNode;
  sections: LegalSection[];
}) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title}>
        {intro}
        <p className="mt-3 text-sm">
          Versión <span className="font-mono">{version}</span> · Última actualización: {LEGAL_UPDATED}
        </p>
      </PageHeader>
      <div className="mx-auto grid max-w-7xl gap-8 px-5 lg:grid-cols-[15rem_1fr]">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <nav aria-label="Documentos legales" className="card-soft p-5 text-sm">
            <p className="eyebrow">Documentos</p>
            <ul className="mt-3 space-y-2">
              {LEGAL_PAGES.map((page) => (
                <li key={page.href}>
                  <Link
                    href={page.href}
                    aria-current={page.href === current ? "page" : undefined}
                    className={
                      page.href === current
                        ? "font-semibold text-foreground"
                        : "text-muted-foreground hover:text-foreground hover:underline"
                    }
                  >
                    {page.label}
                  </Link>
                </li>
              ))}
            </ul>
            <p className="eyebrow mt-6">En esta página</p>
            <ol className="mt-3 space-y-1.5">
              {sections.map((section, index) => (
                <li key={section.id}>
                  <a href={`#${section.id}`} className="text-muted-foreground hover:text-foreground hover:underline">
                    {index + 1}. {section.title}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
        </aside>
        <div className="max-w-3xl space-y-4">
          {sections.map((section, index) => (
            <section
              key={section.id}
              id={section.id}
              aria-labelledby={`titulo-${section.id}`}
              className="card-soft scroll-mt-24 p-6"
            >
              <h2 id={`titulo-${section.id}`} className="text-xl font-bold">
                {index + 1}. {section.title}
              </h2>
              <div className="mt-3 space-y-3 text-muted-foreground [&_li]:mt-1.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:text-foreground [&_ul]:list-disc [&_ul]:pl-5">
                {section.body}
              </div>
            </section>
          ))}
        </div>
      </div>
    </>
  );
}
