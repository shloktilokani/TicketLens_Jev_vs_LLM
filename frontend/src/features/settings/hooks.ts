import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { api, send } from "@/services/api"
import type { AppSettings } from "@/types/api"

export const useSettings = () =>
  useQuery({
    queryKey: ["settings"],
    queryFn: () => api<AppSettings>("/api/settings"),
  })

/** Save one section. The form shows the new values only after the API confirms them. */
export function useSaveSettings(method: "PATCH" | "PUT", path = "") {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) =>
      send<AppSettings>(method, `/api/settings${path}`, body),
    onSuccess: (saved) => {
      queryClient.setQueryData(["settings"], saved)
      queryClient.invalidateQueries({ queryKey: ["providers"] })
      queryClient.invalidateQueries({ queryKey: ["taxonomy"] })
      toast.success("Saved")
    },
    onError: (error) => toast.error(error.message),
  })
}

export const useModelList = (side: "jev" | "llm") =>
  useQuery({
    queryKey: ["settings", "models", side],
    queryFn: () =>
      api<{ models: string[]; error: string | null }>(
        `/api/settings/models/${side}`,
      ),
  })
