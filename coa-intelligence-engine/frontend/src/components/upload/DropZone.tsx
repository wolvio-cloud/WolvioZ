"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, AlertCircle } from "lucide-react";
import { clsx } from "clsx";

interface DropZoneProps {
  onFile: (file: File) => void;
  isUploading: boolean;
  error: string | null;
}

const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/tiff"];
const MAX_MB = 50;

export function DropZone({ onFile, isUploading, error }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(pdf|jpg|jpeg|png|tif|tiff)$/i)) {
      return "Unsupported file type. Please upload a PDF, JPG, PNG, or TIFF.";
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      return `File exceeds ${MAX_MB} MB limit.`;
    }
    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      const err = validate(file);
      if (err) {
        setLocalError(err);
        return;
      }
      setLocalError(null);
      onFile(file);
    },
    [onFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const displayError = localError ?? error;

  return (
    <div className="flex flex-col items-center gap-4">
      <label
        className={clsx(
          "flex flex-col items-center justify-center w-full min-h-64 rounded-xl border-2 border-dashed",
          "cursor-pointer transition-all duration-200",
          isDragging
            ? "border-brand-blue bg-blue-50 scale-[1.01]"
            : "border-slate-300 bg-brand-light hover:border-brand-blue hover:bg-blue-50/40",
          isUploading && "pointer-events-none opacity-60"
        )}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        aria-label="Upload Certificate of Analysis"
      >
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff"
          className="sr-only"
          onChange={handleChange}
          disabled={isUploading}
          aria-hidden="true"
        />

        <div className="flex flex-col items-center gap-3 px-8 text-center">
          <div
            className={clsx(
              "flex items-center justify-center w-16 h-16 rounded-full transition-colors",
              isDragging ? "bg-blue-100" : "bg-slate-100"
            )}
          >
            {isUploading ? (
              <div className="w-8 h-8 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
            ) : (
              <Upload
                className={clsx(
                  "w-8 h-8 transition-colors",
                  isDragging ? "text-brand-blue" : "text-slate-400"
                )}
              />
            )}
          </div>

          {isUploading ? (
            <p className="text-sm text-brand-slate font-medium">Uploading…</p>
          ) : (
            <>
              <p className="text-base font-semibold text-navy">
                {isDragging ? "Drop to upload" : "Drop your CoA here"}
              </p>
              <p className="text-sm text-brand-slate">
                or click to browse — PDF, JPG, PNG, TIFF up to {MAX_MB} MB
              </p>
            </>
          )}
        </div>
      </label>

      {displayError && (
        <div
          className="flex items-start gap-2 w-full px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
          role="alert"
        >
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}

      <div className="flex items-center gap-2 text-xs text-slate-400">
        <FileText className="w-3.5 h-3.5" />
        <span>Supports multi-page PDFs — all pages will be extracted</span>
      </div>
    </div>
  );
}
