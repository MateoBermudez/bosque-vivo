export const SESSION_COOKIE = "bv_auditor";
export const SESSION_TTL_SECONDS = 8 * 60 * 60;

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const VERSION = "v2";
const MAX_SUBJECT_BYTES = 254;

export interface AuditorSession {
  subject: string;
  expires: number;
}

async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [
    "sign",
    "verify",
  ]);
}

function toHex(buffer: ArrayBuffer | Uint8Array): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  return [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function fromHex(hex: string): Uint8Array<ArrayBuffer> | null {
  if (hex.length === 0 || hex.length % 2 !== 0 || !/^[0-9a-f]+$/.test(hex)) return null;
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return bytes;
}

export async function createSessionToken(
  secret: string,
  subject: string = "auditor",
  now: number = Date.now(),
  ttlSeconds: number = SESSION_TTL_SECONDS,
): Promise<string> {
  const encodedSubject = encoder.encode(subject.slice(0, MAX_SUBJECT_BYTES));
  const expires = Math.floor(now / 1000) + ttlSeconds;
  const payload = `${VERSION}.${expires}.${toHex(encodedSubject)}`;
  const signature = await crypto.subtle.sign("HMAC", await hmacKey(secret), encoder.encode(payload));
  return `${payload}.${toHex(signature)}`;
}

export async function readSessionToken(
  token: string,
  secret: string,
  now: number = Date.now(),
): Promise<AuditorSession | null> {
  const parts = token.split(".");
  if (parts.length !== 4 || parts[0] !== VERSION) return null;
  const expires = Number(parts[1]);
  if (!Number.isInteger(expires) || expires * 1000 < now) return null;
  const subjectBytes = fromHex(parts[2] ?? "");
  const signature = fromHex(parts[3] ?? "");
  if (!subjectBytes || !signature) return null;
  const valid = await crypto.subtle.verify(
    "HMAC",
    await hmacKey(secret),
    signature,
    encoder.encode(`${VERSION}.${expires}.${parts[2]}`),
  );
  if (!valid) return null;
  return { subject: decoder.decode(subjectBytes), expires };
}

export async function verifySessionToken(token: string, secret: string, now: number = Date.now()): Promise<boolean> {
  return (await readSessionToken(token, secret, now)) !== null;
}
