import { clsx } from "clsx";
import { CheckCircle, AlertTriangle, XCircle, HelpCircle, AlertOctagon } from "lucide-react";
import { statusClasses } from "@/config/brand";
import type { CoAResult } from "@/lib/types";

const icons = {
  PASS: CheckCircle,
  WARNING: AlertTriangle,
  FAIL: XCircle,
  REVIEW: HelpCircle,
  ERROR: AlertOctagon,
};

const messages = {
  PASS: "All parameters within specification",
  WARNING: "Parameters within spec — some approaching limits",
  FAIL: "One or more parameters outside specification",
  REVIEW: "Manual review required for some parameters",
  ERROR: "Extraction errors detected — low confidence results",
};

interface OverallStatusProps {
  result: CoAResult;
}

export function OverallStatus({ result }: OverallStatusProps) {
  const { overall_status, parameters, parameter_count } = result;
  const classes = statusClasses[overall_status] ?? statusClasses.REVIEW;
  const Icon = icons[overall_status] ?? HelpCircle;

  const counts = parameters.reduce(
    (acc, p) => {
      acc[p.validation_status] = (acc[p.validation_status] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div
      className={clsx(
        "rounded-xl border p-4 flex items-start gap-4",
        classes.bg,
        classes.border
      )}
    >
      <Icon className={clsx("w-6 h-6 mt-0.5 shrink-0", classes.text)} aria-hidden />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className={clsx("font-bold text-base", classes.text)}>
            {overall_status} — {messages[overall_status]}
          </h2>
        </div>
        <div className="flex flex-wrap gap-3 mt-2">
          {(["PASS", "WARNING", "FAIL", "REVIEW", "ERROR"] as const).map((s) =>
            counts[s] ? (
              <span
                key={s}
                className={clsx(
                  "text-xs font-medium",
                  statusClasses[s].text
                )}
              >
                {counts[s]} {s}
              </span>
            ) : null
          )}
          <span className="text-xs text-slate-500">
            {parameter_count} parameters total
          </span>
        </div>
      </div>
    </div>
  );
}
