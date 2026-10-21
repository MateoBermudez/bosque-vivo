"use client";

import { LockKeyhole } from "lucide-react";
import { useActionState } from "react";

import { login, type LoginState } from "./actions";

const initialState: LoginState = { error: null };

export function LoginForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState(login, initialState);
  return (
    <form action={action} className="card-soft mt-8 space-y-4 p-6">
      <input type="hidden" name="next" value={next} />
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
          aria-describedby={state.error ? "error-acceso" : undefined}
          aria-invalid={state.error ? true : undefined}
          className="mt-2 h-11 w-full rounded-full border border-input bg-background px-4 text-sm"
        />
      </div>
      {state.error && (
        <p id="error-acceso" role="alert" className="text-sm text-destructive">
          {state.error}
        </p>
      )}
      <button type="submit" className="btn-dark w-full" disabled={pending}>
        <LockKeyhole className="h-4 w-4" aria-hidden /> {pending ? "Verificando…" : "Entrar"}
      </button>
    </form>
  );
}
