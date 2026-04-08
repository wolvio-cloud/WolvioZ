import { useQuery } from "@tanstack/react-query";
import { getCoAResult } from "@/lib/api";
import type { CoAResult } from "@/lib/types";

export function useCoaResult(submissionId: string | null, ready: boolean) {
  return useQuery<CoAResult, Error>({
    queryKey: ["coa-result", submissionId],
    queryFn: async () => {
      if (!submissionId) throw new Error("No submission ID");
      const res = await getCoAResult(submissionId);
      if (res.error) throw new Error(res.error.message);
      if (!res.data) throw new Error("No result data");
      return res.data;
    },
    enabled: !!submissionId && ready,
    staleTime: 5 * 60 * 1000, // 5 min — results don't change
  });
}
