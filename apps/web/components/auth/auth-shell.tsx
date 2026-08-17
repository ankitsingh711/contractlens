"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Scale, type LucideIcon } from "lucide-react";
import { useEffect } from "react";

export interface AuthHighlight {
  icon: LucideIcon;
  label: string;
}

export function AuthShell({
  title,
  description,
  imageSrc,
  imageAlt,
  panelHeading,
  panelSubheading,
  highlights,
  children,
}: {
  title: string;
  description: string;
  imageSrc: string;
  imageAlt: string;
  panelHeading: string;
  panelSubheading: string;
  highlights: AuthHighlight[];
  children: React.ReactNode;
}) {
  useEffect(() => {
    document.title = `${title} · ContractLens AI`;
  }, [title]);

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      {/* Image panel — hidden below lg, real photography with a brand-gradient scrim */}
      <div className="relative hidden overflow-hidden lg:block">
        <Image
          src={imageSrc}
          alt={imageAlt}
          fill
          priority
          sizes="50vw"
          className="object-cover"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-t from-[#06253d]/95 via-[#0b3a5c]/70 to-[#106ebe]/30"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,color-mix(in_oklch,var(--mint),transparent_70%),transparent_55%)]"
        />

        <div className="relative flex h-full flex-col justify-between p-10 text-white">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15 backdrop-blur-sm">
              <Scale className="h-4 w-4" />
            </span>
            ContractLens AI
          </Link>

          <div className="max-w-md">
            <h2 className="text-3xl leading-tight font-semibold tracking-tight">{panelHeading}</h2>
            <p className="mt-3 text-sm leading-relaxed text-white/75">{panelSubheading}</p>

            <ul className="mt-8 space-y-4">
              {highlights.map((item) => (
                <li key={item.label} className="flex items-center gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-mint backdrop-blur-sm">
                    <item.icon className="h-4 w-4" />
                  </span>
                  <span className="text-sm text-white/90">{item.label}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-white/50">Demo/portfolio project — not legal advice.</p>
        </div>
      </div>

      {/* Form panel */}
      <div className="relative flex items-center justify-center px-4 py-16">
        <Link
          href="/"
          className="absolute top-6 left-6 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        <div className="w-full max-w-sm space-y-6">
          <div className="flex flex-col items-center gap-2 text-center lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-mint text-white shadow-sm">
              <Scale className="h-5 w-5" />
            </div>
            <span className="text-lg font-semibold tracking-tight">ContractLens AI</span>
          </div>

          <div className="space-y-1 text-center lg:text-left">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>

          <div className="rounded-2xl border bg-card/60 p-6 shadow-sm backdrop-blur-sm">{children}</div>
        </div>
      </div>
    </div>
  );
}
