"use client";

import { Bot, Check, Copy, User } from "lucide-react";
import { useState } from "react";

import { CitationList } from "@/components/assistant/citation-list";
import { FormattedAnswer } from "@/components/assistant/formatted-answer";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/hooks/use-chat";

export function ChatMessage({
  message,
  stepLabel,
}: {
  message: ChatMessageType;
  stepLabel?: string | null;
}) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const copy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        )}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>
      <div
        className={cn(
          "group max-w-[75%] rounded-lg border px-3 py-2",
          isUser ? "bg-primary text-primary-foreground" : "bg-card",
          message.isError && "border-destructive/50 bg-destructive/5"
        )}
      >
        {message.isStreaming && !message.content ? (
          <div className="space-y-2 py-1">
            <Skeleton className="h-3 w-40" />
            {stepLabel && <p className="text-xs text-muted-foreground">{stepLabel}...</p>}
          </div>
        ) : (
          <>
            <FormattedAnswer text={message.content} />
            {!isUser && !message.isError && <CitationList citations={message.citations} />}
            {!isUser && !message.isStreaming && (
              <Button
                variant="ghost"
                size="icon-sm"
                className="mt-1 opacity-0 transition-opacity group-hover:opacity-100"
                onClick={copy}
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
