import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE, auditorSession, hasAuditorAccess } from "@/lib/auth/access";

// Protege el área de auditores: el chat y las trazas consumen la cuota de IA y las trazas
// contienen preguntas de usuarios. Además, el asistente comunitario es para el público: quien
// tiene sesión de auditor usa su propio chat.
export async function proxy(request: NextRequest) {
  const cookie = request.cookies.get(SESSION_COOKIE)?.value;

  if (request.nextUrl.pathname === "/asistente") {
    if (await auditorSession(cookie)) {
      const destination = request.nextUrl.clone();
      destination.pathname = "/chat";
      destination.search = "";
      return NextResponse.redirect(destination);
    }
    return NextResponse.next();
  }

  if (await hasAuditorAccess(cookie)) {
    return NextResponse.next();
  }

  if (request.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const login = request.nextUrl.clone();
  login.pathname = "/acceso";
  login.search = `?next=${encodeURIComponent(request.nextUrl.pathname + request.nextUrl.search)}`;
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/chat/:path*", "/trazas/:path*", "/api/chat/:path*", "/asistente"],
};
