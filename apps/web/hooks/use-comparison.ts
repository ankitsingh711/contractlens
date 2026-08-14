"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { CompareResponse } from "@/types/comparison";

export function useCompareDocuments() {
  return useMutation({
    mutationFn: (input: { documentIdA: string; documentIdB: string }) =>
      apiFetch<CompareResponse>("/comparisons", {
        method: "POST",
        body: JSON.stringify({
          document_id_a: input.documentIdA,
          document_id_b: input.documentIdB,
        }),
      }),
  });
}
