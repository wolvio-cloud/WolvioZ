import { useQuery } from "@tanstack/react-query";
import { getCoAStatus } from "@/lib/api";
import type { StatusResponse } from "@/lib/types";

export function useCoaStatus(submissionId: string | null) {
  return useQuery<StatusResponse, Error>({
    queryKey: ["coa-status", submissionId],
    queryFn: async () => {
      if (!submissionId) throw new Error("No submission ID");
      const res = await getCoAStatus(submissionId);
      if (res.error) throw new Error(res.error.message);
      if (!res.data) throw new Error("No status data");
      return res.data;
    },
    enabled: !!submissionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 1500;
      if (data.status === "completed" || data.status === "failed") return false;
      return 1500;
    },
    staleTime: 0,
  });
}
