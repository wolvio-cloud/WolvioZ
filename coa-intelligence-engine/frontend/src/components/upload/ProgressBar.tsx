"use client";

import { clsx } from "clsx";
import type { StatusResponse } from "@/lib/types";

interface ProgressBarProps {
  status: StatusResponse;
}

const statusMessages: Record<string, string> = {
  pending: "Queued for processing…",
  processing: "Extracting data with AI…",
  completed: "Extraction complete",
  failed: "Extraction failed",
};

export function ProgressBar({ status }: ProgressBarProps) {
  const { status: state, page_count, pages_processed } = status;
  const total = page_count ?? 1;
  const processed = pages_processed ?? 0;
  const pct = total > 0 ? Math.round((processed / total) * 100) : 0;

  const isFailed = state === "failed";
  const isComplete = state === "completed";

  return (
    <div className="w-full space-y-3">
      <div className="flex items-center justify-between">
        <p
          className={clsx(
            "text-sm font-medium",
            isFailed ? "text-red-600" : "text-brand-slate"
          )}
        >
          {statusMessages[state] ?? "Processing…"}
        </p>
        {page_count && page_count > 1 && (
          <p className="text-xs text-slate-400">
            {processed} / {total} pages
          </p>
        )}
      </div>

      <div
        className="w-full h-2 rounded-full bg-slate-200 overflow-hidden"
        role="progressbar"
        aria-valuenow={isComplete ? 100 : pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Extraction progress"
      >
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-500",
            isFailed
              ? "bg-red-400"
              : isComplete
              ? "bg-green-500"
              : "bg-brand-blue animate-pulse"
          )}
          style={{ width: isComplete ? "100%" : `${Math.max(pct, state === "pending" ? 5 : 15)}%` }}
        />
      </div>

      {!isFailed && !isComplete && (
        <p className="text-xs text-slate-400">
          {state === "pending"
            ? "Your file is queued — extraction will begin shortly"
            : "Claude Vision is reading every test parameter…"}
        </p>
      )}

      {isFailed && status.error_message && (
        <p className="text-xs text-red-500">{status.error_message}</p>
      )}
    </div>
  );
}
