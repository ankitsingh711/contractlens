"use client";

import { GitCompare, Loader2, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { ComparisonTable } from "@/components/analysis/comparison-table";
import { DocumentPicker } from "@/components/analysis/document-picker";
import { RiskFindingsList } from "@/components/analysis/risk-findings-list";
import { RiskScoreGauge } from "@/components/analysis/risk-score-gauge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCompareDocuments } from "@/hooks/use-comparison";
import { useDocuments } from "@/hooks/use-documents";
import { useAnalyzeDocument, useDocumentAnalysis } from "@/hooks/use-risk-analysis";
import { ApiError } from "@/lib/api-client";

function RiskAnalysisTab() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const { data: analysis, isError } = useDocumentAnalysis(documentId);
  const analyze = useAnalyzeDocument();

  const isRunning = analysis?.status === "running" || analyze.isPending;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">Document</label>
          <DocumentPicker value={documentId} onChange={setDocumentId} />
        </div>
        <Button
          onClick={() => documentId && analyze.mutate(documentId)}
          disabled={!documentId || isRunning}
        >
          {isRunning && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
          {isRunning ? "Analyzing..." : "Analyze Contract"}
        </Button>
      </div>

      {!documentId ? (
        <EmptyState
          icon={ShieldAlert}
          title="Select a document to analyze"
          description="Risk analysis scans the document for termination, liability, indemnification, renewal, and other key provisions — every finding is backed by a citation."
        />
      ) : isRunning ? (
        <div className="space-y-2">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : isError || !analysis ? (
        <EmptyState
          icon={ShieldAlert}
          title="No analysis yet"
          description="Click Analyze Contract to run risk analysis on this document."
        />
      ) : analysis.status === "failed" ? (
        <p className="text-sm text-destructive">
          {analysis.error_message ?? "Analysis failed. Please try again."}
        </p>
      ) : (
        <div className="space-y-4">
          {analysis.risk_score !== null && <RiskScoreGauge score={analysis.risk_score} />}
          {analysis.findings.length === 0 ? (
            <EmptyState
              icon={ShieldAlert}
              title="No significant findings"
              description="No categories had strong enough evidence to flag — this can mean the contract is straightforward, or that it uses unusual phrasing this heuristic pipeline doesn't recognize."
            />
          ) : (
            <RiskFindingsList findings={analysis.findings} />
          )}
        </div>
      )}
    </div>
  );
}

function ComparisonTab() {
  const { data: documents } = useDocuments();
  const [documentIdA, setDocumentIdA] = useState<string | null>(null);
  const [documentIdB, setDocumentIdB] = useState<string | null>(null);
  const compare = useCompareDocuments();

  const run = () => {
    if (!documentIdA || !documentIdB) return;
    compare.mutate({ documentIdA, documentIdB });
  };

  const filenameFor = (id: string | null) =>
    documents?.find((d) => d.id === id)?.filename ?? "Document";

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">Contract A</label>
          <DocumentPicker value={documentIdA} onChange={setDocumentIdA} exclude={documentIdB} />
        </div>
        <div className="flex-1 space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">Contract B</label>
          <DocumentPicker value={documentIdB} onChange={setDocumentIdB} exclude={documentIdA} />
        </div>
        <Button onClick={run} disabled={!documentIdA || !documentIdB || compare.isPending}>
          {compare.isPending && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
          Compare
        </Button>
      </div>

      {compare.isError && (
        <p className="text-sm text-destructive">
          {compare.error instanceof ApiError ? compare.error.message : "Comparison failed."}
        </p>
      )}

      {!compare.data ? (
        <EmptyState
          icon={GitCompare}
          title="Select two documents to compare"
          description="Comparison shows the retrieved clause for each category side by side, with citations — no summarization, so there's nothing to hallucinate."
        />
      ) : compare.data.rows.length === 0 ? (
        <EmptyState
          icon={GitCompare}
          title="No comparable clauses found"
          description="Neither document had strong evidence for any of the compared categories."
        />
      ) : (
        <ComparisonTable
          rows={compare.data.rows}
          labelA={filenameFor(documentIdA)}
          labelB={filenameFor(documentIdB)}
        />
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Analysis</h2>
        <p className="text-sm text-muted-foreground">
          Risk scores, clause categorization, and document comparison — every claim backed by a
          citation.
        </p>
      </div>

      <Tabs defaultValue="risk">
        <TabsList>
          <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
          <TabsTrigger value="compare">Compare Documents</TabsTrigger>
        </TabsList>
        <TabsContent value="risk" className="pt-4">
          <RiskAnalysisTab />
        </TabsContent>
        <TabsContent value="compare" className="pt-4">
          <ComparisonTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
