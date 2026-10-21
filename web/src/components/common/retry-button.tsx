"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function RetryButton({ label = "Reintentar" }: { label?: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <button
      type="button"
      className="btn-dark"
      disabled={pending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {pending ? "Reintentando…" : label}
    </button>
  );
}
