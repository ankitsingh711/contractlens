"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { RiskAnalysis } from "@/types/risk-analysis";

export function useDocumentAnalysis(documentId: string | null) {
  return useQuery({
    queryKey: ["analysis", documentId],
    queryFn: () => apiFetch<RiskAnalysis>(`/documents/${documentId}/analysis`),
    enabled: !!documentId,
    retry: false,
    refetchInterval: (query) => (query.state.data?.status === "running" ? 1000 : false),
  });
}

export function useAnalyzeDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      apiFetch<RiskAnalysis>(`/documents/${documentId}/analyze`, { method: "POST" }),
    onSuccess: (data, documentId) => {
      queryClient.setQueryData(["analysis", documentId], data);
      queryClient.invalidateQueries({ queryKey: ["analysis", documentId] });
    },
  });
}
