import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadCoA } from "@/lib/api";
import type { UploadResponse } from "@/lib/types";

export function useCoaUpload() {
  const queryClient = useQueryClient();

  return useMutation<UploadResponse, Error, File>({
    mutationFn: async (file: File) => {
      const res = await uploadCoA(file);
      if (res.error) throw new Error(res.error.message);
      if (!res.data) throw new Error("No response data from upload");
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
    },
  });
}
