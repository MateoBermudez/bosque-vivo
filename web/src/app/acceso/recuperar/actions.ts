"use server";

import { BackendError, accountsApi } from "@/lib/api/backend";
import { auditorLoginMethod } from "@/lib/auth/access";
import { clientKey } from "@/lib/auth/client-key";
import { createThrottle } from "@/lib/auth/throttle";

export interface RecoverState {
  message: string | null;
  error: string | null;
}

const throttle = createThrottle(5, 15 * 60 * 1000);

export async function requestPasswordReset(_previous: RecoverState, formData: FormData): Promise<RecoverState> {
  if (auditorLoginMethod() !== "cuentas") {
    return { message: null, error: "La recuperación de contraseña requiere la API en vivo." };
  }
  const key = await clientKey();
  if (throttle.blocked(key)) {
    return { message: null, error: "Demasiadas solicitudes. Espera unos minutos e inténtalo de nuevo." };
  }
  throttle.fail(key);
  const email = String(formData.get("email") ?? "").trim();
  if (!email) return { message: null, error: "Escribe tu correo electrónico." };
  try {
    return { message: await accountsApi.requestReset(email), error: null };
  } catch (error) {
    if (error instanceof BackendError) return { message: null, error: error.message };
    throw error;
  }
}
