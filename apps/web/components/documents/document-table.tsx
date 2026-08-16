"use client";

import { FileText, MoreHorizontal, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { DocumentStatusBadge } from "@/components/documents/status-badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDeleteDocument } from "@/hooks/use-documents";
import { ApiError } from "@/lib/api-client";
import type { Document } from "@/types/document";

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function DocumentTable({ documents }: { documents: Document[] }) {
  const deleteDocument = useDeleteDocument();

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Document</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Pages</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Uploaded</TableHead>
            <TableHead className="w-10" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell className="flex items-center gap-2 font-medium">
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{doc.filename}</span>
              </TableCell>
              <TableCell className="uppercase text-muted-foreground">
                {doc.document_type}
              </TableCell>
              <TableCell className="text-muted-foreground">{formatSize(doc.size_bytes)}</TableCell>
              <TableCell className="text-muted-foreground">{doc.page_count ?? "—"}</TableCell>
              <TableCell>
                <DocumentStatusBadge status={doc.status} />
                {doc.status === "failed" && doc.error_message && (
                  <p className="mt-1 max-w-xs text-xs text-destructive">{doc.error_message}</p>
                )}
              </TableCell>
              <TableCell className="text-muted-foreground">{formatDate(doc.created_at)}</TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger
                    render={
                      <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${doc.filename}`} />
                    }
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() =>
                        deleteDocument.mutate(doc.id, {
                          onError: (err) => {
                            toast.error("Failed to delete document", {
                              description:
                                err instanceof ApiError ? err.message : "Please try again.",
                            });
                          },
                        })
                      }
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
