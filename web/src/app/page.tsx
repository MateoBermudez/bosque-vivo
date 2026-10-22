import {
  ArrowRight,
  Check,
  Clock,
  Code2,
  FileCheck2,
  GraduationCap,
  Layers,
  MessageCircle,
  Satellite,
  Scale,
  ShieldOff,
  Users,
  Wallet,
  X,
} from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { PhoneChat } from "@/components/home/phone-chat";

export const metadata: Metadata = {
  title: { absolute: "Bosque Vivo · Lo declarado frente a lo observado" },
  description:
    "Sistema que contrasta lo que declaran los proyectos de carbono forestal con lo que se observa desde el satélite, explicado en lenguaje sencillo.",
};

const STATS = [
  { value: "6 %", text: "de los créditos de 18 proyectos REDD+ correspondía a reducciones reales y adicionales", source: "West et al., 2023, Science" },
  { value: "< 16 %", text: "de los créditos de 2.346 proyectos son reducciones reales", source: "Probst et al., 2024, Nature Communications" },
  { value: "44 %", text: "de mortalidad de árboles plantados a los cinco años", source: "Banin et al., 2022" },
  { value: "1/3", text: "de los ingresos de un proyecto puede consumirlo la auditoría", source: "Foster et al., 2017" },
  { value: "113.608 ha", text: "deforestadas en Colombia en 2024, 43 % más que en 2023", source: "IDEAM y MinAmbiente, 2025" },
  { value: "41,4 %", text: "de hogares rurales con internet, frente a 70,5 % en cabeceras", source: "DANE, 2024" },
] as const;

const GAPS = [
  { icon: Clock, title: "Detección tardía", text: "Los cambios de cobertura se detectan meses o años después." },
  { icon: Wallet, title: "MRV inaccesible", text: "Medir, reportar y verificar es costoso para proyectos pequeños." },
  { icon: ShieldOff, title: "Sin auditoría independiente", text: "Hay pocas revisiones abiertas por fuera de los certificadores." },
] as const;

const STEPS = [
  { icon: Layers, title: "Importamos los polígonos", text: "Tomamos los límites públicos de cada proyecto desde los registros." },
  { icon: Satellite, title: "Calculamos el NDVI", text: "Obtenemos series satelitales y medimos el verdor de la vegetación." },
  { icon: Scale, title: "Comparamos", text: "Ponemos lado a lado lo declarado y lo observado." },
  { icon: FileCheck2, title: "Índice y reporte", text: "Generamos un índice de credibilidad y un reporte reproducible." },
] as const;

const SOURCES = [
  "Registros públicos (Karnik et al., 2025)",
  "Sentinel-2",
  "Landsat",
  "Hansen Global Forest Change",
  "Google Earth Engine",
] as const;

export default function HomePage() {
  return (
    <>
      <section className="px-3 pt-3 md:px-5" aria-labelledby="titulo-hero">
        <div className="relative mx-auto max-w-7xl overflow-hidden rounded-[2rem]">
          <Image
            src="/images/hero-forest.jpg"
            alt="Vista aérea de un bosque andino atravesado por un río"
            fill
            priority
            sizes="(min-width: 1280px) 1280px, 100vw"
            className="object-cover"
          />
          <div className="bg-fade absolute inset-0" />
          <div className="relative flex min-h-[78vh] flex-col justify-end p-6 text-forest-foreground md:p-14">
            <span className="glass mb-5 w-fit rounded-full px-3 py-1 text-xs font-medium">
              ODS 15 · Vida de ecosistemas terrestres
            </span>
            <h1 id="titulo-hero" className="max-w-3xl text-4xl leading-[1.05] font-extrabold md:text-7xl">
              Lo que se declara, frente a lo que el satélite observa.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-forest-foreground/85">
              Revisamos proyectos de carbono forestal con imágenes satelitales y te lo explicamos en palabras
              sencillas.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/proyectos" className="btn-lime">
                Explorar proyectos <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
              <Link href="/whatsapp" className="btn-cream">
                Hablar con el asistente
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pt-24" aria-labelledby="titulo-problema">
        <p className="eyebrow">El problema</p>
        <h2 id="titulo-problema" className="mt-2 max-w-2xl text-3xl font-extrabold md:text-5xl">
          Las cifras muestran una brecha entre lo prometido y lo medido.
        </h2>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {STATS.map((stat) => (
            <article key={stat.value} className="card-soft flex flex-col p-6">
              <p className="text-4xl font-extrabold text-primary">{stat.value}</p>
              <p className="mt-3 flex-1 text-foreground/80">{stat.text}</p>
              <p className="mt-5 text-xs font-semibold text-muted-foreground">Fuente: {stat.source}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto mt-24 max-w-7xl px-5" aria-labelledby="titulo-vacios">
        <div className="rounded-[2rem] bg-forest p-8 text-forest-foreground md:p-14">
          <h2 id="titulo-vacios" className="text-sm font-semibold text-lime">
            Tres vacíos
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {GAPS.map((gap) => (
              <div key={gap.title} className="glass rounded-3xl p-6">
                <gap.icon className="h-6 w-6 text-lime" aria-hidden />
                <h3 className="mt-4 text-xl font-bold">{gap.title}</h3>
                <p className="mt-2 text-forest-muted">{gap.text}</p>
              </div>
            ))}
          </div>
          <blockquote className="mt-10 max-w-3xl border-l-2 border-lime pl-5 text-xl font-semibold md:text-2xl">
            ¿Qué nivel de correspondencia existe entre la reducción de deforestación declarada por proyectos de
            créditos de carbono forestal certificados y la permanencia forestal real de la cobertura arbórea,
            verificable mediante evidencia satelital histórica en sus polígonos públicamente registrados?
          </blockquote>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pt-24" aria-labelledby="titulo-como">
        <p className="eyebrow">Cómo funciona</p>
        <h2 id="titulo-como" className="mt-2 text-3xl font-extrabold md:text-5xl">
          Cuatro pasos, todo a la vista.
        </h2>
        <ol className="mt-10 grid gap-4 md:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title} className="card-soft p-6">
              <div className="flex items-center justify-between">
                <span className="grid h-11 w-11 place-items-center rounded-full bg-lime text-lime-foreground">
                  <step.icon className="h-5 w-5" aria-hidden />
                </span>
                <span className="text-sm font-bold text-muted-foreground">0{index + 1}</span>
              </div>
              <h3 className="mt-5 text-lg font-bold">{step.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{step.text}</p>
            </li>
          ))}
        </ol>
        <div className="mt-4 flex gap-1.5" aria-hidden>
          {STEPS.map((step) => (
            <span key={step.title} className="h-1.5 flex-1 rounded-full bg-lime" />
          ))}
        </div>
      </section>

      <section className="mx-auto mt-24 max-w-7xl px-5" aria-labelledby="titulo-asistente">
        <div className="grid items-center gap-10 rounded-[2rem] bg-secondary p-8 md:grid-cols-2 md:p-14">
          <div>
            <p className="eyebrow">Asistente de IA</p>
            <h2 id="titulo-asistente" className="mt-2 text-3xl font-extrabold md:text-5xl">
              Pregunta por WhatsApp, en español sencillo.
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Escribe, comparte tu ubicación, envía una foto o una nota de voz. El asistente te responde con las
              cifras del sistema.
            </p>
            <Link href="/whatsapp" className="btn-dark mt-8">
              <MessageCircle className="h-4 w-4" aria-hidden /> Conocer el asistente
            </Link>
          </div>
          <PhoneChat />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pt-24" aria-labelledby="titulo-publico">
        <p className="eyebrow">Para quién es</p>
        <h2 id="titulo-publico" className="sr-only">
          Para quién es Bosque Vivo
        </h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <article className="card-soft p-8">
            <Users className="h-7 w-7 text-primary" aria-hidden />
            <h3 className="mt-4 text-2xl font-bold">Comunidad rural y pequeños productores</h3>
            <p className="mt-2 text-muted-foreground">
              Mensajes cortos desde el celular para saber qué pasa con el bosque de tu territorio.
            </p>
          </article>
          <article className="rounded-[calc(var(--radius)+4px)] bg-forest p-8 text-forest-foreground">
            <GraduationCap className="h-7 w-7 text-lime" aria-hidden />
            <h3 className="mt-4 text-2xl font-bold">Auditores, docentes e investigadores</h3>
            <p className="mt-2 text-forest-muted">
              Detalle por componente, trazas del agente, versiones de datos y cálculo reproducible.
            </p>
          </article>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pt-24" aria-labelledby="titulo-mide">
        <p className="eyebrow">Qué mide y qué no</p>
        <h2 id="titulo-mide" className="sr-only">
          Qué mide y qué no mide el índice
        </h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="card-soft p-8">
            <h3 className="flex items-center gap-2 text-xl font-bold">
              <Check className="h-5 w-5 text-cat-alta" aria-hidden /> Sí mide
            </h3>
            <p className="mt-3 text-muted-foreground">
              La correspondencia observada entre lo que declara un proyecto y lo que muestran las imágenes
              satelitales: permanencia del bosque, tendencia de vigor y estabilidad.
            </p>
          </div>
          <div className="card-soft p-8">
            <h3 className="flex items-center gap-2 text-xl font-bold">
              <X className="h-5 w-5 text-cat-baja" aria-hidden /> No mide
            </h3>
            <p className="mt-3 text-muted-foreground">
              No estima qué habría pasado sin el proyecto (contrafactual) ni si las reducciones son adicionales.
              Es una señal, no un veredicto.
            </p>
          </div>
        </div>
        <p className="mt-4 text-sm">
          <Link href="/metodologia" className="font-semibold underline underline-offset-4">
            Conoce la metodología completa
          </Link>
        </p>
      </section>

      <section className="mx-auto max-w-7xl px-5 pt-24" aria-labelledby="titulo-fuentes">
        <p className="eyebrow">Fuentes de datos y transparencia</p>
        <h2 id="titulo-fuentes" className="mt-2 text-3xl font-extrabold md:text-4xl">
          Datos abiertos, código abierto.
        </h2>
        <ul className="mt-8 flex flex-wrap gap-3">
          {SOURCES.map((source) => (
            <li key={source} className="rounded-full border border-border bg-card px-4 py-2 text-sm font-medium">
              {source}
            </li>
          ))}
          <li className="flex items-center gap-2 rounded-full bg-lime px-4 py-2 text-sm font-semibold text-lime-foreground">
            <Code2 className="h-4 w-4" aria-hidden /> Cálculo reproducible
          </li>
        </ul>
      </section>
    </>
  );
}
