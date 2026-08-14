"use client";

import { useDocuments } from "@/hooks/use-documents";

export function DocumentPicker({
  value,
  onChange,
  placeholder = "Select a document...",
  exclude,
}: {
  value: string | null;
  onChange: (id: string) => void;
  placeholder?: string;
  exclude?: string | null;
}) {
  const { data: documents, isLoading } = useDocuments();
  const completed = (documents ?? []).filter(
    (d) => d.status === "completed" && d.id !== exclude
  );

  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      disabled={isLoading}
      className="h-9 w-full rounded-md border bg-transparent px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
    >
      <option value="" disabled>
        {isLoading ? "Loading documents..." : placeholder}
      </option>
      {completed.map((doc) => (
        <option key={doc.id} value={doc.id}>
          {doc.filename}
        </option>
      ))}
    </select>
  );
}
