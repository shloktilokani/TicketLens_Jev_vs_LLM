import { useQuery } from "@tanstack/react-query"

import { api } from "@/services/api"
import type { ProviderStatus, Taxonomy } from "@/types/api"

export const useTaxonomy = () =>
  useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => api<Taxonomy>("/api/taxonomy"),
    staleTime: Infinity, // refreshed when Settings saves a new version
  })

export const useProviderStatus = () =>
  useQuery({
    queryKey: ["providers", "status"],
    queryFn: () => api<ProviderStatus>("/api/providers/status"),
    staleTime: 60_000,
  })
