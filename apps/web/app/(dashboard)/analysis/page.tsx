import { ShieldAlert } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";

export default function AnalysisPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Analysis</h2>
        <p className="text-sm text-muted-foreground">
          Risk scores, clause categorization, and document comparison.
        </p>
      </div>
      <EmptyState
        icon={ShieldAlert}
        title="Risk analysis is implemented in Phase 5"
        description="Once documents can be uploaded and indexed, this page will show risk scores, flagged clauses, and side-by-side contract comparison, each backed by citations."
      />
    </div>
  );
}
