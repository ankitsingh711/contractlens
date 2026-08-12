"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";

interface HealthResponse {
  status: "ok" | "degraded";
  uptime_seconds: number;
  database: "ok" | "unavailable";
  demo_mode: boolean;
}

export function useSystemStatus() {
  return useQuery({
    queryKey: ["system-status"],
    queryFn: () => apiFetch<HealthResponse>("/health", { auth: false }),
    refetchInterval: 60_000,
  });
}
