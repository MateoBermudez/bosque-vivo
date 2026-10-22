import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE, hasAuditorAccess } from "@/lib/auth/access";

// Protege el área de auditores: el chat y las trazas consumen la cuota de IA y las trazas
// contienen preguntas de usuarios.
export async function proxy(request: NextRequest) {
  if (await hasAuditorAccess(request.cookies.get(SESSION_COOKIE)?.value)) {
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
  matcher: ["/chat/:path*", "/trazas/:path*", "/api/chat/:path*"],
};
