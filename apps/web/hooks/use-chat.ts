"use client";

import { useCallback, useState } from "react";

import { streamChat } from "@/lib/chat-stream";
import { useInvalidateConversations } from "@/hooks/use-conversations";
import type { Citation, ConversationDetail } from "@/types/chat";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  isStreaming?: boolean;
  isError?: boolean;
}

const STEP_LABELS: Record<string, string> = {
  classify_query: "Classifying question",
  plan: "Planning retrieval",
  retrieve: "Searching documents",
  evaluate_evidence: "Evaluating evidence",
  reason: "Generating answer",
  abstain: "Insufficient evidence",
  validate_claims: "Checking claims",
  validate_citations: "Validating citations",
  final_response: "Finalizing response",
};

export function useChat() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStepLabel, setCurrentStepLabel] = useState<string | null>(null);
  const invalidateConversations = useInvalidateConversations();

  const send = useCallback(
    async (text: string, documentIds?: string[]) => {
      const userMessage: ChatMessage = {
        id: `local-${crypto.randomUUID()}`,
        role: "user",
        content: text,
        citations: [],
      };
      const assistantId = `local-${crypto.randomUUID()}`;
      const placeholder: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        citations: [],
        isStreaming: true,
      };
      setMessages((prev) => [...prev, userMessage, placeholder]);
      setIsStreaming(true);

      try {
        for await (const event of streamChat({
          message: text,
          conversationId: conversationId ?? undefined,
          documentIds,
        })) {
          if (event.type === "run_started") {
            setConversationId(event.conversation_id);
          } else if (event.type === "step") {
            setCurrentStepLabel(STEP_LABELS[event.step_name] ?? event.step_name);
          } else if (event.type === "done") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: event.answer, citations: event.citations, isStreaming: false }
                  : m
              )
            );
          } else if (event.type === "error") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: event.message, isStreaming: false, isError: true }
                  : m
              )
            );
          }
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: err instanceof Error ? err.message : "Something went wrong.",
                  isStreaming: false,
                  isError: true,
                }
              : m
          )
        );
      } finally {
        setIsStreaming(false);
        setCurrentStepLabel(null);
        invalidateConversations();
      }
    },
    [conversationId, invalidateConversations]
  );

  const clear = useCallback(() => {
    setConversationId(null);
    setMessages([]);
  }, []);

  const loadConversation = useCallback((conversation: ConversationDetail) => {
    setConversationId(conversation.id);
    setMessages(
      conversation.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations as Citation[],
      }))
    );
  }, []);

  const regenerate = useCallback(
    (documentIds?: string[]) => {
      const lastUserIndex = messages.map((m) => m.role).lastIndexOf("user");
      if (lastUserIndex === -1 || isStreaming) return;
      const lastUserContent = messages[lastUserIndex].content;
      // send() appends its own fresh user + assistant bubbles, so drop the
      // old pair (last user message and everything after it) first.
      setMessages((prev) => prev.slice(0, lastUserIndex));
      void send(lastUserContent, documentIds);
    },
    [messages, isStreaming, send]
  );

  return {
    conversationId,
    messages,
    isStreaming,
    currentStepLabel,
    send,
    clear,
    loadConversation,
    regenerate,
  };
}
