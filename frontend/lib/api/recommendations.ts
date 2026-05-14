import { apiClient } from "./client"

export const recommendationsApi = {
  // Goi y cho user dang nhap, demo user, hoac fallback popular.
  forUser(params: { userId?: string; topK?: number } = {}) {
    const searchParams = new URLSearchParams()
    if (params.userId) searchParams.set("user_id", params.userId)
    if (params.topK) searchParams.set("top_k", String(params.topK))
    const query = searchParams.toString()
    return apiClient.get(`/recommend${query ? `?${query}` : ""}`)
  },
  popular(topK = 12) {
    return apiClient.get(`/recommend/popular?top_k=${topK}`)
  },
  fromSequence(sequence: number[], topK = 12) {
    return apiClient.post("/recommend/sequence", { sequence, top_k: topK })
  },
}

