export interface ComparisonSide {
  found: boolean;
  text: string | null;
  page: number | null;
  section: string | null;
  chunk_id: string | null;
}

export interface ComparisonRow {
  category: string;
  label: string;
  document_a: ComparisonSide;
  document_b: ComparisonSide;
}

export interface CompareResponse {
  document_id_a: string;
  document_id_b: string;
  rows: ComparisonRow[];
}
