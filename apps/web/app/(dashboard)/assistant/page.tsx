"use client";

import { MessagesSquare, RotateCcw, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { ChatInput } from "@/components/assistant/chat-input";
import { ChatMessage } from "@/components/assistant/chat-message";
import { ConversationHistory } from "@/components/assistant/conversation-history";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { useChat } from "@/hooks/use-chat";

const SAMPLE_QUESTIONS = [
  "What are the termination obligations?",
  "What happens if the supplier breaches the agreement?",
  "What are the payment terms?",
  "Is there an automatic renewal clause?",
];

export default function AssistantPage() {
  const { messages, isStreaming, currentStepLabel, send, clear, loadConversation, regenerate } =
    useChat();
  const [documentIds, setDocumentIds] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-[calc(100vh-7.5rem)] flex-col">
      <div className="flex items-center justify-between pb-4">
        <div>
          <h2 className="text-lg font-semibold">AI Assistant</h2>
          <p className="text-sm text-muted-foreground">
            Ask questions about your documents and get citation-grounded answers.
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <ConversationHistory onSelect={loadConversation} onNew={clear} />
          {messages.length > 0 && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => regenerate(documentIds)}
                disabled={isStreaming}
              >
                <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                Regenerate
              </Button>
              <Button variant="outline" size="sm" onClick={clear}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Clear
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-1 flex-col overflow-hidden rounded-lg border bg-muted/10">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-4">
              <EmptyState
                icon={MessagesSquare}
                title="Ask your first question"
                description="Answers are grounded in your uploaded documents and always cite their sources. If there isn't enough evidence, the assistant will say so instead of guessing."
              />
              <div className="grid w-full max-w-md gap-2">
                {SAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => send(q, documentIds)}
                    className="rounded-md border bg-background px-3 py-2 text-left text-sm hover:bg-muted"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((m) => (
                <ChatMessage
                  key={m.id}
                  message={m}
                  stepLabel={m.isStreaming ? currentStepLabel : null}
                />
              ))}
              <div ref={scrollRef} />
            </>
          )}
        </div>

        <ChatInput
          onSend={(text) => send(text, documentIds)}
          disabled={isStreaming}
          selectedDocumentIds={documentIds}
          onDocumentIdsChange={setDocumentIds}
        />
      </div>
    </div>
  );
}
