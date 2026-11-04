import type { Metadata } from "next";
import Link from "next/link";

import { RecoverForm } from "./recover-form";

export const metadata: Metadata = {
  title: "Recuperar contraseña",
  robots: { index: false },
};

export default function RecoverPage() {
  return (
    <div className="mx-auto max-w-md px-5 py-16">
      <p className="eyebrow">Área de auditores</p>
      <h1 className="mt-2 text-3xl font-extrabold">Recuperar contraseña</h1>
      <p className="mt-3 text-muted-foreground">
        Escribe el correo con el que te registraron. Te enviaremos un enlace de un solo uso para elegir una nueva
        contraseña.
      </p>
      <RecoverForm />
      <p className="mt-6 text-center text-sm">
        <Link href="/acceso" className="underline underline-offset-4">
          Volver a iniciar sesión
        </Link>
      </p>
    </div>
  );
}
