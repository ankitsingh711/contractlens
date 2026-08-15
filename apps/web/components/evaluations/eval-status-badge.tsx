import { Badge } from "@/components/ui/badge";
import type { EvaluationRun } from "@/types/evaluation";

export function EvalStatusBadge({ status }: { status: EvaluationRun["status"] }) {
  return (
    <Badge variant={status === "completed" ? "default" : status === "failed" ? "destructive" : "secondary"}>
      {status}
    </Badge>
  );
}
