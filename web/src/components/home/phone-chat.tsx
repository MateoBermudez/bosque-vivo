import { Check, MapPin, Mic } from "lucide-react";
import Image from "next/image";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

function Bubble({ me, children }: { me?: boolean; children: ReactNode }) {
  return (
    <div className={cn("flex", me ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-3 py-2",
          me ? "rounded-br-sm bg-lime text-lime-foreground" : "rounded-bl-sm glass",
        )}
      >
        {children}
        {me && <Check className="ml-1 inline h-3 w-3 opacity-60" aria-hidden />}
      </div>
    </div>
  );
}

/** Maqueta ilustrativa de una conversación con el asistente. */
export function PhoneChat() {
  return (
    <div
      className="mx-auto w-full max-w-[340px] rounded-[2.6rem] bg-forest p-3 shadow-[var(--shadow-soft)]"
      role="img"
      aria-label="Ejemplo de conversación con el asistente de WhatsApp: una persona comparte su ubicación, una foto y una nota de voz, y el asistente responde."
    >
      <div className="rounded-[2.1rem] bg-forest-2 p-4 text-forest-foreground">
        <div className="mb-4 flex items-center gap-3 border-b border-forest-foreground/10 pb-3">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-lime text-sm font-bold text-lime-foreground">
            BV
          </span>
          <div>
            <p className="text-sm font-semibold">Bosque Vivo</p>
            <p className="text-xs text-forest-muted">Asistente · en línea</p>
          </div>
        </div>
        <div className="space-y-3 text-sm">
          <Bubble me>Hola, ¿el bosque cerca de mi vereda está dentro de un proyecto?</Bubble>
          <Bubble me>
            <span className="flex items-center gap-2">
              <MapPin className="h-4 w-4" aria-hidden /> Ubicación compartida
            </span>
          </Bubble>
          <Bubble>
            Sí. Está dentro de <b>Corredor Andino Las Nubes</b>. Allí el verdor viene aumentando, aunque más
            despacio de lo declarado.
          </Bubble>
          <Bubble me>
            <Image
              src="/images/sat-before.jpg"
              alt=""
              width={256}
              height={192}
              className="h-24 w-full rounded-xl object-cover"
            />
          </Bubble>
          <Bubble me>
            <span className="flex items-center gap-2">
              <Mic className="h-4 w-4" aria-hidden /> Nota de voz · 0:12
            </span>
          </Bubble>
          <Bubble>
            En la foto se ve bosque denso. Soy una IA y puedo equivocarme. Puedes escribir{" "}
            <b>BORRAR MIS DATOS</b> cuando quieras.
          </Bubble>
        </div>
      </div>
    </div>
  );
}
