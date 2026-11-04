"use server";

import { createHash, timingSafeEqual } from "node:crypto";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { BackendError, accountsApi } from "@/lib/api/backend";
import { SESSION_COOKIE, auditorAccessMode, auditorLoginMethod, safeNextPath } from "@/lib/auth/access";
import { clientKey } from "@/lib/auth/client-key";
import { SESSION_TTL_SECONDS, createSessionToken } from "@/lib/auth/session";
import { createThrottle } from "@/lib/auth/throttle";

export interface LoginState {
  error: string | null;
  email?: string;
}

const throttle = createThrottle(5, 10 * 60 * 1000);

function digest(value: string): Buffer {
  return createHash("sha256").update(value).digest();
}

function pause(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 600));
}

async function verifyCredentials(formData: FormData): Promise<{ subject: string } | { error: string }> {
  if (auditorLoginMethod() === "codigo") {
    const submitted = String(formData.get("codigo") ?? "");
    const valid = timingSafeEqual(digest(submitted), digest(process.env.AUDITOR_ACCESS_CODE!));
    return valid ? { subject: "codigo" } : { error: "El código no es correcto." };
  }
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return { error: "Escribe tu correo y tu contraseña." };
  try {
    const user = await accountsApi.login(email, password);
    return { subject: user.email };
  } catch (error) {
    if (error instanceof BackendError && (error.status === 401 || error.status === 429)) {
      return { error: error.message };
    }
    if (error instanceof BackendError) return { error: error.message };
    throw error;
  }
}

export async function login(_previous: LoginState, formData: FormData): Promise<LoginState> {
  if (auditorAccessMode() !== "protected") {
    return { error: "El acceso de auditores no está configurado en este servidor." };
  }
  const email = String(formData.get("email") ?? "");
  const key = await clientKey();
  if (throttle.blocked(key)) {
    return { error: "Demasiados intentos. Espera unos minutos e inténtalo de nuevo.", email };
  }
  const outcome = await verifyCredentials(formData);
  if ("error" in outcome) {
    throttle.fail(key);
    await pause();
    return { error: outcome.error, email };
  }
  throttle.reset(key);
  (await cookies()).set(SESSION_COOKIE, await createSessionToken(process.env.SESSION_SECRET!, outcome.subject), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  });
  redirect(safeNextPath(String(formData.get("next") ?? "")));
}

export async function logout(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/");
}
