"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { CitationList } from "@/components/assistant/citation-list";
import { FormattedAnswer } from "@/components/assistant/formatted-answer";
import { RunStatusBadge } from "@/components/agent-runs/run-status-badge";
import { StepItem } from "@/components/agent-runs/step-item";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgentRun } from "@/hooks/use-agent-runs";
import type { Citation } from "@/types/chat";

export default function AgentRunDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: run, isLoading } = useAgentRun(params.id);

  if (isLoading || !run) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-64" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/agent-runs"
          className="mb-2 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" />
          All agent runs
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Query</p>
            <h2 className="text-lg font-semibold">&ldquo;{run.query}&rdquo;</h2>
          </div>
          <RunStatusBadge status={run.status} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Intent", value: run.intent ?? "—" },
          { label: "Evidence Score", value: run.evidence_score?.toFixed(2) ?? "—" },
          { label: "Confidence", value: run.confidence?.toFixed(2) ?? "—" },
          {
            label: "Latency",
            value: run.latency_ms !== null ? `${(run.latency_ms / 1000).toFixed(2)}s` : "—",
          },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-sm font-semibold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {run.error_message && (
        <Card className="border-destructive/50">
          <CardContent className="p-3 text-sm text-destructive">{run.error_message}</CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Steps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {run.steps.map((step) => (
            <StepItem key={step.id} step={step} />
          ))}
        </CardContent>
      </Card>

      {run.answer && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Final Response</CardTitle>
          </CardHeader>
          <CardContent>
            <FormattedAnswer text={run.answer} />
            <CitationList citations={run.citations as unknown as Citation[]} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
