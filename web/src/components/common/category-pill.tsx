import type { Category } from "@/lib/api/schema";
import { categoryBg } from "@/lib/domain";
import { cn } from "@/lib/utils";

export function CategoryPill({ category, className }: { category: Category; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold",
        className,
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", categoryBg[category])} aria-hidden />
      {category}
    </span>
  );
}
