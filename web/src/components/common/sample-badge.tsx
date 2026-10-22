import { Info } from "lucide-react";

import { SAMPLE_NOTICE } from "@/lib/domain";
import { cn } from "@/lib/utils";

export function SampleBadge({ dark = false }: { dark?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
        dark ? "glass text-forest-foreground" : "bg-secondary text-secondary-foreground",
      )}
    >
      <Info className="h-3.5 w-3.5" aria-hidden /> {SAMPLE_NOTICE}
    </span>
  );
}
