import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { z } from "zod";

import { BackendError, communityApi } from "@/lib/api/backend";
import { createThrottle } from "@/lib/auth/throttle";

const bodySchema = z.object({
  session_ref: z.string().regex(/^[A-Za-z0-9-]{8,64}$/),
  message: z.string().trim().min(1).max(1000),
});

const throttle = createThrottle(40, 10 * 60 * 1000);

export async function POST(request: NextRequest) {
  if (process.env.BV_DATA_SOURCE !== "live") {
    return NextResponse.json(
      { error: "El chat en línea necesita la API de Bosque Vivo encendida (modo live)." },
      { status: 503 },
    );
  }
  const origin = request.headers.get("origin");
  if (origin && new URL(origin).host !== request.headers.get("host")) {
    return NextResponse.json({ error: "Origen no permitido" }, { status: 403 });
  }
  const key = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  if (throttle.blocked(key)) {
    return NextResponse.json({ error: "Escribiste muchos mensajes seguidos. Espera unos minutos." }, { status: 429 });
  }
  throttle.fail(key);
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "La solicitud no es válida." }, { status: 400 });
  }
  const parsed = bodySchema.safeParse(payload);
  if (!parsed.success) {
    return NextResponse.json({ error: "Escribe un mensaje de hasta 1.000 caracteres." }, { status: 400 });
  }
  try {
    const replies = await communityApi.send(parsed.data.session_ref, parsed.data.message);
    return NextResponse.json({ replies }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof BackendError ? error.message : "El asistente no respondió. Intenta de nuevo.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
