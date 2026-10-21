import { AlertCircle, Leaf, Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import { RetryButton } from "./retry-button";

export function Loading({ label = "Cargando…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> {label}
    </div>
  );
}

export function ErrorState({ message, retry = true }: { message: string; retry?: boolean }) {
  return (
    <div role="alert" className="card-soft flex flex-col items-center gap-3 p-10 text-center">
      <AlertCircle className="h-6 w-6 text-destructive" aria-hidden />
      <p className="font-semibold">No pudimos cargar la información</p>
      <p className="max-w-md text-sm text-muted-foreground">{message}</p>
      {retry && <RetryButton />}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="card-soft flex flex-col items-center gap-2 p-10 text-center">
      <Leaf className="h-6 w-6 text-muted-foreground" aria-hidden />
      <p className="font-semibold">{title}</p>
      {children && <div className="max-w-md text-sm text-muted-foreground">{children}</div>}
    </div>
  );
}
