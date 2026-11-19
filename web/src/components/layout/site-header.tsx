import { cookies } from "next/headers";

import { SESSION_COOKIE, auditorAccessMode, auditorSession } from "@/lib/auth/access";

import { SiteHeaderView } from "./site-header-view";

/**
 * Lee la sesión en el servidor para que el encabezado sepa si quien navega es un auditor.
 * Debe renderizarse dentro de un <Suspense> (lo hace el layout): leer cookies es un dato de la petición.
 */
export async function SiteHeader() {
  const session = await auditorSession((await cookies()).get(SESSION_COOKIE)?.value);
  return <SiteHeaderView auditor={session !== null} openMode={auditorAccessMode() === "open"} />;
}
