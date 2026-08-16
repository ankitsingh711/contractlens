import Link from "next/link";
import { ArrowRight, CircleDot } from "lucide-react";

import { Button } from "@/components/ui/button";
import { AgentTracePanel } from "@/components/landing/agent-trace-panel";

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-36 pb-20 sm:pt-44 sm:pb-28">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,color-mix(in_oklch,var(--primary),transparent_88%),transparent_70%)]"
      />
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-16 px-6 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur-sm">
            <CircleDot className="h-3 w-3 text-mint" />
            Every answer traces back to a real clause
          </div>

          <h1 className="mt-6 text-4xl leading-[1.08] font-semibold tracking-tight text-foreground sm:text-5xl lg:text-[3.4rem]">
            Contract intelligence that{" "}
            <span className="relative whitespace-nowrap">
              <span className="relative z-10 bg-gradient-to-r from-primary to-[#0aa88a] bg-clip-text text-transparent">
                shows its work
              </span>
            </span>
            , not just its answer.
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
            ContractLens AI reads your contracts with a hybrid-retrieval, citation-grounded agent that refuses to
            guess. Every claim is traceable to a retrieved clause — and when the evidence isn&apos;t there, it says
            so instead of making something up.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Button
              size="lg"
              className="h-11 rounded-full bg-gradient-to-r from-primary to-[#0a8fbf] px-6 text-base text-white shadow-lg shadow-primary/20 hover:opacity-90"
              render={<Link href="/register" />}
            >
              Get started free
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="h-11 rounded-full px-6 text-base"
              render={<a href="#capabilities" />}
            >
              See how it works
            </Button>
          </div>

          <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
            <span>No credit card required</span>
            <span className="h-1 w-1 rounded-full bg-border" />
            <span>Runs fully self-hosted</span>
            <span className="h-1 w-1 rounded-full bg-border" />
            <span>Abstains instead of hallucinating</span>
          </div>
        </div>

        <div className="flex justify-center lg:justify-end">
          <AgentTracePanel />
        </div>
      </div>
    </section>
  );
}
