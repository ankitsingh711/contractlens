"use client";

import { History, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useConversation, useConversations } from "@/hooks/use-conversations";
import type { ConversationDetail } from "@/types/chat";

export function ConversationHistory({
  onSelect,
  onNew,
}: {
  onSelect: (conversation: ConversationDetail) => void;
  onNew: () => void;
}) {
  const { data: conversations } = useConversations();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const { data: pendingConversation } = useConversation(pendingId);

  useEffect(() => {
    if (pendingConversation) {
      onSelect(pendingConversation);
      setPendingId(null);
    }
  }, [pendingConversation, onSelect]);

  return (
    <div className="flex items-center gap-1.5">
      <Button variant="outline" size="sm" onClick={onNew}>
        <Plus className="mr-1.5 h-3.5 w-3.5" />
        New
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="outline" size="sm" />}>
          <History className="mr-1.5 h-3.5 w-3.5" />
          History
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          {(!conversations || conversations.length === 0) && (
            <p className="px-2 py-1.5 text-xs text-muted-foreground">No conversations yet.</p>
          )}
          {conversations?.map((c) => (
            <DropdownMenuItem key={c.id} onClick={() => setPendingId(c.id)}>
              <span className="truncate">{c.title || "Untitled conversation"}</span>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
