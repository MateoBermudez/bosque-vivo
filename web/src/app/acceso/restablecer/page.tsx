import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { BackendError, accountsApi } from "@/lib/api/backend";
import { auditorLoginMethod } from "@/lib/auth/access";

import { ResetForm } from "./reset-form";

export const metadata: Metadata = {
  title: "Elegir contraseña",
  robots: { index: false },
  referrer: "no-referrer",
};

export default function ResetPage({ searchParams }: PageProps<"/acceso/restablecer">) {
  return (
    <div className="mx-auto max-w-md px-5 py-16">
      <p className="eyebrow">Área de auditores</p>
      <h1 className="mt-2 text-3xl font-extrabold">Elegir contraseña</h1>
      <Suspense>
        <ResetContent searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

function Problem({ message }: { message: string }) {
  return (
    <div role="alert" className="card-soft mt-8 space-y-4 p-6 text-sm">
      <p>{message}</p>
      <Link href="/acceso/recuperar" className="btn-dark w-full">
        Solicitar un nuevo enlace
      </Link>
    </div>
  );
}

async function ResetContent({ searchParams }: Pick<PageProps<"/acceso/restablecer">, "searchParams">) {
  const { token } = await searchParams;
  if (auditorLoginMethod() !== "cuentas") {
    return <Problem message="La recuperación de contraseña requiere la API en vivo." />;
  }
  if (typeof token !== "string" || !token) {
    return <Problem message="El enlace no es válido. Solicita uno nuevo." />;
  }
  let status;
  try {
    status = await accountsApi.verifyReset(token);
  } catch (error) {
    if (error instanceof BackendError) return <Problem message={error.message} />;
    throw error;
  }
  if (status.status !== "valido") {
    return <Problem message={status.detail ?? "El enlace no es válido. Solicita uno nuevo."} />;
  }
  return (
    <>
      <p className="mt-3 text-muted-foreground">
        {status.purpose === "invitacion"
          ? "Bienvenido al área de auditores. Elige la contraseña de tu cuenta para activarla."
          : "Elige una contraseña nueva para tu cuenta de auditor."}
      </p>
      <ResetForm token={token} />
    </>
  );
}
