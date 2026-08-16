"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import { CitationList } from "@/components/assistant/citation-list";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RiskFinding } from "@/types/risk-analysis";

const SEVERITY_STYLES: Record<string, string> = {
  high: "border-l-destructive",
  medium: "border-l-amber-500",
  low: "border-l-emerald-500",
};

export function RiskFindingCard({ finding }: { finding: RiskFinding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={cn("rounded-lg border border-l-4 bg-card", SEVERITY_STYLES[finding.severity])}>
      <button
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        className="flex w-full items-center gap-2 px-3 py-2.5 text-left"
      >
        <span className="flex-1 text-sm font-medium">{finding.title}</span>
        <Badge variant="outline" className="text-[10px]">
          {Math.round(finding.confidence * 100)}% confidence
        </Badge>
        <ChevronRight className={cn("h-4 w-4 text-muted-foreground transition-transform", expanded && "rotate-90")} />
      </button>
      {expanded && (
        <div className="border-t px-3 py-2.5">
          <p className="text-sm leading-relaxed">{finding.reason}</p>
          <CitationList citations={finding.citations} />
        </div>
      )}
    </div>
  );
}
