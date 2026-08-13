"use client";

import { AlertTriangle, ChevronRight } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";
import type { AgentStep } from "@/types/agent-run";

const STEP_LABELS: Record<string, string> = {
  classify_query: "Query Classification",
  plan: "Planning",
  retrieve: "Retrieval",
  evaluate_evidence: "Evidence Validation",
  reason: "LLM Reasoning",
  abstain: "Abstention",
  validate_claims: "Claim Validation",
  validate_citations: "Citation Validation",
  final_response: "Final Response",
};

export function StepItem({ step }: { step: AgentStep }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-muted/50"
      >
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
          {String(step.step_index + 1).padStart(2, "0")}
        </span>
        <span className="flex-1 text-sm font-medium">
          {STEP_LABELS[step.step_name] ?? step.step_name}
        </span>
        {step.error && <AlertTriangle className="h-4 w-4 text-destructive" />}
        <span className="text-xs text-muted-foreground">{step.latency_ms.toFixed(0)}ms</span>
        <ChevronRight className={cn("h-4 w-4 text-muted-foreground transition-transform", expanded && "rotate-90")} />
      </button>
      {expanded && (
        <div className="space-y-2 border-t p-3 text-xs">
          {step.error && (
            <p className="rounded bg-destructive/10 px-2 py-1 text-destructive">{step.error}</p>
          )}
          <div>
            <p className="mb-1 font-medium text-muted-foreground">Input</p>
            <pre className="overflow-x-auto rounded bg-muted p-2">
              {JSON.stringify(step.input, null, 2)}
            </pre>
          </div>
          <div>
            <p className="mb-1 font-medium text-muted-foreground">Output</p>
            <pre className="overflow-x-auto rounded bg-muted p-2">
              {JSON.stringify(step.output, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
