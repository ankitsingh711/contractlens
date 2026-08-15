"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AuditLogEntry } from "@/types/audit-log";

export function useAuditLogs(enabled = true) {
  return useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => apiFetch<{ audit_logs: AuditLogEntry[] }>("/audit-logs"),
    select: (data) => data.audit_logs,
    enabled,
    retry: false,
  });
}
