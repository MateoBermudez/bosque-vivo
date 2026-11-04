"use client";

import { LockKeyhole, MailCheck, RotateCw } from "lucide-react";
import Link from "next/link";
import { useActionState } from "react";

import type { AuditorLoginMethod } from "@/lib/auth/access";

import { login, type LoginState } from "./actions";

const initialState: LoginState = { error: null, step: "credenciales" };
const inputClass = "mt-2 h-11 w-full rounded-full border border-input bg-background px-4 text-sm";

function Messages({ state }: { state: LoginState }) {
  return (
    <>
      {state.notice && !state.error && (
        <p role="status" className="text-sm text-muted-foreground">
          {state.notice}
        </p>
      )}
      {state.error && (
        <p id="error-acceso" role="alert" className="text-sm text-destructive">
          {state.error}
        </p>
      )}
    </>
  );
}

export function LoginForm({ next, method }: { next: string; method: AuditorLoginMethod }) {
  const [state, action, pending] = useActionState(login, initialState);
  const errorProps = state.error ? { "aria-describedby": "error-acceso", "aria-invalid": true } : {};

  if (state.step === "codigo") {
    return (
      <form action={action} className="card-soft mt-8 space-y-4 p-6">
        <input type="hidden" name="next" value={next} />
        <input type="hidden" name="step" value="codigo" />
        <input type="hidden" name="challenge" value={state.challenge ?? ""} />
        <div>
          <label htmlFor="codigo-verificacion" className="text-sm font-semibold">
            Código de verificación
          </label>
          <p className="mt-1 text-xs text-muted-foreground">
            Lo enviamos a {state.destination ?? "tu correo"}. Vence en 10 minutos.
          </p>
          <input
            id="codigo-verificacion"
            name="codigo"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="\d{6}"
            maxLength={6}
            autoFocus
            className={`${inputClass} text-center font-mono text-lg tracking-[0.5em]`}
            {...errorProps}
          />
        </div>
        <Messages state={state} />
        <button type="submit" name="intent" value="verificar" className="btn-dark w-full" disabled={pending}>
          <MailCheck className="h-4 w-4" aria-hidden /> {pending ? "Verificando…" : "Verificar"}
        </button>
        <button
          type="submit"
          name="intent"
          value="reenviar"
          formNoValidate
          className="btn-outline w-full"
          disabled={pending}
        >
          <RotateCw className="h-4 w-4" aria-hidden /> Reenviar código
        </button>
      </form>
    );
  }

  return (
    <form action={action} className="card-soft mt-8 space-y-4 p-6">
      <input type="hidden" name="next" value={next} />
      <input type="hidden" name="step" value="credenciales" />
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
      <Messages state={state} />
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
