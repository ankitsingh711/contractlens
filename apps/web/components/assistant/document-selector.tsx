"use client";

import { FileText, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useDocuments } from "@/hooks/use-documents";

export function DocumentSelector({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const { data: documents } = useDocuments();
  const completed = documents?.filter((d) => d.status === "completed") ?? [];

  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="outline" size="sm" />}>
          <FileText className="mr-1.5 h-3.5 w-3.5" />
          {selected.length > 0 ? `${selected.length} document(s)` : "All documents"}
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          {completed.length === 0 && (
            <p className="px-2 py-1.5 text-xs text-muted-foreground">
              No processed documents yet.
            </p>
          )}
          {completed.map((doc) => (
            <DropdownMenuCheckboxItem
              key={doc.id}
              checked={selected.includes(doc.id)}
              onCheckedChange={() => toggle(doc.id)}
              onSelect={(e) => e.preventDefault()}
            >
              <span className="truncate">{doc.filename}</span>
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      {selected.map((id) => {
        const doc = completed.find((d) => d.id === id);
        if (!doc) return null;
        return (
          <Badge key={id} variant="secondary" className="gap-1">
            <span className="max-w-32 truncate">{doc.filename}</span>
            <button onClick={() => toggle(id)} aria-label={`Remove ${doc.filename}`}>
              <X className="h-3 w-3" />
            </button>
          </Badge>
        );
      })}
    </div>
  );
}
