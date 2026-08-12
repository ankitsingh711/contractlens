import { MessagesSquare } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";

export default function AssistantPage() {
  return (
    <div className="flex h-full flex-col space-y-6">
      <div>
        <h2 className="text-lg font-semibold">AI Assistant</h2>
        <p className="text-sm text-muted-foreground">
          Ask questions about your documents and get citation-grounded answers.
        </p>
      </div>
      <EmptyState
        icon={MessagesSquare}
        title="The LangGraph agent lands in Phase 4"
        description="Retrieval-augmented, citation-grounded chat with streaming responses and abstention when evidence is insufficient will be wired up here."
      />
    </div>
  );
}
