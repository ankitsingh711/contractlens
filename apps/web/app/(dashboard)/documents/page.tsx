"use client";

import { FileText } from "lucide-react";

import { DocumentTable } from "@/components/documents/document-table";
import { UploadDropzone } from "@/components/documents/upload-dropzone";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useDocuments } from "@/hooks/use-documents";

export default function DocumentsPage() {
  const { data: documents, isLoading } = useDocuments();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Documents</h2>
        <p className="text-sm text-muted-foreground">
          Upload contracts to extract clauses, run risk analysis, and enable Q&amp;A.
        </p>
      </div>

      <UploadDropzone />

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : documents && documents.length > 0 ? (
        <DocumentTable documents={documents} />
      ) : (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload a contract above to see processing status here — parsing, chunking, embedding, and indexing happen automatically."
        />
      )}
    </div>
  );
}
