import { Check, FileSearch, GitBranch, ShieldCheck, Sparkles, SplitSquareVertical } from "lucide-react";

const STEPS = [
  { icon: SplitSquareVertical, label: "classify_query", detail: "intent: contract_question", ms: 4 },
  { icon: GitBranch, label: "plan", detail: "tool: search_documents", ms: 1 },
  { icon: FileSearch, label: "retrieve", detail: "hybrid search · RRF fusion", ms: 15 },
  { icon: Sparkles, label: "reason", detail: "grounded on 3 evidence chunks", ms: 210 },
  { icon: ShieldCheck, label: "validate_citations", detail: "0 unsupported markers stripped", ms: 1 },
];

export function AgentTracePanel() {
  return (
    <div className="relative w-full max-w-md">
      <div
        aria-hidden
        className="absolute -inset-6 -z-10 rounded-[2rem] bg-[radial-gradient(circle_at_30%_20%,color-mix(in_oklch,var(--mint),transparent_75%),transparent_65%)] blur-xl"
      />
      <div className="overflow-hidden rounded-2xl border border-border/80 bg-card shadow-xl">
        <div className="flex items-center justify-between border-b bg-muted/40 px-4 py-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-destructive/50" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500/60" />
            <span className="h-2.5 w-2.5 rounded-full bg-mint" />
          </div>
          <span className="text-xs font-medium text-muted-foreground">agent_run · live trace</span>
        </div>

        <div className="space-y-3 p-4">
          {STEPS.map((step, i) => (
            <div key={step.label} className="flex items-start gap-3">
              <div className="flex flex-col items-center">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <step.icon className="h-3.5 w-3.5" />
                </div>
                {i < STEPS.length - 1 && <div className="my-0.5 h-full w-px flex-1 bg-border" />}
              </div>
              <div className="flex-1 pb-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[13px] font-medium text-foreground">{step.label}</span>
                  <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                    <Check className="h-3 w-3 text-mint" />
                    {step.ms}ms
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{step.detail}</p>
              </div>
            </div>
          ))}

          <div className="rounded-xl border-l-2 border-mint bg-accent/60 p-3">
            <p className="text-xs leading-relaxed text-foreground">
              &ldquo;Either party may terminate with{" "}
              <span className="rounded bg-mint/20 px-1 font-medium text-accent-foreground">30 days written
              notice</span>
              .&rdquo;{" "}
              <span className="font-mono text-[11px] text-primary">[1]</span>
            </p>
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              §8.2 Termination · master_services_agreement.pdf, p.4
            </p>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
            <span className="text-xs font-medium text-muted-foreground">Evidence confidence</span>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-20 overflow-hidden rounded-full bg-border">
                <div className="h-full w-[87%] rounded-full bg-gradient-to-r from-primary to-mint" />
              </div>
              <span className="text-xs font-semibold text-foreground">0.87</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
