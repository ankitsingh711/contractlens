"use client";

import { ClipboardCheck, Loader2, Play } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { EvalStatusBadge } from "@/components/evaluations/eval-status-badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEvaluationRuns, useTriggerEvaluation } from "@/hooks/use-evaluations";
import { ApiError } from "@/lib/api-client";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function pct(value: number | null) {
  return value !== null ? `${(value * 100).toFixed(1)}%` : "—";
}

export default function EvaluationsPage() {
  const { data: evaluationRuns, isLoading } = useEvaluationRuns();
  const trigger = useTriggerEvaluation();

  const hasRunningRun = evaluationRuns?.some((run) => run.status === "running") ?? false;
  const isTriggering = trigger.isPending || hasRunningRun;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Evaluations</h2>
          <p className="text-sm text-muted-foreground">
            Faithfulness, citation accuracy, retrieval quality, and regression tracking.
          </p>
        </div>
        <Button
          onClick={() =>
            trigger.mutate(undefined, {
              onError: (err) => {
                toast.error("Failed to start evaluation run", {
                  description: err instanceof ApiError ? err.message : "Please try again.",
                });
              },
            })
          }
          disabled={isTriggering}
        >
          {isTriggering ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Play className="mr-1.5 h-3.5 w-3.5" />
          )}
          {isTriggering ? "Running..." : "Run Evaluation"}
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : evaluationRuns && evaluationRuns.length > 0 ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Dataset</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Passed</TableHead>
                <TableHead>Failed</TableHead>
                <TableHead>Faithfulness</TableHead>
                <TableHead>Citation Accuracy</TableHead>
                <TableHead>Avg Latency</TableHead>
                <TableHead>Avg Cost</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {evaluationRuns.map((run) => (
                <TableRow key={run.id} className="cursor-pointer">
                  <TableCell>
                    <Link href={`/evaluations/${run.id}`} className="block hover:underline">
                      {run.dataset_version}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <EvalStatusBadge status={run.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">{run.total_cases}</TableCell>
                  <TableCell className="text-muted-foreground">{run.passed_cases}</TableCell>
                  <TableCell className="text-muted-foreground">{run.failed_cases}</TableCell>
                  <TableCell className="text-muted-foreground">{pct(run.faithfulness)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {pct(run.citation_accuracy)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {run.avg_latency_ms !== null ? `${(run.avg_latency_ms / 1000).toFixed(1)}s` : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {run.avg_cost_usd !== null ? `$${run.avg_cost_usd.toFixed(3)}` : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(run.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <EmptyState
          icon={ClipboardCheck}
          title="No evaluation runs yet"
          description="Run the evaluation suite to score faithfulness, citation accuracy, and retrieval quality against a fixed dataset."
          action={
            <Button
              onClick={() =>
                trigger.mutate(undefined, {
                  onError: (err) => {
                    toast.error("Failed to start evaluation run", {
                      description: err instanceof ApiError ? err.message : "Please try again.",
                    });
                  },
                })
              }
              disabled={isTriggering}
            >
              {isTriggering ? (
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="mr-1.5 h-3.5 w-3.5" />
              )}
              {isTriggering ? "Running..." : "Run Evaluation"}
            </Button>
          }
        />
      )}
    </div>
  );
}
