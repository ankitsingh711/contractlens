import { Badge } from "@/components/ui/badge";
import type { AgentRun } from "@/types/agent-run";

export function RunStatusBadge({ status }: { status: AgentRun["status"] }) {
  return (
    <Badge variant={status === "completed" ? "default" : status === "failed" ? "destructive" : "secondary"}>
      {status}
    </Badge>
  );
}
