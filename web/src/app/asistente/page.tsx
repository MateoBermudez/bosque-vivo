import { Image as ImageIcon, MapPin, Mic, ShieldCheck, Smartphone, Type } from "lucide-react";
import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { connection } from "next/server";
import QRCode from "qrcode";
import { Suspense } from "react";

import { PageHeader } from "@/components/common/page-header";
import { CommunityChat } from "@/components/community/community-chat";

export const metadata: Metadata = {
  title: "Asistente",
  description:
    "Pregunta por el estado del bosque de tu proyecto en español sencillo: escribe, comparte tu ubicación, una foto o una nota de voz.",
};

const STEPS = [
  {
    title: "Escribe «Hola»",
    text: "El asistente se presenta y te recuerda que es una inteligencia artificial y que puede equivocarse.",
  },
  {
    title: "Lee el aviso y escribe ACEPTO",
    text: "Sin tu autorización no puede ayudarte. El aviso explica qué datos se usan y quién los procesa.",
  },
  {
    title: "Elige tu proyecto",
    text: "Escribe PROYECTO y el número (por ejemplo, PROYECTO 7) o comparte tu ubicación para que encuentre el proyecto.",
  },
  {
    title: "Pregunta con tus palabras",
    text: "Por ejemplo: «¿cómo está el bosque de mi finca?», o escribe ESTADO o ALERTAS.",
  },
  {
    title: "Para enviar fotos o audios, escribe ACEPTO FOTOS",
    text: "Es un permiso aparte, porque se procesan con un servicio externo y son información sin verificar.",
  },
  {
    title: "Cuando quieras, escribe BORRAR MIS DATOS",
    text: "Se eliminan tu conversación, tus permisos y tus consultas.",
  },
] as const;

const CAPABILITIES = [
  { icon: Type, title: "Texto", text: "Preguntas cortas, en lenguaje cotidiano." },
  { icon: MapPin, title: "Ubicación", text: "Comparte tu punto y te decimos si cae dentro de un proyecto." },
  {
    icon: ImageIcon,
    title: "Fotos",
    text: "Describe lo que se ve y lo compara con el satélite. Es evidencia comunitaria, no verificada.",
  },
  {
    icon: Mic,
    title: "Notas de voz",
    text: "Si no quieres escribir, cuéntale tu pregunta hablando (hasta un minuto).",
  },
] as const;

export default function CommunityChatPage() {
  return (
    <>
      <PageHeader eyebrow="Asistente de IA" title="Pregunta por el bosque, en español sencillo">
        Desde el navegador del celular o del computador, sin instalar nada. Antes de responder te pedirá autorización
        según la{" "}
        <Link href="/privacidad" className="underline underline-offset-4">
          política de privacidad
        </Link>{" "}
        y aplican los{" "}
        <Link href="/terminos" className="underline underline-offset-4">
          términos y condiciones
        </Link>
        .
      </PageHeader>

      <div className="mx-auto grid max-w-7xl gap-10 px-5 pb-16 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <CommunityChat />
          <p className="mt-4 text-xs text-muted-foreground">
            Las respuestas describen lo que se ve desde el satélite y pueden contener errores. Escribe BORRAR MIS DATOS
            para eliminar tu conversación.
          </p>
        </div>

        <div className="space-y-10">
          <Suspense fallback={<div className="card-soft h-32 animate-pulse" />}>
            <PhoneCard />
          </Suspense>

          <section aria-labelledby="titulo-empezar">
            <h2 id="titulo-empezar" className="text-2xl font-extrabold">
              Cómo funciona
            </h2>
            <ol className="mt-4 space-y-3">
              {STEPS.map((step, index) => (
                <li key={step.title} className="card-soft flex gap-4 p-5">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-lime text-sm font-bold text-lime-foreground">
                    {index + 1}
                  </span>
                  <div>
                    <h3 className="font-bold">{step.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{step.text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section aria-labelledby="titulo-puede">
            <h2 id="titulo-puede" className="text-2xl font-extrabold">
              Qué puede hacer
            </h2>
            <ul className="mt-4 grid gap-4 sm:grid-cols-2">
              {CAPABILITIES.map((item) => (
                <li key={item.title} className="card-soft p-5">
                  <item.icon className="h-6 w-6 text-primary" aria-hidden />
                  <h3 className="mt-3 font-bold">{item.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{item.text}</p>
                </li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="titulo-datos" className="rounded-[2rem] bg-forest p-8 text-forest-foreground">
            <ShieldCheck className="h-7 w-7 text-lime" aria-hidden />
            <h2 id="titulo-datos" className="mt-3 text-2xl font-extrabold">
              Tus datos
            </h2>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-forest-muted">
              <li>
                No pedimos tu nombre, tu teléfono ni tu correo: la conversación se identifica con un código anónimo.
              </li>
              <li>
                Un servicio de un tercero (Google Gemini) procesa los mensajes, posiblemente fuera de Colombia. No
                envíes cédula, dirección ni datos privados.
              </li>
              <li>Las fotos y los audios se procesan y se descartan; no se guardan los archivos.</li>
              <li>Puedes borrar tus datos cuando quieras escribiendo BORRAR MIS DATOS.</li>
            </ul>
            <Link href="/privacidad" className="btn-lime mt-6">
              Leer la política de privacidad
            </Link>
          </section>
        </div>
      </div>
    </>
  );
}

async function PhoneCard() {
  await connection();
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  if (!host) return null;
  const url = `${protocol}://${host}/asistente`;
  const svg = await QRCode.toString(url, { type: "svg", margin: 1, width: 140 });
  return (
    <div className="card-soft flex flex-wrap items-center gap-6 p-6">
      {/* eslint-disable-next-line @next/next/no-img-element -- código QR generado en el servidor */}
      <img
        src={`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`}
        alt="Código QR para abrir el chat del asistente en el celular"
        width={140}
        height={140}
        className="rounded-xl"
      />
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-2 font-semibold">
          <Smartphone className="h-4 w-4" aria-hidden /> Ábrelo en tu celular
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Escanea el código o comparte este enlace por cualquier medio:{" "}
          <span className="break-all font-mono text-xs">{url}</span>
        </p>
      </div>
    </div>
  );
}
