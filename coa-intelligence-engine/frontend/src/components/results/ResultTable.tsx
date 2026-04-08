"use client";

import { useState } from "react";
import { OverallStatus } from "./OverallStatus";
import { ParameterRow } from "./ParameterRow";
import { ParameterDetail } from "./ParameterDetail";
import type { CoAResult, ParameterResult, ValidationStatus } from "@/lib/types";

type FilterStatus = ValidationStatus | "ALL";

const FILTER_OPTIONS: { value: FilterStatus; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "FAIL", label: "Fail" },
  { value: "WARNING", label: "Warning" },
  { value: "PASS", label: "Pass" },
  { value: "REVIEW", label: "Review" },
  { value: "ERROR", label: "Error" },
];

interface ResultTableProps {
  result: CoAResult;
}

export function ResultTable({ result }: ResultTableProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterStatus>("ALL");

  const filtered =
    filter === "ALL"
      ? result.parameters
      : result.parameters.filter((p) => p.validation_status === filter);

  const selected = result.parameters.find((p) => p.id === selectedId) ?? null;

  const counts = result.parameters.reduce(
    (acc, p) => {
      acc[p.validation_status] = (acc[p.validation_status] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="flex gap-4 h-full min-h-0">
      {/* Main table */}
      <div className="flex-1 min-w-0 flex flex-col gap-4">
        {/* Header info */}
        {result.header && (
          <div className="grid grid-cols-2 gap-x-8 gap-y-1 px-1">
            {result.header.product_name && (
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wide">Product</span>
                <p className="text-sm font-semibold text-navy">{result.header.product_name}</p>
              </div>
            )}
            {result.header.supplier_name && (
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wide">Supplier</span>
                <p className="text-sm font-semibold text-navy">{result.header.supplier_name}</p>
              </div>
            )}
            {result.header.batch_number && (
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wide">Batch</span>
                <p className="text-sm font-semibold text-navy font-mono">{result.header.batch_number}</p>
              </div>
            )}
            {result.header.expiry_date && (
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wide">Expiry</span>
                <p className="text-sm font-semibold text-navy">{result.header.expiry_date}</p>
              </div>
            )}
          </div>
        )}

        {/* Overall status */}
        <OverallStatus result={result} />

        {/* Filter tabs */}
        <div className="flex items-center gap-1 flex-wrap">
          {FILTER_OPTIONS.map((opt) => {
            const count = opt.value === "ALL" ? result.parameter_count : counts[opt.value] ?? 0;
            return (
              <button
                key={opt.value}
                onClick={() => setFilter(opt.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  filter === opt.value
                    ? "bg-navy text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {opt.label}
                {count > 0 && (
                  <span className="ml-1.5 opacity-70">{count}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Table */}
        <div className="rounded-xl border border-slate-200 overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Parameter
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Result
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Specification
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Margin
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-400">
                      No parameters match this filter
                    </td>
                  </tr>
                ) : (
                  filtered.map((param) => (
                    <ParameterRow
                      key={param.id}
                      parameter={param}
                      isSelected={selectedId === param.id}
                      onClick={() =>
                        setSelectedId((prev) => (prev === param.id ? null : param.id))
                      }
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-80 shrink-0 rounded-xl border border-slate-200 shadow-card overflow-hidden bg-white">
          <ParameterDetail
            parameter={selected}
            onClose={() => setSelectedId(null)}
          />
        </div>
      )}
    </div>
  );
}
