import { FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export default function DocumentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Documents</h2>
          <p className="text-sm text-muted-foreground">
            Upload contracts to extract clauses, run risk analysis, and enable Q&amp;A.
          </p>
        </div>
        <Button disabled>Upload document</Button>
      </div>
      <EmptyState
        icon={FileText}
        title="Document upload is coming in the next phase"
        description="Drag-and-drop upload, S3-compatible storage, and the parsing/chunking/embedding pipeline are implemented in Phase 2."
      />
    </div>
  );
}
