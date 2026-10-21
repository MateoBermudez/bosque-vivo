"use server";

import { createHash, timingSafeEqual } from "node:crypto";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { SESSION_COOKIE, auditorAccessMode, safeNextPath } from "@/lib/auth/access";
import { SESSION_TTL_SECONDS, createSessionToken } from "@/lib/auth/session";

export interface LoginState {
  error: string | null;
}

const MAX_FAILURES = 5;
const LOCK_MS = 10 * 60 * 1000;
const failures = new Map<string, { count: number; lockedUntil: number }>();

function digest(value: string): Buffer {
  return createHash("sha256").update(value).digest();
}

async function clientKey(): Promise<string> {
  const forwarded = (await headers()).get("x-forwarded-for");
  return forwarded?.split(",")[0]?.trim() || "local";
}

export async function login(_previous: LoginState, formData: FormData): Promise<LoginState> {
  if (auditorAccessMode() !== "protected") {
    return { error: "El acceso de auditores no está configurado en este servidor." };
  }

  const key = await clientKey();
  const now = Date.now();
  const entry = failures.get(key);
  if (entry && entry.lockedUntil > now) {
    return { error: "Demasiados intentos. Espera unos minutos e inténtalo de nuevo." };
  }

  const submitted = String(formData.get("codigo") ?? "");
  const expected = process.env.AUDITOR_ACCESS_CODE!;
  const valid = timingSafeEqual(digest(submitted), digest(expected));

  if (!valid) {
    // Un bloqueo vencido reinicia la cuenta.
    const previous = entry && (entry.lockedUntil === 0 || entry.lockedUntil > now) ? entry.count : 0;
    const count = previous + 1;
    failures.set(key, { count, lockedUntil: count >= MAX_FAILURES ? now + LOCK_MS : 0 });
    await new Promise((resolve) => setTimeout(resolve, 600));
    return { error: "El código no es correcto." };
  }

  failures.delete(key);
  (await cookies()).set(SESSION_COOKIE, await createSessionToken(process.env.SESSION_SECRET!), {
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
