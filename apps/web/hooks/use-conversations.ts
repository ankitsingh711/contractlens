"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { Conversation, ConversationDetail } from "@/types/chat";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiFetch<{ conversations: Conversation[] }>("/conversations"),
    select: (data) => data.conversations,
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: ["conversations", conversationId],
    queryFn: () => apiFetch<ConversationDetail>(`/conversations/${conversationId}`),
    enabled: !!conversationId,
  });
}

export function useInvalidateConversations() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["conversations"] });
}
