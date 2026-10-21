import type { Metadata } from "next";

import { PageHeader } from "@/components/common/page-header";

export const metadata: Metadata = {
  title: "Aviso de privacidad",
  description:
    "Qué datos trata Bosque Vivo, para qué, quién los procesa y cómo ejercer tus derechos según la Ley 1581 de 2012.",
};

const SECTIONS: { id: string; title: string; body: React.ReactNode }[] = [
  {
    id: "datos",
    title: "Qué datos tratamos",
    body: (
      <ul className="list-disc space-y-2 pl-5">
        <li>
          Tu número de teléfono: se guarda únicamente como una huella cifrada (HMAC); no se almacena el número.
        </li>
        <li>Tus mensajes y las respuestas, para poder atenderte y revisar la calidad del servicio.</li>
        <li>
          Fotos y notas de voz, solo si lo autorizas de forma expresa con <strong>ACEPTO FOTOS</strong>. No se
          guardan los archivos: se procesan y se descartan.
        </li>
      </ul>
    ),
  },
  {
    id: "finalidad",
    title: "Para qué",
    body: <p>Responder consultas sobre el estado de bosques de proyectos de carbono con información satelital.</p>,
  },
  {
    id: "quien",
    title: "Quién procesa",
    body: (
      <p>
        Un asistente de inteligencia artificial. El procesamiento del texto, las imágenes y el audio lo realiza un
        tercero (Google Gemini) en sus servidores, posiblemente fuera de Colombia. No envíes cédula, dirección ni
        datos privados. En la capa gratuita de ese servicio el contenido puede usarse para mejorar sus productos.
      </p>
    ),
  },
  {
    id: "derechos",
    title: "Tus derechos",
    body: (
      <ul className="list-disc space-y-2 pl-5">
        <li>Conocer, actualizar y rectificar tus datos.</li>
        <li>
          Revocar tu autorización y pedir la supresión escribiendo <strong>BORRAR MIS DATOS</strong>: se eliminan tu
          registro, tus permisos y tus consultas.
        </li>
        <li>Hablar con una persona del equipo cuando lo necesites.</li>
      </ul>
    ),
  },
  {
    id: "retencion",
    title: "Retención",
    body: (
      <p>
        Las consultas se conservan solo mientras el usuario no pida su borrado y por el tiempo del piloto.
      </p>
    ),
  },
  {
    id: "limitaciones",
    title: "Limitaciones",
    body: (
      <p>
        Las respuestas pueden contener errores. Describen lo que se observa desde el satélite y no atribuyen
        intenciones a nadie.
      </p>
    ),
  },
];

export default function PrivacyPage() {
  return (
    <>
      <PageHeader eyebrow="Ley 1581 de 2012" title="Aviso de privacidad">
        Versión del aviso: <span className="font-mono">v1</span>. Aplica al asistente de WhatsApp. Este sitio web
        no pide datos personales ni usa cookies de seguimiento; solo usa una cookie técnica de sesión en el área
        de auditores.
      </PageHeader>
      <div className="mx-auto max-w-3xl space-y-4 px-5">
        {SECTIONS.map((section) => (
          <section key={section.id} aria-labelledby={`titulo-${section.id}`} className="card-soft p-6">
            <h2 id={`titulo-${section.id}`} className="text-xl font-bold">
              {section.title}
            </h2>
            <div className="mt-3 text-muted-foreground">{section.body}</div>
          </section>
        ))}
      </div>
    </>
  );
}
