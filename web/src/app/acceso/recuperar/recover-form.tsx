"use client";

import { Mail } from "lucide-react";
import { useActionState } from "react";

import { requestPasswordReset, type RecoverState } from "./actions";

const initialState: RecoverState = { message: null, error: null };

export function RecoverForm() {
  const [state, action, pending] = useActionState(requestPasswordReset, initialState);
  if (state.message) {
    return (
      <p role="status" className="card-soft mt-8 p-6 text-sm">
        {state.message}
      </p>
    );
  }
  return (
    <form action={action} className="card-soft mt-8 space-y-4 p-6">
      <div>
        <label htmlFor="email" className="text-sm font-semibold">
          Correo electrónico registrado
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          aria-describedby={state.error ? "error-recuperar" : undefined}
          aria-invalid={state.error ? true : undefined}
          className="mt-2 h-11 w-full rounded-full border border-input bg-background px-4 text-sm"
        />
      </div>
      {state.error && (
        <p id="error-recuperar" role="alert" className="text-sm text-destructive">
          {state.error}
        </p>
      )}
      <button type="submit" className="btn-dark w-full" disabled={pending}>
        <Mail className="h-4 w-4" aria-hidden /> {pending ? "Enviando…" : "Enviar instrucciones"}
      </button>
    </form>
  );
}
