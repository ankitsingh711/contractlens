"use client";

import { Send } from "lucide-react";
import { useState } from "react";

import { DocumentSelector } from "@/components/assistant/document-selector";
import { Button } from "@/components/ui/button";

export function ChatInput({
  onSend,
  disabled,
  selectedDocumentIds,
  onDocumentIdsChange,
}: {
  onSend: (message: string) => void;
  disabled: boolean;
  selectedDocumentIds: string[];
  onDocumentIdsChange: (ids: string[]) => void;
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="space-y-2 border-t bg-background p-3">
      <DocumentSelector selected={selectedDocumentIds} onChange={onDocumentIdsChange} />
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask about termination, liability, payment terms..."
          rows={2}
          className="flex-1 resize-none rounded-md border bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
        />
        <Button size="icon" onClick={submit} disabled={disabled || !value.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
