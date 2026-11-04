"use server";

import { BackendError, accountsApi } from "@/lib/api/backend";
import { passwordProblem } from "@/lib/auth/throttle";

export interface ResetState {
  done: boolean;
  message: string | null;
  error: string | null;
  expired: boolean;
}

export async function confirmPasswordReset(_previous: ResetState, formData: FormData): Promise<ResetState> {
  const token = String(formData.get("token") ?? "");
  const password = String(formData.get("password") ?? "");
  const confirmation = String(formData.get("confirmacion") ?? "");
  const problem = passwordProblem(password, confirmation);
  if (problem) return { done: false, message: null, error: problem, expired: false };
  try {
    const message = await accountsApi.confirmReset(token, password);
    return { done: true, message, error: null, expired: false };
  } catch (error) {
    if (error instanceof BackendError) {
      return { done: false, message: null, error: error.message, expired: error.status === 410 };
    }
    throw error;
  }
}
