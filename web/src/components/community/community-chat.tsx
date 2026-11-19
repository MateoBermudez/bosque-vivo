"use client";

import { Camera, MapPin, Mic, SendHorizontal, Square, X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { MAX_RECORDING_SECONDS, VoiceRecorder, currentPosition, encodePhoto } from "@/lib/media";
import { cn } from "@/lib/utils";

type Bubble = { id: number; from: "persona" | "asistente" | "error"; text: string; imageUrl?: string };

type Payload =
  | { kind: "text"; message: string }
  | { kind: "location"; latitude: number; longitude: number }
  | { kind: "image" | "audio"; media_base64: string; mime_type: string; message?: string };

const STORAGE_KEY = "bv_chat_comunitario";
const QUICK = ["Hola", "ACEPTO", "AYUDA", "ESTADO", "ALERTAS", "ACEPTO FOTOS"];

function storedRef(): string {
  try {
    const existing = window.localStorage.getItem(STORAGE_KEY);
    if (existing && /^[A-Za-z0-9-]{8,64}$/.test(existing)) return existing;
    const created = crypto.randomUUID();
    window.localStorage.setItem(STORAGE_KEY, created);
    return created;
  } catch {
    return crypto.randomUUID();
  }
}

function formatSeconds(total: number): string {
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

export function CommunityChat() {
  const inputId = useId();
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const sessionRef = useRef("");
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);
  const photoRef = useRef<HTMLInputElement>(null);
  const recorderRef = useRef<VoiceRecorder | null>(null);
  const autoStopRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    sessionRef.current = storedRef();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [bubbles, pending]);

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => {
      setElapsed(Math.round((Date.now() - (recorderRef.current?.startedAt ?? Date.now())) / 1000));
    }, 250);
    return () => window.clearInterval(timer);
  }, [recording]);

  useEffect(
    () => () => {
      window.clearTimeout(autoStopRef.current);
      recorderRef.current?.cancel();
    },
    [],
  );

  function add(from: Bubble["from"], text: string, imageUrl?: string) {
    setBubbles((current) => [...current, { id: nextId.current++, from, text, imageUrl }]);
  }

  async function deliver(payload: Payload) {
    setPending(true);
    try {
      const response = await fetch("/api/asistente", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_ref: sessionRef.current || storedRef(), ...payload }),
      });
      const body: unknown = await response.json().catch(() => null);
      const record = body && typeof body === "object" ? (body as Record<string, unknown>) : {};
      if (!response.ok || !Array.isArray(record.replies)) {
        throw new Error(typeof record.error === "string" ? record.error : "El asistente no respondió.");
      }
      for (const reply of record.replies) if (typeof reply === "string") add("asistente", reply);
    } catch (error) {
      add("error", error instanceof Error ? error.message : "El asistente no respondió.");
    } finally {
      setPending(false);
    }
  }

  async function send(raw: string) {
    const text = raw.trim();
    if (!text || pending) return;
    add("persona", text);
    setInput("");
    await deliver({ kind: "text", message: text });
  }

  async function shareLocation() {
    if (pending) return;
    try {
      const position = await currentPosition();
      add("persona", "📍 Ubicación compartida");
      await deliver({ kind: "location", ...position });
    } catch (error) {
      add("error", error instanceof Error ? error.message : "No se pudo obtener tu ubicación.");
    }
  }

  async function sendPhoto(file: File | undefined) {
    if (!file || pending) return;
    const caption = input.trim();
    try {
      const photo = await encodePhoto(file);
      add("persona", caption || "📷 Foto", URL.createObjectURL(file));
      setInput("");
      await deliver({
        kind: "image",
        media_base64: photo.base64,
        mime_type: photo.mimeType,
        ...(caption ? { message: caption } : {}),
      });
    } catch (error) {
      add("error", error instanceof Error ? error.message : "No se pudo enviar la foto.");
    }
  }

  async function startRecording() {
    if (pending || recording) return;
    if (!VoiceRecorder.supported()) {
      add("error", "Este navegador no permite grabar notas de voz. Escribe tu pregunta.");
      return;
    }
    const recorder = new VoiceRecorder();
    try {
      await recorder.start();
      recorderRef.current = recorder;
      setElapsed(0);
      setRecording(true);
      autoStopRef.current = window.setTimeout(() => void finishRecording(), MAX_RECORDING_SECONDS * 1000);
    } catch {
      add("error", "No se pudo usar el micrófono. Revisa el permiso del navegador.");
    }
  }

  async function finishRecording() {
    window.clearTimeout(autoStopRef.current);
    const recorder = recorderRef.current;
    recorderRef.current = null;
    setRecording(false);
    if (!recorder) return;
    try {
      const audio = await recorder.stop();
      if (audio.seconds < 1) {
        add("error", "La nota de voz quedó muy corta. Mantén la grabación al menos un segundo.");
        return;
      }
      add("persona", `🎤 Nota de voz · ${formatSeconds(audio.seconds)}`);
      await deliver({ kind: "audio", media_base64: audio.base64, mime_type: audio.mimeType });
    } catch {
      add("error", "No se pudo procesar la nota de voz. Intenta de nuevo o escribe tu pregunta.");
    }
  }

  function cancelRecording() {
    window.clearTimeout(autoStopRef.current);
    recorderRef.current?.cancel();
    recorderRef.current = null;
    setRecording(false);
  }

  const busy = pending || recording;

  return (
    <div className="card-soft flex min-h-[28rem] flex-col p-4 md:p-6">
      <div className="flex-1 space-y-3" role="log" aria-live="polite" aria-label="Conversación con el asistente">
        {bubbles.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Escribe <strong>Hola</strong> para empezar. También puedes compartir tu ubicación, enviar una foto o una
            nota de voz.
          </p>
        )}
        {bubbles.map((bubble) => (
          <div
            key={bubble.id}
            data-from={bubble.from}
            className={cn(
              "w-fit max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2 text-sm",
              bubble.from === "persona" && "ml-auto bg-forest text-forest-foreground",
              bubble.from === "asistente" && "bg-secondary text-secondary-foreground",
              bubble.from === "error" && "bg-destructive/10 text-destructive",
            )}
          >
            {bubble.imageUrl && (
              // eslint-disable-next-line @next/next/no-img-element -- vista previa local de la foto elegida
              <img src={bubble.imageUrl} alt="Foto enviada" className="mb-2 max-h-48 rounded-xl object-cover" />
            )}
            {bubble.text}
          </div>
        ))}
        {pending && (
          <p role="status" className="text-sm text-muted-foreground">
            El asistente está escribiendo…
          </p>
        )}
        <div ref={endRef} />
      </div>
      <ul className="mt-4 flex flex-wrap gap-2" aria-label="Respuestas rápidas">
        {QUICK.map((quick) => (
          <li key={quick}>
            <button
              type="button"
              onClick={() => send(quick)}
              disabled={busy}
              className="rounded-full border border-border bg-background px-3 py-1 text-xs hover:bg-muted"
            >
              {quick}
            </button>
          </li>
        ))}
      </ul>
      {recording ? (
        <div className="mt-3 flex items-center gap-2" role="status" aria-live="polite">
          <span className="flex h-11 min-w-0 flex-1 items-center gap-2 rounded-full border border-destructive/40 bg-destructive/5 px-4 text-sm">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-destructive" aria-hidden />
            Grabando · {formatSeconds(elapsed)} de {formatSeconds(MAX_RECORDING_SECONDS)}
          </span>
          <button type="button" className="btn-cream" onClick={cancelRecording} aria-label="Cancelar la nota de voz">
            <X className="h-4 w-4" aria-hidden />
          </button>
          <button
            type="button"
            className="btn-dark"
            onClick={() => void finishRecording()}
            aria-label="Enviar la nota de voz"
          >
            <Square className="h-4 w-4" aria-hidden />
          </button>
        </div>
      ) : (
        <>
          <div className="mt-3 flex flex-wrap gap-2" aria-label="Adjuntar">
            <button
              type="button"
              className="flex h-9 items-center gap-1.5 rounded-full border border-border bg-background px-3 text-xs font-semibold hover:bg-muted disabled:opacity-50"
              onClick={() => void shareLocation()}
              disabled={busy}
              aria-label="Compartir mi ubicación"
            >
              <MapPin className="h-4 w-4" aria-hidden /> Ubicación
            </button>
            <button
              type="button"
              className="flex h-9 items-center gap-1.5 rounded-full border border-border bg-background px-3 text-xs font-semibold hover:bg-muted disabled:opacity-50"
              onClick={() => photoRef.current?.click()}
              disabled={busy}
              aria-label="Enviar una foto"
            >
              <Camera className="h-4 w-4" aria-hidden /> Foto
            </button>
            <button
              type="button"
              className="flex h-9 items-center gap-1.5 rounded-full border border-border bg-background px-3 text-xs font-semibold hover:bg-muted disabled:opacity-50"
              onClick={() => void startRecording()}
              disabled={busy}
              aria-label="Grabar una nota de voz"
            >
              <Mic className="h-4 w-4" aria-hidden /> Nota de voz
            </button>
            <input
              ref={photoRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              aria-hidden
              tabIndex={-1}
              data-testid="foto"
              onChange={(event) => {
                void sendPhoto(event.target.files?.[0]);
                event.target.value = "";
              }}
            />
          </div>
          <form
            className="mt-3 flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void send(input);
            }}
          >
            <label htmlFor={inputId} className="sr-only">
              Mensaje
            </label>
            <input
              id={inputId}
              value={input}
              maxLength={1000}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Escribe tu mensaje"
              className="h-11 min-w-0 flex-1 rounded-full border border-input bg-background px-4 text-sm"
            />
            <button type="submit" className="btn-dark shrink-0" disabled={busy || !input.trim()} aria-label="Enviar">
              <SendHorizontal className="h-4 w-4" aria-hidden />
            </button>
          </form>
        </>
      )}
    </div>
  );
}
