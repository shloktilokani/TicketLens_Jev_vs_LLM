import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api, send } from "@/services/api"
import type { BulkJob, BulkJobList, BulkStart } from "@/types/api"

const POLL_MS = 2000

export const isActive = (job: Pick<BulkJob, "status">) =>
  job.status === "Queued" || job.status === "Running"

export const attemptsDone = (job: BulkJob) =>
  job.completed + job.failed + job.skipped

export const useBulkJobs = (limit: number) =>
  useQuery({
    queryKey: ["bulk-jobs", "list", limit],
    queryFn: () => api<BulkJobList>(`/api/bulk-jobs?limit=${limit}`),
    refetchInterval: (query) =>
      query.state.data?.items.some(isActive) ? POLL_MS : false,
  })

export const useBulkJob = (jobId: string) =>
  useQuery({
    queryKey: ["bulk-jobs", "detail", jobId],
    queryFn: () => api<BulkJob>(`/api/bulk-jobs/${encodeURIComponent(jobId)}`),
    retry: false,
    refetchInterval: (query) =>
      query.state.data && isActive(query.state.data) ? POLL_MS : false,
  })

export function useStartBulk() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: BulkStart) =>
      send<BulkJob>("POST", "/api/bulk-jobs", body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bulk-jobs"] }),
  })
}
