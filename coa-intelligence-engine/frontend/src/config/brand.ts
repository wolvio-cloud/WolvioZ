// Wolvio Intelligence brand tokens

export const brand = {
  colors: {
    navy: "#1A2332",
    blue: "#2563EB",
    slate: "#475569",
    lightGray: "#F1F5F9",
  },
} as const;

// Validation status → Tailwind classes
export const statusClasses: Record<
  string,
  { bg: string; text: string; border: string; dot: string }
> = {
  PASS: {
    bg: "bg-green-50",
    text: "text-green-700",
    border: "border-green-200",
    dot: "bg-green-500",
  },
  WARNING: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
    dot: "bg-amber-500",
  },
  FAIL: {
    bg: "bg-red-50",
    text: "text-red-700",
    border: "border-red-200",
    dot: "bg-red-500",
  },
  REVIEW: {
    bg: "bg-cyan-50",
    text: "text-cyan-700",
    border: "border-cyan-200",
    dot: "bg-cyan-500",
  },
  ERROR: {
    bg: "bg-orange-50",
    text: "text-orange-700",
    border: "border-orange-200",
    dot: "bg-orange-500",
  },
};

export const submissionStatusClasses: Record<string, { text: string; dot: string }> = {
  pending: { text: "text-slate-500", dot: "bg-slate-400" },
  processing: { text: "text-blue-600", dot: "bg-blue-500" },
  completed: { text: "text-green-700", dot: "bg-green-500" },
  failed: { text: "text-red-700", dot: "bg-red-500" },
};
