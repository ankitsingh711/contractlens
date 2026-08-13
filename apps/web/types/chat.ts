export interface Citation {
  document_id: string;
  filename: string;
  page: number | null;
  section: string | null;
  heading: string | null;
  chunk_id: string;
  quote: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export type ChatStreamEvent =
  | { type: "run_started"; agent_run_id: string; conversation_id: string }
  | { type: "step"; step_index: number; step_name: string; output: Record<string, unknown>; latency_ms: number }
  | {
      type: "done";
      agent_run_id: string;
      conversation_id: string;
      answer: string;
      citations: Citation[];
      confidence: number;
      evidence_score: number;
      intent: string;
    }
  | { type: "error"; message: string };
