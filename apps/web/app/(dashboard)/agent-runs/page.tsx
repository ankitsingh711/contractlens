"use client";

import { Bot } from "lucide-react";
import Link from "next/link";

import { RunStatusBadge } from "@/components/agent-runs/run-status-badge";
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
import { useAgentRuns } from "@/hooks/use-agent-runs";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AgentRunsPage() {
  const { data: agentRuns, isLoading } = useAgentRuns();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Agent Runs</h2>
        <p className="text-sm text-muted-foreground">
          Inspect every step of the LangGraph agent: retrieval, evidence evaluation, reasoning,
          and citation validation.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : agentRuns && agentRuns.length > 0 ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Query</TableHead>
                <TableHead>Intent</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Evidence</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agentRuns.map((run) => (
                <TableRow key={run.id} className="cursor-pointer">
                  <TableCell className="max-w-xs">
                    <Link href={`/agent-runs/${run.id}`} className="block truncate hover:underline">
                      {run.query}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{run.intent ?? "—"}</TableCell>
                  <TableCell>
                    <RunStatusBadge status={run.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {run.evidence_score !== null ? run.evidence_score.toFixed(2) : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {run.confidence !== null ? run.confidence.toFixed(2) : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {run.latency_ms !== null ? `${(run.latency_ms / 1000).toFixed(1)}s` : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(run.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <EmptyState
          icon={Bot}
          title="No agent runs yet"
          description="Ask a question in the AI Assistant to see agent execution traces here."
        />
      )}
    </div>
  );
}
