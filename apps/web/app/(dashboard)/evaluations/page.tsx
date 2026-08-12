import { ClipboardCheck } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";

export default function EvaluationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Evaluations</h2>
        <p className="text-sm text-muted-foreground">
          Faithfulness, citation accuracy, retrieval quality, and regression tracking.
        </p>
      </div>
      <EmptyState
        icon={ClipboardCheck}
        title="The evaluation framework is implemented in Phase 6"
        description="A 50+ case dataset, automated scoring, and regression comparisons against a baseline will appear here."
      />
    </div>
  );
}
