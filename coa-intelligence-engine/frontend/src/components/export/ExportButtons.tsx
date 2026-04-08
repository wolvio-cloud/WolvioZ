"use client";

import { Download, FileText, Braces } from "lucide-react";
import { getExportUrl } from "@/lib/api";

interface ExportButtonsProps {
  submissionId: string;
}

export function ExportButtons({ submissionId }: ExportButtonsProps) {
  const handleExport = (format: "csv" | "json") => {
    const url = getExportUrl(submissionId, format);
    const a = document.createElement("a");
    a.href = url;
    a.download = "";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-400 mr-1">Export:</span>
      <button
        onClick={() => handleExport("csv")}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                   bg-slate-100 text-slate-700 border border-slate-200
                   hover:bg-slate-200 transition-colors"
        aria-label="Download CSV export"
      >
        <FileText className="w-3.5 h-3.5" aria-hidden />
        CSV
      </button>
      <button
        onClick={() => handleExport("json")}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                   bg-slate-100 text-slate-700 border border-slate-200
                   hover:bg-slate-200 transition-colors"
        aria-label="Download JSON export"
      >
        <Braces className="w-3.5 h-3.5" aria-hidden />
        JSON
      </button>
    </div>
  );
}
