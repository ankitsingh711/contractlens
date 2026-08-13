export interface AgentStep {
  id: string;
  step_index: number;
  step_name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  latency_ms: number;
  error: string | null;
}

export interface AgentRun {
  id: string;
  conversation_id: string | null;
  query: string;
  intent: string | null;
  status: "running" | "completed" | "failed";
  answer: string | null;
  citations: Array<Record<string, unknown>>;
  evidence_score: number | null;
  confidence: number | null;
  model: string | null;
  prompt_version: string | null;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface AgentRunDetail extends AgentRun {
  steps: AgentStep[];
}
