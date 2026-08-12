import { Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DocumentStatus } from "@/types/document";

const LABELS: Record<DocumentStatus, string> = {
  uploading: "Uploading",
  processing: "Processing",
  parsing: "Parsing",
  chunking: "Chunking",
  embedding: "Embedding",
  indexing: "Indexing",
  completed: "Completed",
  failed: "Failed",
};

const IN_PROGRESS: DocumentStatus[] = [
  "uploading",
  "processing",
  "parsing",
  "chunking",
  "embedding",
  "indexing",
];

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  const inProgress = IN_PROGRESS.includes(status);
  const failed = status === "failed";

  return (
    <Badge
      variant={failed ? "destructive" : status === "completed" ? "default" : "secondary"}
      className={cn("gap-1", inProgress && "text-muted-foreground")}
    >
      {inProgress && <Loader2 className="h-3 w-3 animate-spin" />}
      {LABELS[status]}
    </Badge>
  );
}
