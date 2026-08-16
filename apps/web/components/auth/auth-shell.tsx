"use client";

import { Scale } from "lucide-react";
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
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Scale className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">ContractLens AI</h1>
          <div className="space-y-1">
            <p className="text-sm font-medium">{title}</p>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}
