import { FileText } from "lucide-react";

import type { Citation } from "@/types/chat";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 space-y-1.5 border-t pt-3">
      <p className="text-xs font-medium text-muted-foreground">Sources</p>
      {citations.map((citation, i) => (
        <div key={citation.chunk_id} className="flex items-start gap-2 text-xs">
          <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded bg-muted text-[10px] font-medium">
            {i + 1}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-1 font-medium">
              <FileText className="h-3 w-3 shrink-0 text-muted-foreground" />
              <span className="truncate">{citation.filename}</span>
            </div>
            <p className="text-muted-foreground">
              {[
                citation.section && `Section ${citation.section}`,
                citation.heading,
                citation.page && `Page ${citation.page}`,
              ]
                .filter(Boolean)
                .join(" — ")}
            </p>
            <p className="mt-0.5 truncate text-muted-foreground italic">&ldquo;{citation.quote}&rdquo;</p>
          </div>
        </div>
      ))}
    </div>
  );
}
