"use client";

import { LockKeyhole } from "lucide-react";
import Link from "next/link";
import { useActionState } from "react";

import type { AuditorLoginMethod } from "@/lib/auth/access";

import { login, type LoginState } from "./actions";

const initialState: LoginState = { error: null };
const inputClass = "mt-2 h-11 w-full rounded-full border border-input bg-background px-4 text-sm";

export function LoginForm({ next, method }: { next: string; method: AuditorLoginMethod }) {
  const [state, action, pending] = useActionState(login, initialState);
  const errorProps = state.error ? { "aria-describedby": "error-acceso", "aria-invalid": true } : {};
  return (
    <form action={action} className="card-soft mt-8 space-y-4 p-6">
      <input type="hidden" name="next" value={next} />
      {method === "cuentas" ? (
        <>
          <div>
            <label htmlFor="email" className="text-sm font-semibold">
              Correo electrónico
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="username"
              defaultValue={state.email}
              className={inputClass}
              {...errorProps}
            />
          </div>
          <div>
            <label htmlFor="password" className="text-sm font-semibold">
              Contraseña
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              autoComplete="current-password"
              className={inputClass}
              {...errorProps}
            />
          </div>
        </>
      ) : (
        <div>
          <label htmlFor="codigo" className="text-sm font-semibold">
            Código de acceso
          </label>
          <input
            id="codigo"
            name="codigo"
            type="password"
            required
            autoComplete="current-password"
            className={inputClass}
            {...errorProps}
          />
        </div>
      )}
      {state.error && (
        <p id="error-acceso" role="alert" className="text-sm text-destructive">
          {state.error}
        </p>
      )}
      <button type="submit" className="btn-dark w-full" disabled={pending}>
        <LockKeyhole className="h-4 w-4" aria-hidden /> {pending ? "Verificando…" : "Entrar"}
      </button>
      {method === "cuentas" && (
        <p className="text-center text-sm">
          <Link href="/acceso/recuperar" className="underline underline-offset-4">
            ¿Olvidaste tu contraseña?
          </Link>
        </p>
      )}
    </form>
  );
}
