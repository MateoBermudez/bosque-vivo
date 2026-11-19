import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { z } from "zod";

import { BackendError, communityApi } from "@/lib/api/backend";
import { createThrottle } from "@/lib/auth/throttle";

const MAX_MEDIA_BASE64 = 4_000_004;

const sessionRef = z.string().regex(/^[A-Za-z0-9-]{8,64}$/);
const bodySchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("text"), session_ref: sessionRef, message: z.string().trim().min(1).max(1000) }),
  z.object({
    kind: z.literal("location"),
    session_ref: sessionRef,
    latitude: z.number().min(-90).max(90),
    longitude: z.number().min(-180).max(180),
  }),
  z.object({
    kind: z.enum(["image", "audio"]),
    session_ref: sessionRef,
    message: z.string().trim().max(1000).optional(),
    media_base64: z.string().min(4).max(MAX_MEDIA_BASE64),
    mime_type: z.string().max(60),
  }),
]);

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
    if (payload && typeof payload === "object" && !("kind" in payload)) payload = { ...payload, kind: "text" };
  } catch {
    return NextResponse.json({ error: "La solicitud no es válida." }, { status: 400 });
  }
  const parsed = bodySchema.safeParse(payload);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Escribe un mensaje de hasta 1.000 caracteres, o envía una foto o un audio de hasta 3 MB." },
      { status: 400 },
    );
  }
  const data = parsed.data;
  try {
    const replies =
      data.kind === "text"
        ? await communityApi.send(data.session_ref, data.message)
        : data.kind === "location"
          ? await communityApi.send(data.session_ref, "", {
              kind: "location",
              latitude: data.latitude,
              longitude: data.longitude,
            })
          : await communityApi.send(data.session_ref, data.message ?? "", {
              kind: data.kind,
              media_base64: data.media_base64,
              mime_type: data.mime_type,
            });
    return NextResponse.json({ replies }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof BackendError ? error.message : "El asistente no respondió. Intenta de nuevo.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
