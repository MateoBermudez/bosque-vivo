import type { Metadata } from "next";
import { cookies } from "next/headers";
import { Suspense } from "react";

import { ErrorState } from "@/components/common/states";
import { SESSION_COOKIE, auditorAccessMode, hasAuditorAccess, safeNextPath } from "@/lib/auth/access";

import { logout } from "./actions";
import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "Acceso de auditores",
  robots: { index: false },
};

export default function AccessPage({ searchParams }: PageProps<"/acceso">) {
  return (
    <div className="mx-auto max-w-md px-5 py-16">
      <p className="eyebrow">Área de auditores</p>
      <h1 className="mt-2 text-3xl font-extrabold">Acceso</h1>
      <p className="mt-3 text-muted-foreground">
        El chat del auditor y las trazas del agente usan la cuota de IA y muestran preguntas de usuarios, por eso
        requieren un código.
      </p>
      <Suspense>
        <AccessContent searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function AccessContent({ searchParams }: Pick<PageProps<"/acceso">, "searchParams">) {
  const mode = auditorAccessMode();
  const { next } = await searchParams;
  const target = safeNextPath(typeof next === "string" ? next : undefined);

  if (mode === "disabled") {
    return (
      <div className="mt-8">
        <ErrorState
          retry={false}
          message="El área de auditores está desactivada: falta configurar AUDITOR_ACCESS_CODE y SESSION_SECRET en el servidor."
        />
      </div>
    );
  }
  if (mode === "open") {
    return (
      <p className="card-soft mt-8 p-6 text-sm text-muted-foreground">
        Estás en desarrollo y el acceso de auditores no está configurado, así que el área está abierta. Define{" "}
        <code className="font-mono">AUDITOR_ACCESS_CODE</code> y <code className="font-mono">SESSION_SECRET</code> para
        protegerla.
      </p>
    );
  }

  const signedIn = await hasAuditorAccess((await cookies()).get(SESSION_COOKIE)?.value);
  if (signedIn) {
    return (
      <form action={logout} className="card-soft mt-8 space-y-4 p-6">
        <p className="text-sm">Ya iniciaste sesión como auditor.</p>
        <button type="submit" className="btn-outline">
          Cerrar sesión
        </button>
      </form>
    );
  }
  return <LoginForm next={target} />;
}
