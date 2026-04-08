"use client";

import { useQuery } from "@tanstack/react-query";
import { clsx } from "clsx";
import { FileText, Clock, Loader2 } from "lucide-react";
import { listSubmissions } from "@/lib/api";
import { submissionStatusClasses } from "@/config/brand";
import type { SubmissionSummary } from "@/lib/types";

interface RecentSubmissionsProps {
  activeId: string | null;
  onSelect: (id: string) => void;
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.floor(diffHr / 24)}d ago`;
}

function SubmissionItem({
  submission,
  isActive,
  onClick,
}: {
  submission: SubmissionSummary;
  isActive: boolean;
  onClick: () => void;
}) {
  const statusStyle = submissionStatusClasses[submission.status] ?? submissionStatusClasses.pending;

  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full text-left px-3 py-2.5 rounded-lg transition-colors group",
        isActive
          ? "bg-blue-50 border border-blue-200"
          : "hover:bg-slate-50 border border-transparent"
      )}
      aria-current={isActive ? "true" : undefined}
    >
      <div className="flex items-start gap-2.5">
        <FileText
          className={clsx(
            "w-4 h-4 mt-0.5 shrink-0",
            isActive ? "text-brand-blue" : "text-slate-400"
          )}
        />
        <div className="min-w-0 flex-1">
          <p
            className={clsx(
              "text-sm font-medium truncate",
              isActive ? "text-brand-blue" : "text-navy"
            )}
            title={submission.original_filename}
          >
            {submission.original_filename}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className={clsx(
                "inline-flex items-center gap-1 text-xs font-medium",
                statusStyle.text
              )}
            >
              <span
                className={clsx("w-1.5 h-1.5 rounded-full", statusStyle.dot)}
                aria-hidden
              />
              {submission.status === "processing" ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : null}
              {submission.status.charAt(0).toUpperCase() + submission.status.slice(1)}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3" aria-hidden />
              {formatRelativeTime(submission.created_at)}
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}

export function RecentSubmissions({ activeId, onSelect }: RecentSubmissionsProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["submissions"],
    queryFn: async () => {
      const res = await listSubmissions(20);
      if (res.error) throw new Error(res.error.message);
      return res.data ?? [];
    },
    refetchInterval: 5000,
    staleTime: 2000,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-slate-200">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Recent Submissions
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        )}

        {error && (
          <p className="text-xs text-red-500 px-3 py-2">{error.message}</p>
        )}

        {!isLoading && data?.length === 0 && (
          <p className="text-xs text-slate-400 px-3 py-4 text-center">
            No submissions yet. Upload a CoA to get started.
          </p>
        )}

        {data?.map((submission) => (
          <SubmissionItem
            key={submission.id}
            submission={submission}
            isActive={activeId === submission.id}
            onClick={() => onSelect(submission.id)}
          />
        ))}
      </div>
    </div>
  );
}
