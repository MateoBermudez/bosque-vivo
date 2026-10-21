import { Image as ImageIcon, MapPin, MessageCircle, Mic, ShieldCheck, Type } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import QRCode from "qrcode";
import { Suspense } from "react";

import { PageHeader } from "@/components/common/page-header";
import { PhoneChat } from "@/components/home/phone-chat";

export const metadata: Metadata = {
  title: "Asistente de WhatsApp",
  description:
    "Pregunta por el estado de un bosque en español sencillo: escribe, comparte tu ubicación, una foto o una nota de voz.",
};

const STEPS = [
  { title: "Escribe «Hola»", text: "El asistente se presenta y te recuerda que es una inteligencia artificial y que puede equivocarse." },
  { title: "Lee el aviso y escribe ACEPTO", text: "Sin tu autorización no puede ayudarte. El aviso explica qué datos se usan y quién los procesa." },
  { title: "Pregunta con tus palabras", text: "Por ejemplo: «¿cómo está el bosque de mi finca?». Puedes compartir tu ubicación para que encuentre el proyecto." },
  { title: "Si quieres enviar fotos o audios, escribe ACEPTO FOTOS", text: "Es un permiso aparte, porque se procesan con un servicio externo y son información sin verificar." },
  { title: "Cuando quieras, escribe BORRAR MIS DATOS", text: "Se eliminan tu registro, tus permisos y tus consultas." },
] as const;

const CAPABILITIES = [
  { icon: Type, title: "Texto", text: "Preguntas cortas, en lenguaje cotidiano." },
  { icon: MapPin, title: "Ubicación", text: "Comparte tu punto y te decimos si cae dentro de un proyecto." },
  { icon: ImageIcon, title: "Fotos", text: "Describe lo que se ve y lo compara con el satélite. Es evidencia comunitaria, no verificada." },
  { icon: Mic, title: "Notas de voz", text: "Si no quieres escribir, cuéntale tu pregunta hablando." },
] as const;

export default function WhatsAppPage() {
  return (
    <>
      <PageHeader eyebrow="Asistente de IA" title="Pregunta por WhatsApp, en español sencillo">
        Mensajes cortos desde el celular para saber qué se ve desde el satélite en el bosque de tu territorio.
      </PageHeader>

      <div className="mx-auto grid max-w-7xl gap-10 px-5 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-12">
          <section aria-labelledby="titulo-empezar">
            <h2 id="titulo-empezar" className="text-2xl font-extrabold">
              Empieza en un minuto
            </h2>
            <Suspense fallback={<div className="card-soft mt-4 h-32 animate-pulse" />}>
              <StartCard />
            </Suspense>
            <ol className="mt-6 space-y-3">
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
              <li>Tu número de teléfono se guarda solo como una huella cifrada; no se almacena el número.</li>
              <li>
                Un servicio de un tercero (Google Gemini) procesa los mensajes, posiblemente fuera de Colombia. No
                envíes cédula, dirección ni datos privados.
              </li>
              <li>Las fotos y los audios se procesan y se descartan; no se guardan los archivos.</li>
              <li>Puedes pedir que se borren tus datos cuando quieras.</li>
            </ul>
            <Link href="/privacidad" className="btn-lime mt-6">
              Leer el aviso de privacidad
            </Link>
          </section>
        </div>

        <div className="lg:sticky lg:top-24 lg:self-start">
          <PhoneChat />
          <p className="mt-4 text-center text-xs text-muted-foreground">Conversación de ejemplo.</p>
        </div>
      </div>
    </>
  );
}

async function StartCard() {
  await connection();
  const number = (process.env.WHATSAPP_PUBLIC_NUMBER ?? "").replace(/\D/g, "");
  if (number.length < 8) {
    return (
      <div className="card-soft mt-4 flex items-start gap-3 p-6">
        <MessageCircle className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" aria-hidden />
        <p className="text-sm text-muted-foreground">
          El número del asistente se publicará aquí cuando empiece el piloto. Durante el piloto, el acceso es por
          invitación.
        </p>
      </div>
    );
  }
  const url = `https://wa.me/${number}?text=${encodeURIComponent("Hola")}`;
  const svg = await QRCode.toString(url, { type: "svg", margin: 1, width: 160 });
  return (
    <div className="card-soft mt-4 flex flex-wrap items-center gap-6 p-6">
      {/* eslint-disable-next-line @next/next/no-img-element -- código QR generado en el servidor */}
      <img
        src={`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`}
        alt="Código QR para abrir el chat del asistente en WhatsApp"
        width={160}
        height={160}
        className="rounded-xl"
      />
      <div>
        <p className="font-semibold">Escanea el código o abre el chat desde tu celular.</p>
        <a href={url} className="btn-lime mt-4" rel="noopener noreferrer" target="_blank">
          <MessageCircle className="h-4 w-4" aria-hidden /> Abrir en WhatsApp
        </a>
      </div>
    </div>
  );
}
