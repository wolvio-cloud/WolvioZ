"use client";

import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { DropZone } from "@/components/upload/DropZone";
import { ProgressBar } from "@/components/upload/ProgressBar";
import { ResultTable } from "@/components/results/ResultTable";
import { RecentSubmissions } from "@/components/sidebar/RecentSubmissions";
import { ExportButtons } from "@/components/export/ExportButtons";
import { useCoaUpload } from "@/hooks/useCoaUpload";
import { useCoaStatus } from "@/hooks/useCoaStatus";
import { useCoaResult } from "@/hooks/useCoaResult";

export default function Home() {
  const [activeSubmissionId, setActiveSubmissionId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useCoaUpload();

  const { data: statusData } = useCoaStatus(activeSubmissionId);

  const isCompleted = statusData?.status === "completed";
  const isFailed = statusData?.status === "failed";
  const isProcessing = statusData?.status === "processing" || statusData?.status === "pending";

  const { data: resultData, isLoading: isResultLoading } = useCoaResult(
    activeSubmissionId,
    isCompleted
  );

  // Refresh sidebar when submission completes
  useEffect(() => {
    if (isCompleted || isFailed) {
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
    }
  }, [isCompleted, isFailed, queryClient]);

  const handleFile = (file: File) => {
    uploadMutation.mutate(file, {
      onSuccess: (data) => {
        setActiveSubmissionId(data.submission_id);
      },
    });
  };

  const handleSidebarSelect = (id: string) => {
    setActiveSubmissionId(id);
    uploadMutation.reset();
  };

  const showUpload = !activeSubmissionId && !uploadMutation.isPending;
  const showProgress =
    activeSubmissionId &&
    (isProcessing || uploadMutation.isPending) &&
    !isCompleted &&
    !isFailed;
  const showResult = activeSubmissionId && isCompleted && resultData;
  const showFailed = activeSubmissionId && isFailed;
  const showSidebarResult =
    activeSubmissionId && statusData && !isProcessing && !uploadMutation.isPending;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Top bar */}
      <header className="bg-navy text-white px-6 py-3 flex items-center justify-between shrink-0 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-brand-blue flex items-center justify-center">
              <span className="text-white text-xs font-bold">W</span>
            </div>
            <div>
              <p className="text-xs text-white/60 leading-none">Wolvio Intelligence</p>
              <p className="text-sm font-semibold leading-none mt-0.5">
                CoA Intelligence Engine
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {showResult && (
            <ExportButtons submissionId={activeSubmissionId} />
          )}
          <button
            onClick={() => {
              setActiveSubmissionId(null);
              uploadMutation.reset();
            }}
            className="text-xs text-white/60 hover:text-white transition-colors"
          >
            New Upload
          </button>
          <div className="text-xs text-white/40 border-l border-white/20 pl-4">
            Pharma QC Platform
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="w-56 bg-white border-r border-slate-200 shrink-0 flex flex-col overflow-hidden">
          <RecentSubmissions
            activeId={activeSubmissionId}
            onSelect={handleSidebarSelect}
          />
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 overflow-y-auto p-6">
          {/* Upload zone */}
          {showUpload && (
            <div className="max-w-2xl mx-auto pt-8">
              <div className="mb-8 text-center">
                <h1 className="text-2xl font-bold text-navy">
                  Upload Certificate of Analysis
                </h1>
                <p className="text-sm text-brand-slate mt-2">
                  Upload a supplier CoA — AI will extract all test parameters,
                  validate against your specifications, and flag deviations in seconds.
                </p>
              </div>
              <DropZone
                onFile={handleFile}
                isUploading={uploadMutation.isPending}
                error={uploadMutation.error?.message ?? null}
              />

              {/* Demo context */}
              <div className="mt-8 rounded-xl border border-slate-200 bg-white p-4">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                  Seeded demo products
                </p>
                <div className="space-y-1">
                  {[
                    "Paracetamol IP",
                    "Microcrystalline Cellulose PH102",
                    "Gelatin Pharma Grade",
                  ].map((name) => (
                    <div key={name} className="flex items-center gap-2 text-sm text-navy">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400" aria-hidden />
                      {name}
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Upload a CoA for any of these products to see automatic spec validation.
                </p>
              </div>
            </div>
          )}

          {/* Upload pending feedback */}
          {uploadMutation.isPending && !activeSubmissionId && (
            <div className="max-w-2xl mx-auto pt-8">
              <div className="rounded-xl border border-slate-200 bg-white p-6">
                <ProgressBar
                  status={{
                    submission_id: "",
                    status: "pending",
                    page_count: null,
                    pages_processed: 0,
                    error_message: null,
                  }}
                />
              </div>
            </div>
          )}

          {/* Processing progress */}
          {showProgress && statusData && (
            <div className="max-w-2xl mx-auto pt-8">
              <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
                <div className="mb-4">
                  <p className="text-xs text-slate-400 mb-0.5">Processing</p>
                  <p className="text-sm font-medium text-navy truncate">
                    {statusData.submission_id}
                  </p>
                </div>
                <ProgressBar status={statusData} />
              </div>
            </div>
          )}

          {/* Failed state */}
          {showFailed && statusData && (
            <div className="max-w-2xl mx-auto pt-8">
              <div className="rounded-xl border border-red-200 bg-red-50 p-6">
                <p className="text-sm font-semibold text-red-700">Extraction Failed</p>
                <p className="text-sm text-red-600 mt-1">
                  {statusData.error_message ?? "An unexpected error occurred. Please try again."}
                </p>
                <button
                  onClick={() => {
                    setActiveSubmissionId(null);
                    uploadMutation.reset();
                  }}
                  className="mt-4 px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}

          {/* Loading result */}
          {activeSubmissionId && isCompleted && isResultLoading && (
            <div className="space-y-3 pt-4">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-12 rounded-lg bg-slate-200 animate-pulse"
                  style={{ opacity: 1 - i * 0.15 }}
                />
              ))}
            </div>
          )}

          {/* Result table */}
          {showResult && (
            <div className="h-full">
              <ResultTable result={resultData} />
            </div>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 px-6 py-2 shrink-0">
        <p className="text-xs text-slate-400 text-center">
          Wolvio Intelligence · CoA Intelligence Engine · All extractions carry audit trail
          · Pharma-grade traceability
        </p>
      </footer>
    </div>
  );
}
