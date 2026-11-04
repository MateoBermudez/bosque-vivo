"use client";

import { SendHorizontal } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type Bubble = { id: number; from: "persona" | "asistente" | "error"; text: string };

const STORAGE_KEY = "bv_chat_comunitario";
const QUICK = ["Hola", "ACEPTO", "AYUDA", "ESTADO", "ALERTAS"];

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

export function CommunityChat() {
  const inputId = useId();
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const sessionRef = useRef("");
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    sessionRef.current = storedRef();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [bubbles, pending]);

  function add(from: Bubble["from"], text: string) {
    setBubbles((current) => [...current, { id: nextId.current++, from, text }]);
  }

  async function send(raw: string) {
    const text = raw.trim();
    if (!text || pending) return;
    add("persona", text);
    setInput("");
    setPending(true);
    try {
      const response = await fetch("/api/asistente", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_ref: sessionRef.current || storedRef(), message: text }),
      });
      const payload: unknown = await response.json().catch(() => null);
      const record = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : {};
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

  return (
    <div className="card-soft flex min-h-[28rem] flex-col p-4 md:p-6">
      <div className="flex-1 space-y-3" role="log" aria-live="polite" aria-label="Conversación con el asistente">
        {bubbles.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Escribe <strong>Hola</strong> para empezar. Funciona igual que el asistente de WhatsApp.
          </p>
        )}
        {bubbles.map((bubble) => (
          <p
            key={bubble.id}
            className={cn(
              "max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2 text-sm",
              bubble.from === "persona" && "ml-auto bg-forest text-forest-foreground",
              bubble.from === "asistente" && "bg-secondary text-secondary-foreground",
              bubble.from === "error" && "bg-destructive/10 text-destructive",
            )}
          >
            {bubble.text}
          </p>
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
              disabled={pending}
              className="rounded-full border border-border bg-background px-3 py-1 text-xs hover:bg-muted"
            >
              {quick}
            </button>
          </li>
        ))}
      </ul>
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
          className="h-11 flex-1 rounded-full border border-input bg-background px-4 text-sm"
        />
        <button type="submit" className="btn-dark" disabled={pending || !input.trim()} aria-label="Enviar">
          <SendHorizontal className="h-4 w-4" aria-hidden />
        </button>
      </form>
    </div>
  );
}
