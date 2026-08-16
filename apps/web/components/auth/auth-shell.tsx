"use client";

import Link from "next/link";
import { ArrowLeft, Scale } from "lucide-react";
import { useEffect } from "react";

export function AuthShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  useEffect(() => {
    document.title = `${title} · ContractLens AI`;
  }, [title]);

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_-10%,color-mix(in_oklch,var(--primary),transparent_88%),transparent_60%)]"
      />
      <Link
        href="/"
        className="absolute top-6 left-6 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to home
      </Link>
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-mint text-white shadow-sm">
            <Scale className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">ContractLens AI</h1>
          <div className="space-y-1">
            <p className="text-sm font-medium">{title}</p>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        <div className="rounded-2xl border bg-card/60 p-6 shadow-sm backdrop-blur-sm">{children}</div>
      </div>
    </div>
  );
}
