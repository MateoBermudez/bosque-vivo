"use server";

import { createHash, timingSafeEqual } from "node:crypto";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { BackendError, accountsApi } from "@/lib/api/backend";
import { SESSION_COOKIE, auditorAccessMode, auditorLoginMethod, safeNextPath } from "@/lib/auth/access";
import { clientKey } from "@/lib/auth/client-key";
import { SESSION_TTL_SECONDS, createSessionToken } from "@/lib/auth/session";
import { createThrottle } from "@/lib/auth/throttle";

export interface LoginState {
  error: string | null;
  notice?: string | null;
  email?: string;
  step: "credenciales" | "codigo";
  challenge?: string;
  destination?: string;
}

const throttle = createThrottle(8, 10 * 60 * 1000);

function digest(value: string): Buffer {
  return createHash("sha256").update(value).digest();
}

function pause(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 600));
}

async function describeClient(): Promise<string> {
  const agent = (await headers()).get("user-agent") ?? "navegador desconocido";
  const browser = /Edg\//.test(agent)
    ? "Edge"
    : /Chrome\//.test(agent)
      ? "Chrome"
      : /Firefox\//.test(agent)
        ? "Firefox"
        : /Safari\//.test(agent)
          ? "Safari"
          : "otro navegador";
  const system = /Windows/.test(agent)
    ? "Windows"
    : /Android/.test(agent)
      ? "Android"
      : /iPhone|iPad/.test(agent)
        ? "iOS"
        : /Mac OS/.test(agent)
          ? "macOS"
          : /Linux/.test(agent)
            ? "Linux"
            : "sistema desconocido";
  return `${browser} en ${system}, IP ${await clientKey()}`;
}

async function startSession(subject: string, next: string): Promise<never> {
  (await cookies()).set(SESSION_COOKIE, await createSessionToken(process.env.SESSION_SECRET!, subject), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  });
  redirect(safeNextPath(next));
}

function backendMessage(error: unknown): string {
  if (error instanceof BackendError) return error.message;
  throw error;
}

async function withCode(formData: FormData, previous: LoginState): Promise<LoginState> {
  const challenge = String(formData.get("challenge") ?? "");
  const base: LoginState = { error: null, step: "codigo", challenge, destination: previous.destination };
  if (formData.get("intent") === "reenviar") {
    try {
      const destination = await accountsApi.resendCode(challenge);
      return { ...base, destination, notice: `Enviamos un código nuevo a ${destination}.` };
    } catch (error) {
      return { ...base, error: backendMessage(error) };
    }
  }
  const code = String(formData.get("codigo") ?? "").replace(/\s/g, "");
  if (!/^\d{6}$/.test(code)) return { ...base, error: "Escribe los 6 dígitos del código." };
  let subject: string;
  try {
    subject = (await accountsApi.verifyCode(challenge, code)).email;
  } catch (error) {
    await pause();
    if (error instanceof BackendError && error.status === 410) {
      return { error: error.message, step: "credenciales" };
    }
    return { ...base, error: backendMessage(error) };
  }
  return startSession(subject, String(formData.get("next") ?? ""));
}

export async function login(previous: LoginState, formData: FormData): Promise<LoginState> {
  if (auditorAccessMode() !== "protected") {
    return { error: "El acceso de auditores no está configurado en este servidor.", step: "credenciales" };
  }
  const key = await clientKey();
  if (throttle.blocked(key)) {
    return { error: "Demasiados intentos. Espera unos minutos e inténtalo de nuevo.", step: "credenciales" };
  }
  if (formData.get("step") === "codigo") {
    const state = await withCode(formData, previous);
    if (state.error) throttle.fail(key);
    return state;
  }
  const next = String(formData.get("next") ?? "");
  if (auditorLoginMethod() === "codigo") {
    const submitted = String(formData.get("codigo") ?? "");
    if (!timingSafeEqual(digest(submitted), digest(process.env.AUDITOR_ACCESS_CODE!))) {
      throttle.fail(key);
      await pause();
      return { error: "El código no es correcto.", step: "credenciales" };
    }
    throttle.reset(key);
    return startSession("codigo", next);
  }
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return { error: "Escribe tu correo y tu contraseña.", email, step: "credenciales" };
  let result;
  try {
    result = await accountsApi.login(email, password, await describeClient());
  } catch (error) {
    throttle.fail(key);
    await pause();
    return { error: backendMessage(error), email, step: "credenciales" };
  }
  throttle.reset(key);
  if (result.status === "codigo") {
    return {
      error: null,
      email,
      step: "codigo",
      challenge: result.challenge,
      destination: result.destination,
      notice: `Enviamos un código de 6 dígitos a ${result.destination}.`,
    };
  }
  return startSession(result.user.email, next);
}

export async function logout(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/");
}
