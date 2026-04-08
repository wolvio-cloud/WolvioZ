"use client";

import { clsx } from "clsx";
import { StatusBadge } from "./StatusBadge";
import { statusClasses } from "@/config/brand";
import type { ParameterResult } from "@/lib/types";

interface ParameterRowProps {
  parameter: ParameterResult;
  isSelected: boolean;
  onClick: () => void;
}

export function ParameterRow({ parameter, isSelected, onClick }: ParameterRowProps) {
  const classes = statusClasses[parameter.validation_status] ?? statusClasses.REVIEW;

  return (
    <tr
      className={clsx(
        "cursor-pointer transition-colors border-b border-slate-100",
        isSelected
          ? "bg-blue-50 hover:bg-blue-100"
          : "hover:bg-slate-50"
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick();
      }}
      aria-selected={isSelected}
      aria-label={`${parameter.parameter_name}: ${parameter.validation_status}`}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span
            className={clsx("w-2 h-2 rounded-full shrink-0", classes.dot)}
            aria-hidden
          />
          <span className="text-sm font-medium text-navy">
            {parameter.parameter_name}
          </span>
        </div>
        {parameter.method_reference && (
          <p className="text-xs text-slate-400 ml-4">{parameter.method_reference}</p>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-navy">
        {parameter.result_value}
        {parameter.result_unit && (
          <span className="text-slate-400 ml-1">{parameter.result_unit}</span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-slate-500 font-mono">
        {parameter.specification_limit ?? "—"}
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={parameter.validation_status} size="sm" />
      </td>
      <td className="px-4 py-3 text-xs text-slate-400">
        {parameter.margin_from_boundary !== null &&
        parameter.margin_from_boundary !== undefined ? (
          <span>{parameter.margin_from_boundary.toFixed(1)}%</span>
        ) : (
          "—"
        )}
      </td>
      <td className="px-4 py-3">
        <div
          className="flex items-center gap-1.5"
          title={`Confidence: ${(parameter.extraction_confidence * 100).toFixed(0)}%`}
        >
          <div className="w-16 h-1.5 rounded-full bg-slate-200 overflow-hidden">
            <div
              className={clsx(
                "h-full rounded-full",
                parameter.extraction_confidence >= 0.9
                  ? "bg-green-400"
                  : parameter.extraction_confidence >= 0.6
                  ? "bg-amber-400"
                  : "bg-red-400"
              )}
              style={{ width: `${parameter.extraction_confidence * 100}%` }}
            />
          </div>
          <span className="text-xs text-slate-400">
            {(parameter.extraction_confidence * 100).toFixed(0)}%
          </span>
        </div>
      </td>
    </tr>
  );
}
