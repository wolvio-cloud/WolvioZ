"use client";

import { X, Info, CheckCircle, AlertTriangle, XCircle, HelpCircle, AlertOctagon } from "lucide-react";
import { clsx } from "clsx";
import { StatusBadge } from "./StatusBadge";
import { statusClasses } from "@/config/brand";
import type { ParameterResult } from "@/lib/types";

const icons = {
  PASS: CheckCircle,
  WARNING: AlertTriangle,
  FAIL: XCircle,
  REVIEW: HelpCircle,
  ERROR: AlertOctagon,
};

interface ParameterDetailProps {
  parameter: ParameterResult;
  onClose: () => void;
}

function DetailRow({ label, value }: { label: string; value: string | number | null }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="py-2.5 border-b border-slate-100 last:border-0">
      <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm text-navy font-mono">{String(value)}</p>
    </div>
  );
}

export function ParameterDetail({ parameter, onClose }: ParameterDetailProps) {
  const classes = statusClasses[parameter.validation_status] ?? statusClasses.REVIEW;
  const Icon = icons[parameter.validation_status] ?? HelpCircle;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className={clsx("p-4 border-b", classes.bg, classes.border)}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2">
            <Icon className={clsx("w-5 h-5 mt-0.5 shrink-0", classes.text)} />
            <div>
              <h3 className="text-sm font-bold text-navy leading-snug">
                {parameter.parameter_name}
              </h3>
              {parameter.method_reference && (
                <p className="text-xs text-slate-500 mt-0.5">{parameter.method_reference}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-black/5 transition-colors"
            aria-label="Close parameter detail"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
        <div className="mt-3">
          <StatusBadge status={parameter.validation_status} />
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-0">
        <DetailRow
          label="Result Value"
          value={
            parameter.result_unit
              ? `${parameter.result_value} ${parameter.result_unit}`
              : parameter.result_value
          }
        />
        <DetailRow label="Specification Limit" value={parameter.specification_limit} />
        <DetailRow label="CoA Pass/Fail (as printed)" value={parameter.coa_pass_fail} />
        {parameter.margin_from_boundary !== null && (
          <DetailRow
            label="Margin from Boundary"
            value={`${parameter.margin_from_boundary.toFixed(2)}%`}
          />
        )}
        <DetailRow
          label="Extraction Confidence"
          value={`${(parameter.extraction_confidence * 100).toFixed(1)}%`}
        />
        <DetailRow
          label="Parameter Type"
          value={parameter.is_quantitative ? "Quantitative" : "Qualitative"}
        />
      </div>

      {/* Validation notes */}
      {parameter.validation_notes && (
        <div className="p-4 border-t border-slate-100">
          <div className="flex items-start gap-2 p-3 rounded-lg bg-slate-50 border border-slate-200">
            <Info className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
            <p className="text-xs text-brand-slate leading-relaxed">{parameter.validation_notes}</p>
          </div>
        </div>
      )}
    </div>
  );
}
