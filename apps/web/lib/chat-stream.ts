import { ApiError, getToken } from "@/lib/api-client";
import type { ChatStreamEvent } from "@/types/chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

interface StreamChatInput {
  message: string;
  conversationId?: string;
  documentIds?: string[];
  signal?: AbortSignal;
}

/**
 * POSTs to /chat and reads the SSE response manually (rather than using
 * the browser's EventSource) because EventSource can't send a custom
 * Authorization header — this app uses bearer tokens, not cookies.
 */
export async function* streamChat(input: StreamChatInput): AsyncGenerator<ChatStreamEvent> {
  const token = getToken();
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      message: input.message,
      conversation_id: input.conversationId,
      document_ids: input.documentIds,
    }),
    signal: input.signal,
  });

  if (!response.ok || !response.body) {
    let message = "Failed to reach the assistant.";
    try {
      const body = await response.json();
      message = body?.error?.message ?? message;
    } catch {
      // no JSON body
    }
    throw new ApiError(response.status, "CHAT_FAILED", message, "unknown");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data: ")) continue;
      yield JSON.parse(line.slice("data: ".length)) as ChatStreamEvent;
    }
  }
}
