"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import { TERMINAL_STATUSES, type Document, type DocumentListResponse } from "@/types/document";

const DOCUMENTS_KEY = ["documents"];

export function useDocuments() {
  return useQuery({
    queryKey: DOCUMENTS_KEY,
    queryFn: () => apiFetch<DocumentListResponse>("/documents"),
    select: (data) => data.documents,
    refetchInterval: (query) => {
      const documents = query.state.data?.documents ?? [];
      const hasInFlight = documents.some((doc) => !TERMINAL_STATUSES.includes(doc.status));
      return hasInFlight ? 1500 : false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiFetch<Document>("/documents", { method: "POST", body: formData });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      apiFetch<void>(`/documents/${documentId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}
