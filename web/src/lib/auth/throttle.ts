export interface Throttle {
  blocked(key: string, now?: number): boolean;
  fail(key: string, now?: number): void;
  reset(key: string): void;
}

export function createThrottle(maxFailures: number, lockMs: number): Throttle {
  const entries = new Map<string, { count: number; lockedUntil: number }>();
  return {
    blocked(key, now = Date.now()) {
      const entry = entries.get(key);
      return Boolean(entry && entry.lockedUntil > now);
    },
    fail(key, now = Date.now()) {
      const entry = entries.get(key);
      const previous = entry && (entry.lockedUntil === 0 || entry.lockedUntil > now) ? entry.count : 0;
      const count = previous + 1;
      entries.set(key, { count, lockedUntil: count >= maxFailures ? now + lockMs : 0 });
    },
    reset(key) {
      entries.delete(key);
    },
  };
}

export const PASSWORD_RULES = "Mínimo 10 caracteres, con al menos una letra y un número.";

export function passwordProblem(password: string, confirmation: string): string | null {
  if (password !== confirmation) return "Las contraseñas no coinciden.";
  if (password.length < 10) return "La contraseña debe tener al menos 10 caracteres.";
  if (!/[A-Za-zÁÉÍÓÚÑáéíóúñ]/.test(password) || !/\d/.test(password)) {
    return "La contraseña debe incluir al menos una letra y un número.";
  }
  return null;
}
