import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="mx-auto max-w-7xl px-5 pt-12 pb-8">
      <p className="eyebrow">{eyebrow}</p>
      <h1 className="mt-2 max-w-3xl text-4xl font-extrabold md:text-5xl">{title}</h1>
      {children && <div className="mt-4 max-w-2xl text-lg text-muted-foreground">{children}</div>}
    </div>
  );
}
