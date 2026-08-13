"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AgentRun, AgentRunDetail } from "@/types/agent-run";

export function useAgentRuns() {
  return useQuery({
    queryKey: ["agent-runs"],
    queryFn: () => apiFetch<{ agent_runs: AgentRun[] }>("/agent-runs"),
    select: (data) => data.agent_runs,
  });
}

export function useAgentRun(agentRunId: string | null) {
  return useQuery({
    queryKey: ["agent-runs", agentRunId],
    queryFn: () => apiFetch<AgentRunDetail>(`/agent-runs/${agentRunId}`),
    enabled: !!agentRunId,
  });
}
