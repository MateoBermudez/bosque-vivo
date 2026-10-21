"use client";

import { AlertTriangle, Bot, SendHorizontal, User } from "lucide-react";
import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";

import { chatAnswerSchema, type ChatAnswer } from "@/lib/api/schema";
import { queryClassLabel, toolLabel } from "@/lib/domain";
import { cn } from "@/lib/utils";

import { RichText } from "./rich-text";

type Message =
  | { id: number; role: "user"; text: string }
  | { id: number; role: "assistant"; text: string; meta: ChatAnswer }
  | { id: number; role: "error"; text: string };

const MAX_LENGTH = 2000;

export function ChatPanel({
  suggestions,
  initialPrompt,
}: {
  suggestions: string[];
  initialPrompt?: string;
}) {
  const inputId = useId();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(initialPrompt ?? "");
  const [pending, setPending] = useState(false);
  const sessionRef = useRef<string>("");
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    sessionRef.current = crypto.randomUUID();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, pending]);

  async function send(raw: string) {
    const text = raw.trim();
    if (!text || pending) return;
    setMessages((current) => [...current, { id: nextId.current++, role: "user", text }]);
    setInput("");
    setPending(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_ref: sessionRef.current || "web" }),
      });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const message =
          payload && typeof payload === "object" && "error" in payload && typeof payload.error === "string"
            ? payload.error
            : "El asistente no respondió. Intenta de nuevo.";
        throw new Error(response.status === 401 ? "Tu sesión venció. Vuelve a iniciar sesión." : message);
      }
      const parsed = chatAnswerSchema.safeParse(payload);
      if (!parsed.success) throw new Error("La respuesta del asistente no tiene el formato esperado.");
      setMessages((current) => [
        ...current,
        { id: nextId.current++, role: "assistant", text: parsed.data.answer, meta: parsed.data },
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "El asistente no respondió. Intenta de nuevo.";
      setMessages((current) => [...current, { id: nextId.current++, role: "error", text: message }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-5">
      <p className="rounded-2xl bg-secondary px-4 py-3 text-sm text-secondary-foreground">
        Este asistente usa IA y puede equivocarse. Las cifras provienen del sistema; si una respuesta usó la
        plantilla de respaldo, se indica.
      </p>

      <div className="card-soft mt-4 flex min-h-[26rem] flex-col p-4 md:p-6">
        <div
          className="flex-1 space-y-4"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
          aria-label="Conversación con el asistente"
        >
          {messages.length === 0 && (
            <div>
              <p className="font-semibold">Haz una pregunta sobre un proyecto, el índice o la metodología.</p>
              <ul className="mt-4 flex flex-wrap gap-2">
                {suggestions.map((suggestion) => (
                  <li key={suggestion}>
                    <button
                      type="button"
                      onClick={() => send(suggestion)}
                      className="rounded-full border border-border bg-background px-4 py-2 text-left text-sm hover:bg-muted"
                    >
                      {suggestion}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {pending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
              <Bot className="h-4 w-4 animate-pulse" aria-hidden /> El asistente está revisando los datos…
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form
          className="mt-4 flex items-end gap-2 border-t border-border pt-4"
          onSubmit={(event) => {
            event.preventDefault();
            void send(input);
          }}
        >
          <div className="flex-1">
            <label htmlFor={inputId} className="sr-only">
              Tu pregunta
            </label>
            <textarea
              id={inputId}
              value={input}
              onChange={(event) => setInput(event.target.value.slice(0, MAX_LENGTH))}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send(input);
                }
              }}
              rows={2}
              placeholder="Pregunta por un proyecto, el índice o la metodología"
              className="w-full resize-none rounded-2xl border border-input bg-background px-4 py-3 text-sm"
            />
            {input.length > MAX_LENGTH - 200 && (
              <p className="mt-1 text-xs text-muted-foreground">
                {input.length} / {MAX_LENGTH}
              </p>
            )}
          </div>
          <button type="submit" className="btn-dark h-12" disabled={pending || input.trim() === ""} aria-label="Enviar pregunta">
            <SendHorizontal className="h-4 w-4" aria-hidden />
          </button>
        </form>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex items-start justify-end gap-2">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-lime px-4 py-2.5 text-sm text-lime-foreground">
          {message.text}
        </p>
        <User className="mt-2 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
      </div>
    );
  }
  if (message.role === "error") {
    return (
      <p role="alert" className="flex items-start gap-2 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /> {message.text}
      </p>
    );
  }
  const { meta } = message;
  return (
    <div className="flex items-start gap-2">
      <Bot className="mt-2 h-4 w-4 shrink-0 text-primary" aria-hidden />
      <div className="min-w-0 max-w-[90%] rounded-2xl rounded-bl-sm bg-secondary px-4 py-3 text-sm">
        <RichText text={message.text} />

        {meta.used_fallback && (
          <p className="mt-3 flex items-start gap-2 rounded-xl bg-background px-3 py-2 text-xs text-muted-foreground">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            Esta respuesta salió de la plantilla de respaldo porque el análisis con IA no estuvo disponible o no
            pasó la validación de cifras.
          </p>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className={cn("rounded-full px-2.5 py-1 font-semibold", meta.query_class === "profunda" ? "bg-forest text-forest-foreground" : "bg-background")}>
            Consulta {queryClassLabel(meta.query_class).toLowerCase()}
          </span>
          {meta.evidence_ids.map((id) => (
            <span key={id} className="rounded-full border border-border bg-background px-2.5 py-1 font-mono">
              {id}
            </span>
          ))}
          <Link href={`/trazas#traza-${meta.run_id}`} className="underline underline-offset-4">
            Traza #{meta.run_id}
          </Link>
        </div>

        {meta.tools_called.length > 0 && (
          <details className="mt-2 text-xs text-muted-foreground">
            <summary className="cursor-pointer font-semibold">Cómo llegó a esta respuesta</summary>
            <ol className="mt-2 list-decimal space-y-1 pl-5">
              {meta.tools_called.map((tool, index) => (
                <li key={`${tool}-${index}`}>{toolLabel(tool)}</li>
              ))}
            </ol>
          </details>
        )}
      </div>
    </div>
  );
}
