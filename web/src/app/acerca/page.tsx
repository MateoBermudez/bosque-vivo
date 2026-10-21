import { ClipboardList, Code2, FlaskConical, PencilRuler } from "lucide-react";
import type { Metadata } from "next";

import { PageHeader } from "@/components/common/page-header";
import { REFERENCES } from "@/content/knowledge";
import { TEAM } from "@/content/team";

export const metadata: Metadata = {
  title: "Acerca del proyecto",
  description:
    "Objetivo, objetivos específicos, alcance, institución, equipo y referencias de Bosque Vivo, un proyecto integrador de Ingeniería Informática.",
};

const OBJECTIVES = [
  { icon: ClipboardList, title: "Documentar", text: "Los requisitos funcionales y no funcionales del sistema de información." },
  { icon: PencilRuler, title: "Diseñar", text: "La arquitectura del sistema con herramientas de código abierto." },
  { icon: Code2, title: "Desarrollar", text: "Los módulos del sistema conforme al diseño establecido." },
  { icon: FlaskConical, title: "Validar", text: "El sistema con un plan de pruebas que verifique los requisitos." },
] as const;

export default function AboutPage() {
  return (
    <>
      <PageHeader eyebrow="Acerca del proyecto" title="Bosque Vivo">
        Proyecto integrador de Ingeniería Informática del Politécnico Colombiano Jaime Isaza Cadavid, alineado con
        el ODS 15 · Vida de ecosistemas terrestres.
      </PageHeader>

      <div className="mx-auto max-w-5xl space-y-16 px-5">
        <section aria-labelledby="titulo-objetivo">
          <h2 id="titulo-objetivo" className="text-2xl font-extrabold">
            Objetivo general
          </h2>
          <p className="mt-3 text-lg text-muted-foreground">
            Implementar un sistema de información, utilizando herramientas de código abierto, para la auditoría de
            la supervivencia forestal posterior a la certificación oficial de proyectos de carbono.
          </p>
          <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {OBJECTIVES.map((objective, index) => (
              <li key={objective.title} className="card-soft p-6">
                <div className="flex items-center justify-between">
                  <span className="grid h-11 w-11 place-items-center rounded-full bg-lime text-lime-foreground">
                    <objective.icon className="h-5 w-5" aria-hidden />
                  </span>
                  <span className="text-sm font-bold text-muted-foreground">OE {index + 1}</span>
                </div>
                <h3 className="mt-5 text-lg font-bold">{objective.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{objective.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section aria-labelledby="titulo-alcance">
          <h2 id="titulo-alcance" className="text-2xl font-extrabold">
            Alcance
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="card-soft p-6">
              <h3 className="font-bold">Dentro de la entrega</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                <li>
                  <strong>Verificación y auditoría:</strong> cruza los polígonos públicos de proyectos certificados
                  con series históricas de cobertura vegetal y estima un índice de credibilidad.
                </li>
                <li>
                  <strong>Asistente conversacional:</strong> prototipo por WhatsApp, en español sencillo, para
                  consultar el estado del bosque.
                </li>
              </ul>
            </div>
            <div className="card-soft p-6">
              <h3 className="font-bold">Fuera del alcance</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                <li>
                  <strong>Detección temprana:</strong> alertas de cambios de cobertura e incendios casi en tiempo
                  real. Queda documentada como evolución prevista.
                </li>
                <li>
                  <strong>Contrafactuales y adicionalidad:</strong> el índice mide correspondencia entre lo
                  declarado y lo observado, no estima qué habría pasado sin el proyecto.
                </li>
              </ul>
            </div>
          </div>
        </section>

        {TEAM.length > 0 && (
          <section aria-labelledby="titulo-equipo">
            <h2 id="titulo-equipo" className="text-2xl font-extrabold">
              Equipo
            </h2>
            <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {TEAM.map((member) => (
                <li key={member.name} className="card-soft p-5">
                  <p className="font-bold">{member.name}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{member.role}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section aria-labelledby="titulo-referencias">
          <h2 id="titulo-referencias" className="text-2xl font-extrabold">
            Referencias
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Lista abreviada; las referencias completas con DOI están en el anexo del ERS.
          </p>
          <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
            {REFERENCES.map((reference) => (
              <li key={reference} className="card-soft p-4">
                {reference}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
