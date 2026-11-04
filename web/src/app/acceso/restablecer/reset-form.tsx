"use client";

import { KeyRound } from "lucide-react";
import Link from "next/link";
import { useActionState } from "react";

import { PASSWORD_RULES } from "@/lib/auth/throttle";

import { confirmPasswordReset, type ResetState } from "./actions";

const initialState: ResetState = { done: false, message: null, error: null, expired: false };
const inputClass = "mt-2 h-11 w-full rounded-full border border-input bg-background px-4 text-sm";

export function ResetForm({ token }: { token: string }) {
  const [state, action, pending] = useActionState(confirmPasswordReset, initialState);
  if (state.done) {
    return (
      <div role="status" className="card-soft mt-8 space-y-4 p-6 text-sm">
        <p>{state.message}</p>
        <Link href="/acceso" className="btn-dark w-full">
          Iniciar sesión
        </Link>
      </div>
    );
  }
  return (
    <form action={action} className="card-soft mt-8 space-y-4 p-6">
      <input type="hidden" name="token" value={token} />
      <div>
        <label htmlFor="password" className="text-sm font-semibold">
          Nueva contraseña
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={10}
          autoComplete="new-password"
          aria-describedby="reglas-clave"
          className={inputClass}
        />
        <p id="reglas-clave" className="mt-2 text-xs text-muted-foreground">
          {PASSWORD_RULES}
        </p>
      </div>
      <div>
        <label htmlFor="confirmacion" className="text-sm font-semibold">
          Repite la contraseña
        </label>
        <input
          id="confirmacion"
          name="confirmacion"
          type="password"
          required
          minLength={10}
          autoComplete="new-password"
          className={inputClass}
        />
      </div>
      {state.error && (
        <p role="alert" className="text-sm text-destructive">
          {state.error}{" "}
          {state.expired && (
            <Link href="/acceso/recuperar" className="underline underline-offset-4">
              Solicitar un nuevo enlace
            </Link>
          )}
        </p>
      )}
      <button type="submit" className="btn-dark w-full" disabled={pending}>
        <KeyRound className="h-4 w-4" aria-hidden /> {pending ? "Guardando…" : "Guardar contraseña"}
      </button>
    </form>
  );
}
