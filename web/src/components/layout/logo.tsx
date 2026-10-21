import { Leaf } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <span
      className={cn(
        "flex items-center gap-2 text-lg font-extrabold tracking-tight",
        light ? "text-forest-foreground" : "text-foreground",
      )}
    >
      <span className="grid h-8 w-8 place-items-center rounded-full bg-lime text-lime-foreground">
        <Leaf className="h-4 w-4" aria-hidden />
      </span>
      Bosque Vivo
    </span>
  );
}
