import type { Metadata } from "next";

import { PageHeader } from "@/components/common/page-header";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { FAQ, GLOSSARY, REGULATIONS } from "@/content/knowledge";
import { INDEX_MODEL } from "@/lib/domain";

export const metadata: Metadata = {
  title: "Metodología",
  description:
    "Cómo se calcula el índice de credibilidad y la confianza, qué limitaciones tiene y cómo reproducir el cálculo.",
};

const COMPONENTS = [
  {
    name: "Permanencia forestal",
    weight: INDEX_MODEL.weights.permanencia,
    how: "Qué parte del bosque que había al inicio sigue en pie desde la fecha de acreditación (T0). Se calcula como 100 × (1 − pérdida desde T0 ÷ bosque inicial), con datos de Hansen.",
  },
  {
    name: "Tendencia de vigor",
    weight: INDEX_MODEL.weights.tendencia,
    how: "Hacia dónde va el verdor después de T0. Se mide la pendiente del NDVI (método de Theil-Sen). Si es cero o sube, el puntaje es 100; baja de forma lineal hasta 0 cuando la caída llega a −0,05 por año. Si la tendencia no es estadísticamente significativa (Mann-Kendall, α = 0,05), la penalización se reduce a la mitad.",
  },
  {
    name: "Estabilidad",
    weight: INDEX_MODEL.weights.estabilidad,
    how: "Si hubo caídas bruscas del verdor después de T0. Se busca la mayor caída del promedio móvil de 3 meses, ya descontada la estacionalidad. Una caída de 0,05 o menos da 100; llega a 0 en 0,30.",
  },
] as const;

const INSUFFICIENT = [
  "No hay línea base de bosque o falta la fecha T0.",
  "Hay menos de 12 meses con datos posteriores a T0 para medir la tendencia y la estabilidad.",
  "La confianza es menor a 0,30.",
  "La fracción de píxeles válidos es menor a 0,15.",
];

const LIMITS = [
  "El NDVI de Landsat y el de Sentinel-2 no son equivalentes: no se mezclan; el cálculo usa un solo sensor.",
  "La pérdida de Hansen no distingue tala de incendio ni de manejo autorizado.",
  "Un bosque que no cambia puede estar mal declarado o simplemente no haber estado en riesgo: el índice no lo evalúa.",
  "No estima contrafactuales ni adicionalidad: no sabe qué habría pasado sin el proyecto.",
  "Las nubes pueden dejar pocas imágenes útiles, sobre todo en la Amazonía y en zonas andinas.",
];

export default function MethodologyPage() {
  return (
    <>
      <PageHeader eyebrow="Metodología" title="Cómo calculamos el índice">
        El índice mide la correspondencia entre lo que declara un proyecto y lo que se observa desde el satélite en
        su polígono. Es una señal para revisar, no un veredicto.
      </PageHeader>

      <div className="mx-auto max-w-4xl space-y-16 px-5">
        <section aria-labelledby="titulo-estado">
          <p className="rounded-2xl bg-secondary px-5 py-4 text-sm text-secondary-foreground">
            <strong>Índice {INDEX_MODEL.version} · en validación.</strong> Los pesos y umbrales son una propuesta
            que se está calibrando con proyectos reales. Cada cálculo guarda la versión del índice con la que se
            hizo.
          </p>
          <h2 id="titulo-estado" className="mt-10 text-2xl font-extrabold">
            Qué mide y qué no
          </h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="card-soft p-6">
              <h3 className="font-bold">Sí mide</h3>
              <p className="mt-2 text-muted-foreground">
                La permanencia del bosque, la tendencia del verdor y la estabilidad dentro del polígono público
                del proyecto, desde su fecha de acreditación.
              </p>
            </div>
            <div className="card-soft p-6">
              <h3 className="font-bold">No mide</h3>
              <p className="mt-2 text-muted-foreground">
                Qué habría pasado sin el proyecto (contrafactual), si las reducciones son adicionales, ni las
                intenciones de nadie.
              </p>
            </div>
          </div>
        </section>

        <section aria-labelledby="titulo-componentes">
          <h2 id="titulo-componentes" className="text-2xl font-extrabold">
            Tres componentes
          </h2>
          <p className="mt-2 text-muted-foreground">
            El puntaje es el promedio ponderado de los componentes que se pudieron calcular, de 0 a 100.
          </p>
          <ul className="mt-6 space-y-3">
            {COMPONENTS.map((component) => (
              <li key={component.name} className="card-soft flex gap-5 p-6">
                <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-forest text-lg font-extrabold text-lime">
                  {Math.round(component.weight * 100)}%
                </span>
                <div>
                  <h3 className="text-lg font-bold">{component.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{component.how}</p>
                </div>
              </li>
            ))}
          </ul>
          <h3 className="mt-8 text-lg font-bold">Categorías</h3>
          <dl className="mt-3 grid gap-3 sm:grid-cols-4">
            {[
              ["Alta", `${INDEX_MODEL.categoryHigh} o más`, "bg-cat-alta"],
              ["Media", `${INDEX_MODEL.categoryMedium} a ${INDEX_MODEL.categoryHigh - 1}`, "bg-cat-media"],
              ["Baja", `menos de ${INDEX_MODEL.categoryMedium}`, "bg-cat-baja"],
              ["Insuficiente", "sin puntaje", "bg-cat-insuficiente"],
            ].map(([name, range, color]) => (
              <div key={name} className="card-soft p-4">
                <dt className="flex items-center gap-2 font-bold">
                  <span className={`h-3 w-3 rounded-full ${color}`} aria-hidden /> {name}
                </dt>
                <dd className="mt-1 text-sm text-muted-foreground">{range}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section aria-labelledby="titulo-confianza">
          <h2 id="titulo-confianza" className="text-2xl font-extrabold">
            Confianza: qué tan seguros estamos
          </h2>
          <p className="mt-2 text-muted-foreground">
            La confianza va aparte del índice y no califica al proyecto: dice qué tan firme es el cálculo según las
            imágenes disponibles.
          </p>
          <p className="card-soft mt-4 p-5 font-mono text-sm">
            confianza = 0,4 × cobertura + 0,4 × píxeles válidos + 0,2 × mín(1, escenas por mes ÷ 3)
          </p>
          <p className="mt-3 text-sm text-muted-foreground">
            Alta desde {INDEX_MODEL.confidenceHigh.toString().replace(".", ",")}, media desde{" "}
            {INDEX_MODEL.confidenceMedium.toString().replace(".", ",")}, baja en otro caso. Si la fracción de píxeles
            válidos es menor a 0,15, la confianza se limita a 0,25.
          </p>
        </section>

        <section aria-labelledby="titulo-insuficiente">
          <h2 id="titulo-insuficiente" className="text-2xl font-extrabold">
            Cuando el resultado es «Insuficiente»
          </h2>
          <p className="mt-2 text-muted-foreground">
            Es un resultado legítimo, sobre todo en zonas muy nubosas. Se devuelve sin puntaje cuando:
          </p>
          <ul className="mt-3 list-disc space-y-1 pl-6 text-muted-foreground">
            {INSUFFICIENT.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="titulo-repro">
          <h2 id="titulo-repro" className="text-2xl font-extrabold">
            Reproducible y trazable
          </h2>
          <p className="mt-2 text-muted-foreground">
            Cada cálculo guarda sus parámetros completos, la versión del índice, la versión del código y las
            versiones de los conjuntos de datos. Además, el reporte incluye el rango del puntaje al mover cada peso
            ±10 puntos porcentuales, para ver qué tan sensible es el resultado.
          </p>
        </section>

        <section aria-labelledby="titulo-limites">
          <h2 id="titulo-limites" className="text-2xl font-extrabold">
            Limitaciones
          </h2>
          <ul className="mt-3 list-disc space-y-1 pl-6 text-muted-foreground">
            {LIMITS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="titulo-glosario">
          <h2 id="titulo-glosario" className="text-2xl font-extrabold">
            Glosario
          </h2>
          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            {GLOSSARY.map((entry) => (
              <div key={entry.term} className="card-soft p-5">
                <dt className="font-bold">{entry.term}</dt>
                <dd className="mt-1 text-sm text-muted-foreground">{entry.definition}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section aria-labelledby="titulo-faq">
          <h2 id="titulo-faq" className="text-2xl font-extrabold">
            Preguntas frecuentes
          </h2>
          <Accordion type="single" collapsible className="mt-4">
            {FAQ.map((item) => (
              <AccordionItem key={item.question} value={item.question}>
                <AccordionTrigger>{item.question}</AccordionTrigger>
                <AccordionContent>{item.answer}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </section>

        <section aria-labelledby="titulo-normas">
          <h2 id="titulo-normas" className="text-2xl font-extrabold">
            Marco normativo colombiano
          </h2>
          <ul className="mt-4 space-y-3">
            {REGULATIONS.map((rule) => (
              <li key={rule.name} className="card-soft p-5">
                <p className="font-bold">{rule.name}</p>
                <p className="mt-1 text-sm text-muted-foreground">{rule.summary}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
