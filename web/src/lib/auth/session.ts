// Sesión del área de auditores: una cookie firmada con HMAC-SHA256 y fecha de vencimiento.
// Usa solo Web Crypto para poder ejecutarse tanto en `proxy.ts` como en rutas y acciones.

export const SESSION_COOKIE = "bv_auditor";
export const SESSION_TTL_SECONDS = 8 * 60 * 60;

const encoder = new TextEncoder();
const VERSION = "v1";

async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [
    "sign",
    "verify",
  ]);
}

function toHex(buffer: ArrayBuffer): string {
  return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function fromHex(hex: string): Uint8Array<ArrayBuffer> | null {
  if (hex.length === 0 || hex.length % 2 !== 0 || !/^[0-9a-f]+$/.test(hex)) return null;
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return bytes;
}

export async function createSessionToken(
  secret: string,
  now: number = Date.now(),
  ttlSeconds: number = SESSION_TTL_SECONDS,
): Promise<string> {
  const expires = Math.floor(now / 1000) + ttlSeconds;
  const payload = `${VERSION}.${expires}`;
  const signature = await crypto.subtle.sign("HMAC", await hmacKey(secret), encoder.encode(payload));
  return `${payload}.${toHex(signature)}`;
}

export async function verifySessionToken(
  token: string,
  secret: string,
  now: number = Date.now(),
): Promise<boolean> {
  const parts = token.split(".");
  if (parts.length !== 3 || parts[0] !== VERSION) return false;
  const expires = Number(parts[1]);
  if (!Number.isInteger(expires) || expires * 1000 < now) return false;
  const signature = fromHex(parts[2] ?? "");
  if (!signature) return false;
  // `verify` compara en tiempo constante.
  return crypto.subtle.verify("HMAC", await hmacKey(secret), signature, encoder.encode(`${VERSION}.${expires}`));
}
