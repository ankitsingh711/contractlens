"use client";

import { FileText, ShieldAlert, MessagesSquare, Gauge } from "lucide-react";
import Link from "next/link";

import { RunStatusBadge } from "@/components/agent-runs/run-status-badge";
import { DocumentStatusBadge } from "@/components/documents/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgentRuns } from "@/hooks/use-agent-runs";
import { useDocuments } from "@/hooks/use-documents";

export default function DashboardPage() {
  const { data: documents, isLoading: documentsLoading } = useDocuments();
  const { data: agentRuns, isLoading: agentRunsLoading } = useAgentRuns();
  const recentDocuments = documents?.slice(0, 5) ?? [];
  const recentRuns = agentRuns?.slice(0, 5) ?? [];

  const avgLatency =
    agentRuns && agentRuns.length > 0
      ? agentRuns.reduce((sum, r) => sum + (r.latency_ms ?? 0), 0) / agentRuns.length / 1000
      : null;

  const statCards = [
    {
      label: "Documents",
      icon: FileText,
      value: documentsLoading ? "—" : String(documents?.length ?? 0),
    },
    { label: "High Risk Contracts", icon: ShieldAlert, value: "0" },
    {
      label: "AI Questions",
      icon: MessagesSquare,
      value: agentRunsLoading ? "—" : String(agentRuns?.length ?? 0),
    },
    {
      label: "Avg Latency",
      icon: Gauge,
      value: avgLatency !== null ? `${avgLatency.toFixed(1)}s` : "—",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Overview</h2>
        <p className="text-sm text-muted-foreground">
          Workspace metrics update once documents are processed and agent runs complete.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Recent Documents</CardTitle>
          </CardHeader>
          <CardContent>
            {documentsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : recentDocuments.length > 0 ? (
              <ul className="space-y-3">
                {recentDocuments.map((doc) => (
                  <li key={doc.id} className="flex items-center justify-between gap-3 text-sm">
                    <span className="flex min-w-0 items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="truncate">{doc.filename}</span>
                    </span>
                    <DocumentStatusBadge status={doc.status} />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                icon={FileText}
                title="No documents yet"
                description="Upload a contract to see processing status and analysis here."
              />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Recent Agent Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {agentRunsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : recentRuns.length > 0 ? (
              <ul className="space-y-3">
                {recentRuns.map((run) => (
                  <li key={run.id} className="flex items-center justify-between gap-3 text-sm">
                    <Link
                      href={`/agent-runs/${run.id}`}
                      className="min-w-0 flex-1 truncate hover:underline"
                    >
                      {run.query}
                    </Link>
                    <RunStatusBadge status={run.status} />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                icon={MessagesSquare}
                title="No agent runs yet"
                description="Ask a question in the AI Assistant to see agent execution traces here."
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
