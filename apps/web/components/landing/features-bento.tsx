import {
  GitCompareArrows,
  LineChart,
  Quote,
  ScanSearch,
  SearchCode,
  Workflow,
} from "lucide-react";

import { cn } from "@/lib/utils";

const FEATURES = [
  {
    icon: SearchCode,
    title: "Hybrid retrieval, not vibes",
    description:
      "Vector similarity and PostgreSQL full-text search run in parallel and get fused with Reciprocal Rank Fusion — so exact contract language and semantic meaning both count.",
    span: "lg:col-span-3",
  },
  {
    icon: Workflow,
    title: "An agent with an explicit state machine",
    description:
      "Built on LangGraph: classify → plan → retrieve → reason → validate, with a real conditional branch on evidence sufficiency. Every step is logged and inspectable.",
    span: "lg:col-span-3",
  },
  {
    icon: Quote,
    title: "Citation grounding, enforced in code",
    description: "Any citation marker that doesn't trace back to a retrieved chunk is stripped before you see it.",
    span: "lg:col-span-2",
  },
  {
    icon: ScanSearch,
    title: "Automated risk analysis",
    description: "12 clause categories — termination, liability, indemnification, SLAs — scored with evidence.",
    span: "lg:col-span-2",
  },
  {
    icon: GitCompareArrows,
    title: "Side-by-side comparison",
    description: "Compare two contracts clause-by-clause using retrieved text, never a summarized guess.",
    span: "lg:col-span-2",
  },
  {
    icon: LineChart,
    title: "Evaluation & regression testing",
    description: "Every change runs against a scored eval set with automatic regression detection.",
    span: "lg:col-span-6",
  },
];

export function FeaturesBento() {
  return (
    <section id="capabilities" className="mx-auto max-w-6xl px-6 py-24">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Built for the moment a wrong answer actually matters
        </h2>
        <p className="mt-4 text-muted-foreground">
          Every piece of the pipeline is designed around one constraint: an unsupported claim is worse than no
          answer at all.
        </p>
      </div>

      <div className="mt-14 grid grid-cols-1 gap-4 lg:grid-cols-6">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className={cn(
              "group relative overflow-hidden rounded-2xl border bg-card p-6 transition-colors hover:border-primary/40",
              feature.span
            )}
          >
            <div
              aria-hidden
              className="pointer-events-none absolute -top-10 -right-10 h-32 w-32 rounded-full bg-mint/10 blur-2xl transition-opacity group-hover:opacity-100 opacity-0"
            />
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <feature.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-4 text-base font-semibold text-foreground">{feature.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
