import { clsx } from "clsx";
import { statusClasses } from "@/config/brand";
import type { ValidationStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: ValidationStatus;
  size?: "sm" | "md";
}

const labels: Record<ValidationStatus, string> = {
  PASS: "Pass",
  WARNING: "Warning",
  FAIL: "Fail",
  REVIEW: "Review",
  ERROR: "Error",
};

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const classes = statusClasses[status] ?? statusClasses.REVIEW;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 font-semibold rounded-full border",
        classes.bg,
        classes.text,
        classes.border,
        size === "sm" ? "text-xs px-2 py-0.5" : "text-xs px-2.5 py-1"
      )}
      aria-label={`Status: ${labels[status]}`}
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full shrink-0", classes.dot)} aria-hidden />
      {labels[status]}
    </span>
  );
}
