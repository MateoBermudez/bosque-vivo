import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { attempt, getApi } from "@/lib/api";
import { chatRequestSchema } from "@/lib/api/schema";
import { SESSION_COOKIE, hasAuditorAccess } from "@/lib/auth/access";

// Intermediario entre el navegador y el agente: el token de administración del backend
// vive solo en el servidor de este sitio y nunca llega al navegador.
export async function POST(request: NextRequest) {
  if (!(await hasAuditorAccess(request.cookies.get(SESSION_COOKIE)?.value))) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const origin = request.headers.get("origin");
  if (origin && new URL(origin).host !== request.headers.get("host")) {
    return NextResponse.json({ error: "Origen no permitido" }, { status: 403 });
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "La solicitud no es válida." }, { status: 400 });
  }
  const parsed = chatRequestSchema.safeParse(payload);
  if (!parsed.success) {
    return NextResponse.json({ error: "Escribe un mensaje de hasta 2.000 caracteres." }, { status: 400 });
  }

  const result = await attempt(() => getApi().chat(parsed.data.message, `web-${parsed.data.session_ref}`.slice(0, 60)));
  if (!result.ok) {
    return NextResponse.json({ error: result.message }, { status: 502 });
  }
  return NextResponse.json(result.data, { headers: { "Cache-Control": "no-store" } });
}
