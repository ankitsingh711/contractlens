"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { EvaluationRun, EvaluationRunDetail } from "@/types/evaluation";

export function useEvaluationRuns() {
  return useQuery({
    queryKey: ["evaluations"],
    queryFn: () => apiFetch<{ evaluation_runs: EvaluationRun[] }>("/evaluations"),
    select: (data) => data.evaluation_runs,
  });
}

export function useEvaluationRun(id: string | null) {
  return useQuery({
    queryKey: ["evaluations", id],
    queryFn: () => apiFetch<EvaluationRunDetail>(`/evaluations/${id}`),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === "running" ? 1500 : false),
  });
}

export function useTriggerEvaluation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiFetch<EvaluationRun>("/evaluations/run", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluations"] });
    },
  });
}
