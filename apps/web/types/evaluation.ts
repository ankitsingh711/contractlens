export interface EvaluationResult {
  id: string;
  agent_run_id: string | null;
  case_id: string;
  category: string;
  question: string;
  expected_answer: string | null;
  answer: string | null;
  passed: boolean;
  abstained: boolean;
  should_abstain: boolean;
  retrieval_recall: number;
  retrieval_precision: number;
  citation_accuracy: number;
  faithfulness: number;
  answer_relevance: number;
  hallucinated: boolean;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface EvaluationRegression {
  metric: string;
  baseline: number;
  current: number;
  delta: number;
}

export interface EvaluationRun {
  id: string;
  dataset_version: string;
  status: "running" | "completed" | "failed";
  error_message: string | null;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  faithfulness: number | null;
  citation_accuracy: number | null;
  retrieval_recall: number | null;
  retrieval_precision: number | null;
  hallucination_rate: number | null;
  answer_relevance: number | null;
  avg_latency_ms: number | null;
  avg_input_tokens: number | null;
  avg_output_tokens: number | null;
  avg_cost_usd: number | null;
  baseline_run_id: string | null;
  regressions: EvaluationRegression[];
  created_at: string;
}

export interface EvaluationRunDetail extends EvaluationRun {
  results: EvaluationResult[];
}
