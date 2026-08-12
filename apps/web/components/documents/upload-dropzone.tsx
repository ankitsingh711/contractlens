"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api-client";
import { useUploadDocument } from "@/hooks/use-documents";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

export function UploadDropzone() {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadDocument();

  const uploadFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      for (const file of Array.from(files)) {
        if (!ACCEPTED_TYPES.includes(file.type)) {
          toast.error(`${file.name} isn't a supported file type.`, {
            description: "Upload PDF, DOCX, or TXT files.",
          });
          continue;
        }
        upload.mutate(file, {
          onError: (err) => {
            toast.error(`Failed to upload ${file.name}`, {
              description: err instanceof ApiError ? err.message : "Please try again.",
            });
          },
        });
      }
    },
    [upload]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        uploadFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed py-12 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:bg-muted/40"
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <UploadCloud className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="text-sm font-medium">
        {upload.isPending ? "Uploading..." : "Drag and drop a contract, or click to browse"}
      </p>
      <p className="text-xs text-muted-foreground">PDF, DOCX, or TXT — up to 25MB</p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_TYPES.join(",")}
        className="hidden"
        onChange={(e) => {
          uploadFiles(e.target.files);
          e.target.value = "";
        }}
      />
    </div>
  );
}
