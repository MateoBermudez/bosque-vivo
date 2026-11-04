import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/common/page-header";
import { CommunityChat } from "@/components/community/community-chat";

export const metadata: Metadata = {
  title: "Chat en línea",
  description:
    "Pregunta por el estado del bosque de tu proyecto desde el navegador, con el mismo asistente de WhatsApp.",
};

export default function CommunityChatPage() {
  return (
    <>
      <PageHeader eyebrow="Asistente comunitario" title="Chat en línea">
        La misma conversación del asistente de WhatsApp, desde el navegador. Sirve cuando WhatsApp no está disponible.
        Antes de responder te pedirá autorización según el{" "}
        <Link href="/privacidad" className="underline underline-offset-4">
          aviso de privacidad
        </Link>
        .
      </PageHeader>
      <div className="mx-auto max-w-2xl px-5 pb-16">
        <CommunityChat />
        <p className="mt-4 text-xs text-muted-foreground">
          Las respuestas describen lo que se ve desde el satélite y pueden contener errores. Escribe BORRAR MIS DATOS
          para eliminar tu conversación.
        </p>
      </div>
    </>
  );
}
