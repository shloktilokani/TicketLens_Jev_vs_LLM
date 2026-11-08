import { useQuery } from "@tanstack/react-query"

import { api } from "@/services/api"
import type { ComparisonList } from "@/types/api"

export const useComparisons = (limit: number, ticketId?: string) =>
  useQuery({
    queryKey: ["comparisons", limit, ticketId],
    queryFn: () =>
      api<ComparisonList>(
        `/api/comparisons?limit=${limit}${ticketId ? `&ticket_id=${encodeURIComponent(ticketId)}` : ""}`,
      ),
    refetchInterval: 5000, // new runs appear while a test is in progress
  })
