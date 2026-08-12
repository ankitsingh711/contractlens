export type DocumentStatus =
  | "uploading"
  | "processing"
  | "parsing"
  | "chunking"
  | "embedding"
  | "indexing"
  | "completed"
  | "failed";

export interface Document {
  id: string;
  filename: string;
  document_type: "pdf" | "docx" | "txt";
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  page_count: number | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
}

export const TERMINAL_STATUSES: DocumentStatus[] = ["completed", "failed"];
