import type { Citation } from "@/types/chat";

export type RiskSeverity = "high" | "medium" | "low";

export interface RiskFinding {
  id: string;
  category: string;
  severity: RiskSeverity;
  title: string;
  reason: string;
  confidence: number;
  citations: Citation[];
}

export interface RiskAnalysis {
  id: string;
  document_id: string;
  status: "running" | "completed" | "failed";
  risk_score: number | null;
  error_message: string | null;
  created_at: string;
  findings: RiskFinding[];
}
