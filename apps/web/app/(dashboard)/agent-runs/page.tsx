import { Bot } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";

export default function AgentRunsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Agent Runs</h2>
        <p className="text-sm text-muted-foreground">
          Inspect every step of the LangGraph agent: retrieval, evidence evaluation, reasoning,
          and citation validation.
        </p>
      </div>
      <EmptyState
        icon={Bot}
        title="Agent traces appear once the agent is wired up in Phase 4"
        description="Each run will show classification, planning, retrieval, reranking, evidence validation, reasoning, and citation checks with per-step latency, tokens, and cost."
      />
    </div>
  );
}
