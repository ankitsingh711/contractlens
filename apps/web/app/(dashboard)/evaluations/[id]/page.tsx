"use client";

import { AlertTriangle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { EvalStatusBadge } from "@/components/evaluations/eval-status-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEvaluationRun } from "@/hooks/use-evaluations";

function pct(value: number | null) {
  return value !== null ? `${(value * 100).toFixed(1)}%` : "—";
}

function shortId(id: string) {
  return id.slice(0, 8);
}

export default function EvaluationDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: run, isLoading } = useEvaluationRun(params.id);

  if (isLoading || !run) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-64" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  const stats = [
    { label: "Faithfulness", value: pct(run.faithfulness) },
    { label: "Citation Accuracy", value: pct(run.citation_accuracy) },
    { label: "Retrieval Recall", value: pct(run.retrieval_recall) },
    { label: "Answer Relevance", value: pct(run.answer_relevance) },
    { label: "Hallucination Rate", value: pct(run.hallucination_rate) },
    { label: "Tests", value: String(run.total_cases) },
    { label: "Passed", value: String(run.passed_cases) },
    { label: "Failed", value: String(run.failed_cases) },
    {
      label: "Average Latency",
      value: run.avg_latency_ms !== null ? `${(run.avg_latency_ms / 1000).toFixed(1)}s` : "—",
    },
    {
      label: "Average Tokens",
      value:
        run.avg_input_tokens !== null && run.avg_output_tokens !== null
          ? Math.round(run.avg_input_tokens + run.avg_output_tokens).toLocaleString()
          : "—",
    },
    {
      label: "Average Cost",
      value: run.avg_cost_usd !== null ? `$${run.avg_cost_usd.toFixed(3)}` : "—",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/evaluations"
          className="mb-2 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" />
          All evaluation runs
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Evaluation Results</p>
            <h2 className="text-lg font-semibold">{run.dataset_version}</h2>
          </div>
          <EvalStatusBadge status={run.status} />
        </div>
        {run.baseline_run_id && (
          <p className="mt-1 text-xs text-muted-foreground">
            Compared against run {shortId(run.baseline_run_id)}
          </p>
        )}
      </div>

      {run.error_message && (
        <Card className="border-destructive/50">
          <CardContent className="p-3 text-sm text-destructive">{run.error_message}</CardContent>
        </Card>
      )}

      {run.regressions.length > 0 && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-destructive">
              <AlertTriangle className="h-4 w-4" />
              Regression Detected
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {run.regressions.map((regression) => (
              <p key={regression.metric} className="text-sm text-destructive">
                {regression.metric} dropped from {pct(regression.baseline)} to{" "}
                {pct(regression.current)} — REGRESSION DETECTED
              </p>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-lg font-semibold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Case Results</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Case</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Question</TableHead>
                <TableHead>Result</TableHead>
                <TableHead>Hallucinated</TableHead>
                <TableHead>Trace</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {run.results.map((result) => (
                <TableRow key={result.id}>
                  <TableCell className="text-xs text-muted-foreground">{result.case_id}</TableCell>
                  <TableCell className="text-muted-foreground">{result.category}</TableCell>
                  <TableCell className="max-w-xs truncate" title={result.question}>
                    {result.question}
                  </TableCell>
                  <TableCell>
                    <Badge variant={result.passed ? "default" : "destructive"}>
                      {result.passed ? "passed" : "failed"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {result.hallucinated ? (
                      <Badge variant="destructive">hallucinated</Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {result.agent_run_id ? (
                      <Link
                        href={`/agent-runs/${result.agent_run_id}`}
                        className="text-xs text-primary hover:underline"
                      >
                        View trace
                      </Link>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
